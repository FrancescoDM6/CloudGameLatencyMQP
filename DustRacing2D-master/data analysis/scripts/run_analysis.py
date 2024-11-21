# run_analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
import time
import sys

class DataAnalyzer:
    def __init__(self, base_dir='DustRacing2D-master'):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / 'logs'
        self.analysis_dir = self.base_dir / 'data analysis'
        self.players = ['F', 'J', 'M']
        self.control_types = ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance', 'Bot']
        
    def _set_plot_style(self):
        """Set consistent plot styling."""
        plt.style.use('default')
        plt.rcParams['axes.grid'] = False  # Remove grid
        plt.rcParams['axes.formatter.use_locale'] = True  # For proper number formatting
        
    def _convert_game_time(self, time_str):
        """Convert game time string to seconds."""
        minutes, seconds = time_str.split(':')
        return float(minutes) * 60 + float(seconds)
    

    def analyze_player_run(self, player, control_type, run_number):
        """Analyze a single player run and its corresponding bot run."""
        print(f"\nAnalyzing {player}'s {control_type} run #{run_number}")
        
        player_log = self.logs_dir / player / f'cardata_{run_number}.log'
        bot_log = self.logs_dir / player / f'botdata_{run_number}.log'
        
        try:
            # Process logs and create individual plots
            player_data = self._process_player_log(player_log)
            bot_data = self._process_bot_log(bot_log)
            
            # Save individual plots
            output_dir = self.analysis_dir / 'players' / player / control_type / 'Player'
            self._create_player_plots(player_data, output_dir, run_number)
            
            # Create comparison plots
            comp_dir = self.analysis_dir / 'players' / player / control_type / 'Comparisons'
            self._create_comparison_plots(player_data, bot_data, comp_dir, run_number)
            
            return player_data, bot_data
            
        except Exception as e:
            print(f"Error processing run: {e}")
            return None, None

    

    def analyze_bot_performance(self):
        """Analyze all bot runs across all players and conditions."""
        print("\nAnalyzing overall bot performance")
        bot_dir = self.analysis_dir / 'bot'
        all_bot_data = []
        
        for player in self.players:
            for run in range(1, 16):  # 15 runs per player
                try:
                    bot_log = self.logs_dir / player / f'botdata_{run}.log'
                    bot_data = self._process_bot_log(bot_log)
                    all_bot_data.append(bot_data)
                except Exception as e:
                    print(f"Error processing bot data for {player} run {run}: {e}")
        
        if all_bot_data:
            self._create_bot_analysis_plots(all_bot_data, bot_dir)
            print("Created bot analysis plots")

    def create_overall_analysis(self):
        """Create comprehensive comparison plots and statistics."""
        print("\nCreating overall analysis")
        overall_dir = self.analysis_dir / 'overall'
        
        # Collect all data
        all_data = {
            'player': {player: {} for player in self.players},
            'bot': {player: {} for player in self.players}
        }
        
        for player in self.players:
            for control_type in self.control_types[:-1]:  # Exclude 'Bot' from control types
                player_runs = []
                bot_runs = []
                
                for run in range(1, 6):
                    try:
                        player_log = self.logs_dir / player / f'cardata_{run}.log'
                        bot_log = self.logs_dir / player / f'botdata_{run}.log'
                        
                        player_runs.append(self._process_player_log(player_log))
                        bot_runs.append(self._process_bot_log(bot_log))
                    except Exception as e:
                        print(f"Error processing {player} {control_type} run {run}: {e}")
                
                if player_runs:
                    all_data['player'][player][control_type] = player_runs
                    all_data['bot'][player][control_type] = bot_runs
        
        self._create_overall_analysis_plots(all_data, overall_dir)
        print("Created overall analysis plots")

    def _process_player_log(self, log_file):
        """Process a player log file and return structured data."""
        data = {
            'time': [],
            'car_x': [],
            'car_y': [],
            'target_angle': [], 
            'current_angle': [],
            'diff': [],
            'control': []
        }
        
        try:
            with open(log_file, "r") as file:
                current_time = None
                current_set = {}
                
                for line in file:
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        
                        if 'updateTireWear: car Location i=' in line:
                            i_match = re.search(r'car Location i=\s*([\d\.-]+)', line)
                            if i_match:
                                current_set['car_x'] = float(i_match.group(1))
                                
                        elif 'updateTireWear: car Location j=' in line:
                            j_match = re.search(r'car Location j=\s*([\d\.-]+)', line)
                            if j_match:
                                current_set['car_y'] = float(j_match.group(1))
                                
                        elif 'Continuous angles:' in line:
                            angles_match = re.search(r'target=([\d\.-]+), current=([\d\.-]+)', line)
                            if angles_match:
                                current_set['target_angle'] = float(angles_match.group(1))
                                current_set['current_angle'] = float(angles_match.group(2))
                                
                        elif 'Track assistance:' in line:
                            assist_match = re.search(r'angle=[\d\.-]+, cur=[\d\.-]+, diff=([\d\.-]+), control=([\d\.-]+)', line)
                            if assist_match:
                                current_set['diff'] = float(assist_match.group(1))
                                current_set['control'] = float(assist_match.group(2))
                                
                                if len(current_set) == 6:  # All values except time
                                    data['time'].append(current_time)
                                    data['car_x'].append(current_set['car_x'])
                                    data['car_y'].append(current_set['car_y'])
                                    data['target_angle'].append(current_set['target_angle'])
                                    data['current_angle'].append(current_set['current_angle'])
                                    data['diff'].append(current_set['diff'])
                                    data['control'].append(current_set['control'])
                                    current_set = {}
                                
            return pd.DataFrame(data)
        
        except Exception as e:
            print(f"Error processing player log {log_file}: {e}")
            return None


    def _process_bot_log(self, log_file):
        """Process a bot log file and return structured data."""
        data = {
            'time': [],
            'target_x': [],
            'target_y': [],
            'car_x': [],
            'car_y': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': []
        }
        
        try:
            with open(log_file, "r") as file:
                current_set = {}
                
                for line in file:
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        
                        if 'targetNode X:' in line:
                            x_match = re.search(r'targetNode X:\s*([\d\.-]+)', line)
                            if x_match:
                                current_set['target_x'] = float(x_match.group(1))
                                
                        elif 'targetNode Y:' in line:
                            y_match = re.search(r'targetNode Y:\s*([\d\.-]+)', line)
                            if y_match:
                                current_set['target_y'] = float(y_match.group(1))
                                
                        elif 'car Location i:' in line:
                            i_match = re.search(r'car Location i:\s*([\d\.-]+)', line)
                            if i_match:
                                current_set['car_x'] = float(i_match.group(1))
                                
                        elif 'car Location j:' in line:
                            j_match = re.search(r'car Location j:\s*([\d\.-]+)', line)
                            if j_match:
                                current_set['car_y'] = float(j_match.group(1))
                                
                        elif 'Continuous angles:' in line:
                            angles_match = re.search(r'target=([\d\.-]+), current=([\d\.-]+)', line)
                            if angles_match:
                                current_set['target_angle'] = float(angles_match.group(1))
                                current_set['current_angle'] = float(angles_match.group(2))
                                
                        elif 'steerControl: angle=' in line:
                            control_match = re.search(r'angle=[\d\.-]+, cur=[\d\.-]+, diff=([\d\.-]+), control=([\d\.-]+)', line)
                            if control_match:
                                current_set['diff'] = float(control_match.group(1))
                                current_set['control'] = float(control_match.group(2))
                                
                                if len(current_set) == 8:
                                    data['time'].append(current_time)
                                    for key in data.keys():
                                        if key != 'time':
                                            data[key].append(current_set[key])
                                    current_set = {}
                                    
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error processing bot log {log_file}: {e}")
            return None

    def _create_player_plots(self, data, output_dir, run_number):
        """Create individual player performance plots."""
        if data is None or data.empty:
            print(f"No data available for run {run_number}")
            return
            
        self._set_plot_style()
        
        # Plot 1: Angles and Control
        plt.figure(figsize=(12, 10))
        
        # Target vs Current Angle
        plt.subplot(2, 1, 1)
        plt.plot(data['time'], data['target_angle'], 'r-', label='Target Angle', linewidth=2)
        plt.plot(data['time'], data['current_angle'], 'b-', label='Current Angle', linewidth=2)
        plt.title(f'Steering Angles - Run {run_number}')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Angle (degrees)')
        plt.legend()
        plt.ylim(-180, 180)  # Consistent scale for angles
        
        # Control Input and Difference
        plt.subplot(2, 1, 2)
        plt.plot(data['time'], data['diff'], 'g-', label='Angle Difference', alpha=0.7)
        plt.plot(data['time'], data['control'], 'm-', label='Control Input', alpha=0.7)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Value')
        plt.legend()
        plt.ylim(-1, 1)  # Consistent scale for control values
        
        plt.tight_layout()
        plt.savefig(output_dir / f'run_{run_number}_steering.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_comparison_plots(self, player_data, bot_data, output_dir, run_number):
        """Create comparison plots between player and bot."""
        if player_data is None or bot_data is None or player_data.empty or bot_data.empty:
            print(f"Missing data for comparison in run {run_number}")
            return
            
        self._set_plot_style()
        
        # Plot 1: Control Comparison
        plt.figure(figsize=(12, 8))
        plt.plot(player_data['time'], player_data['control'], 'b-', label='Player Control', alpha=0.7)
        plt.plot(bot_data['time'], bot_data['control'], 'r-', label='Bot Control', alpha=0.7)
        plt.title(f'Control Input Comparison - Run {run_number}')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Control Value')
        plt.legend()
        plt.ylim(-1, 1)  # Consistent scale for control values
        plt.savefig(output_dir / f'run_{run_number}_control_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Trajectory Comparison
        plt.figure(figsize=(12, 8))
        plt.plot(player_data['car_x'], player_data['car_y'], 'b-', label='Player Path', linewidth=2)
        plt.plot(bot_data['car_x'], bot_data['car_y'], 'r-', label='Bot Path', linewidth=2)
        plt.title(f'Path Comparison - Run {run_number}')
        plt.xlabel('X Position')
        plt.ylabel('Y Position')
        plt.legend()
        plt.axis('equal')  # Equal aspect ratio
        plt.savefig(output_dir / f'run_{run_number}_trajectory.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_summary_plots(self, player_data_list, bot_data_list, output_dir):
        """Create summary plots for a set of runs."""
        if not player_data_list or not bot_data_list:
            print("No data available for summary plots")
            return
            
        self._set_plot_style()
        
        # Calculate statistics
        runs = np.arange(1, len(player_data_list) + 1)
        
        # Control values
        player_controls = np.array([data['control'].mean() for data in player_data_list])
        bot_controls = np.array([data['control'].mean() for data in bot_data_list])
        player_control_std = np.array([data['control'].std() for data in player_data_list])
        bot_control_std = np.array([data['control'].std() for data in bot_data_list])
        
        # Completion times
        player_times = np.array([data['time'].max() for data in player_data_list])
        bot_times = np.array([data['time'].max() for data in bot_data_list])
        
        # Plot 1: Average Control Values Comparison
        plt.figure(figsize=(10, 6))
        plt.errorbar(runs, player_controls, yerr=player_control_std, fmt='bo', capsize=5, label='Player')
        plt.errorbar(runs, bot_controls, yerr=bot_control_std, fmt='ro', capsize=5, label='Bot')
        plt.title('Average Control Input by Run')
        plt.xlabel('Run Number')
        plt.ylabel('Average Control Value')
        plt.legend()
        plt.xticks(runs)
        plt.ylim(-1, 1)  # Consistent scale for control values
        plt.savefig(output_dir / 'average_control_summary.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Completion Times
        plt.figure(figsize=(10, 6))
        plt.scatter(runs, player_times, color='blue', marker='o', label='Player')
        plt.scatter(runs, bot_times, color='red', marker='o', label='Bot')
        plt.title('Completion Times by Run')
        plt.xlabel('Run Number')
        plt.ylabel('Time (seconds)')
        plt.legend()
        plt.xticks(runs)
        plt.savefig(output_dir / 'completion_times_summary.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save summary statistics with error metrics
        summary_stats = pd.DataFrame({
            'Run': runs,
            'Player_Avg_Control': player_controls,
            'Player_Control_StdDev': player_control_std,
            'Bot_Avg_Control': bot_controls,
            'Bot_Control_StdDev': bot_control_std,
            'Player_Completion_Time': player_times,
            'Bot_Completion_Time': bot_times
        })
        summary_stats.to_csv(output_dir / 'summary_statistics.csv', index=False)

    def _create_bot_analysis_plots(self, bot_data_list, output_dir):
        """Create comprehensive bot analysis plots."""
        if not bot_data_list:
            print("No bot data available for analysis")
            return
            
        self._set_plot_style()
        
        # Collect statistics across all runs
        completion_times = []
        avg_controls = []
        path_deviations = []
        
        for data in bot_data_list:
            if data is not None and not data.empty:
                completion_times.append(data['time'].max())
                avg_controls.append(data['control'].abs().mean())
                
                # Calculate average deviation from target path
                path_dev = np.mean(np.sqrt(
                    (data['target_x'] - data['car_x'])**2 + 
                    (data['target_y'] - data['car_y'])**2
                ))
                path_deviations.append(path_dev)
        
        # Plot 1: Distribution of Completion Times
        plt.figure(figsize=(10, 6))
        plt.hist(completion_times, bins=15, alpha=0.7)
        plt.axvline(np.mean(completion_times), color='r', linestyle='--', 
                   label=f'Mean: {np.mean(completion_times):.2f}s\nStd: {np.std(completion_times):.2f}s')
        plt.title('Distribution of Bot Completion Times')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Frequency')
        plt.legend()
        plt.savefig(output_dir / 'bot_completion_times_dist.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Control vs Path Deviation
        plt.figure(figsize=(10, 6))
        plt.scatter(avg_controls, path_deviations, alpha=0.6)
        plt.title('Control Input vs Path Deviation')
        plt.xlabel('Average Control Input')
        plt.ylabel('Average Path Deviation')
        plt.savefig(output_dir / 'bot_control_vs_deviation.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_overall_analysis_plots(self, all_data, output_dir):
        """Create overall analysis plots comparing all players and conditions."""
        self._set_plot_style()
        
        # Prepare data for plotting
        stats_data = {
            'condition': [],
            'player': [],
            'mean_time': [],
            'std_time': [],
            'type': []
        }
        
        for data_type in ['player', 'bot']:
            for player in all_data[data_type]:
                for condition in all_data[data_type][player]:
                    if all_data[data_type][player][condition]:
                        times = [data['time'].max() for data in all_data[data_type][player][condition] 
                               if data is not None and not data.empty]
                        if times:
                            stats_data['condition'].append(condition)
                            stats_data['player'].append(player)
                            stats_data['mean_time'].append(np.mean(times))
                            stats_data['std_time'].append(np.std(times))
                            stats_data['type'].append(data_type)
        
        df = pd.DataFrame(stats_data)
        
        # Plot: Completion Times by Condition and Player with Error Bars
        plt.figure(figsize=(15, 8))
        conditions = df['condition'].unique()
        x = np.arange(len(conditions))
        width = 0.25
        
        for i, player in enumerate(['F', 'J', 'M']):
            player_data = df[df['player'] == player]
            if not player_data.empty:
                plt.errorbar(x + i*width, player_data['mean_time'], 
                           yerr=player_data['std_time'],
                           fmt='o', capsize=5, label=f'Player {player}')
        
        plt.xticks(x + width, conditions, rotation=45)
        plt.title('Average Completion Times by Condition and Player')
        plt.xlabel('Condition')
        plt.ylabel('Time (seconds)')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(output_dir / 'overall_completion_times.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save overall statistics
        stats = df.copy()
        stats.to_csv(output_dir / 'overall_statistics.csv', index=False)

    def analyze_player_run(self, player, control_type, run_number):
        """Analyze a single player run and its corresponding bot run."""
        print(f"\nAnalyzing {player}'s {control_type} run #{run_number}")
        
        player_log = self.logs_dir / player / f'cardata_{run_number}.log'
        bot_log = self.logs_dir / player / f'botdata_{run_number}.log'
        
        try:
            # Process logs and create individual plots
            player_data = self._process_player_log(player_log)
            bot_data = self._process_bot_log(bot_log)
            
            # Save individual plots
            output_dir = self.analysis_dir / 'players' / player / control_type / 'Player'
            self._create_player_plots(player_data, output_dir, run_number)
            
            # Create comparison plots
            comp_dir = self.analysis_dir / 'players' / player / control_type / 'Comparisons'
            self._create_comparison_plots(player_data, bot_data, comp_dir, run_number)
            
            return player_data, bot_data
            
        except Exception as e:
            print(f"Error processing run: {e}")
            return None, None

    def analyze_player_set(self, player, control_type):
        """Analyze all runs for a player under a specific control type."""
        print(f"\nAnalyzing complete set for {player} - {control_type}")
        all_player_data = []
        all_bot_data = []
        
        start_run = {
            '1.0 Control Assistance': 1,
            '0.0 Control Assistance': 6,
            '0.2 Control Assistance': 11
        }
        
        for run in range(start_run[control_type], start_run[control_type] + 5):  # 5 runs per condition
            p_data, b_data = self.analyze_player_run(player, control_type, run)
            if p_data is not None and b_data is not None:
                all_player_data.append(p_data)
                all_bot_data.append(b_data)
        
        if all_player_data:
            # Create summary plots
            summary_dir = self.analysis_dir / 'players' / player / control_type / 'Summary'
            self._create_summary_plots(all_player_data, all_bot_data, summary_dir)
            print(f"Created summary plots for {player} - {control_type}")

def run_complete_analysis():
    """Run the complete analysis pipeline."""
    start_time = time.time()
    
    print("=== Starting Complete Analysis ===")
    
    analyzer = DataAnalyzer()
    
    print("\n1. Setting up directory structure...")
    analyzer.setup_directories()
    
    print("\n2. Analyzing individual player runs...")
    for player in ['F', 'J', 'M']:
        for control_type in ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance']:
            analyzer.analyze_player_set(player, control_type)
    
    print("\n3. Analyzing bot performance...")
    bot_dir = analyzer.analysis_dir / 'bot'
    all_bot_data = []
    
    for player in ['F', 'J', 'M']:
        for run in range(1, 16):  # 15 runs per player
            try:
                bot_log = analyzer.logs_dir / player / f'botdata_{run}.log'
                bot_data = analyzer._process_bot_log(bot_log)
                if bot_data is not None:
                    all_bot_data.append(bot_data)
            except Exception as e:
                print(f"Error processing bot data for {player} run {run}: {e}")
    
    if all_bot_data:
        analyzer._create_bot_analysis_plots(all_bot_data, bot_dir)
        print("Created bot analysis plots")
    
    print("\n4. Creating overall analysis...")
    all_data = {
        'player': {player: {} for player in ['F', 'J', 'M']},
        'bot': {player: {} for player in ['F', 'J', 'M']}
    }
    
    for player in ['F', 'J', 'M']:
        for control_type in ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance']:
            player_runs = []
            bot_runs = []
            
            start_run = {
                '1.0 Control Assistance': 1,
                '0.0 Control Assistance': 6,
                '0.2 Control Assistance': 11
            }
            
            for run in range(start_run[control_type], start_run[control_type] + 5):  # 5 runs per condition
                try:
                    player_log = analyzer.logs_dir / player / f'cardata_{run}.log'
                    bot_log = analyzer.logs_dir / player / f'botdata_{run}.log'
                    
                    player_runs.append(analyzer._process_player_log(player_log))
                    bot_runs.append(analyzer._process_bot_log(bot_log))
                except Exception as e:
                    print(f"Error processing {player} {control_type} run {run}: {e}")
            
            if player_runs:
                all_data['player'][player][control_type] = player_runs
                all_data['bot'][player][control_type] = bot_runs
    
    overall_dir = analyzer.analysis_dir / 'overall'
    analyzer._create_overall_analysis_plots(all_data, overall_dir)
    print("Created overall analysis plots")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n=== Analysis Complete ===")
    print(f"Total processing time: {duration:.2f} seconds")

if __name__ == "__main__":
    try:
        run_complete_analysis()
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred during analysis: {e}")
        sys.exit(1)

