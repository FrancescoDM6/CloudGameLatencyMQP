# run_analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
import time
import sys
import shutil

class DataAnalyzer:
    def __init__(self, base_dir='DustRacing2D-master'):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / 'logs'
        self.analysis_dir = self.base_dir / 'data analysis'
        self.players = ['F', 'J', 'M']
        self.control_types = ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance', 'Bot']
        self.lag_conditions = ['0 Lag', '100 Lag']
        
        # Updated run mappings
        self.run_mappings = {
            'J': {
                '1.0 Control Assistance': (6, 10),    # runs 1-5
                '0.0 Control Assistance': (1, 5),   # runs 6-10
                '0.2 Control Assistance': (11, 15)   # runs 11-15
            },
            'F': {
                '1.0 Control Assistance': (1, 5),    # runs 6-10
                '0.0 Control Assistance': (6, 10),     # runs 1-5
                '0.2 Control Assistance': (11, 15)    # runs 11-15
            },
            'M': {
                '1.0 Control Assistance': (1, 5),    # runs 6-10
                '0.0 Control Assistance': (6, 10),     # runs 1-5
                '0.2 Control Assistance': (11, 15)    # runs 11-15
            }
        }
        
    def _set_plot_style(self):
        """Set consistent plot styling."""
        plt.style.use('default')
        plt.rcParams['axes.grid'] = False  # Remove grid
        plt.rcParams['axes.formatter.use_locale'] = True  # For proper number formatting
        
    def _convert_game_time(self, time_str):
        """Convert game time string to seconds."""
        minutes, seconds = time_str.split(':')
        return float(minutes) * 60 + float(seconds)
    
    def _find_global_time_range(self):
        """Find global min and max completion times across all conditions."""
        min_time = float('inf')
        max_time = float('-inf')
        
        for player in self.players:
            for lag_condition in ['0 Lag', '100 Lag']:
                for control_type in ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance']:
                    # Get run range for this condition
                    start_run, end_run = self.run_mappings[player][control_type]
                    
                    # Check each run's lap times
                    for run in range(start_run, end_run + 1):
                        lap_log = self.logs_dir / player / lag_condition / f'laptime_{run}.log'
                        bot_time, player_time = self._process_lap_time(lap_log)
                        
                        if bot_time is not None:
                            min_time = min(min_time, bot_time)
                            max_time = max(max_time, bot_time)
                        if player_time is not None:
                            min_time = min(min_time, player_time)
                            max_time = max(max_time, player_time)
        
        # Add some padding
        time_range = max_time - min_time
        min_time = min_time - (time_range * 0.1)
        max_time = max_time + (time_range * 0.1)
        
        return min_time, max_time
    

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
        
        # Create a single figure with three subplots
        plt.figure(figsize=(12, 15))
        
        # Plot 1: Steering Angles
        plt.subplot(3, 1, 1)
        plt.plot(data['time'], data['target_angle'], 'r-', label='Target Angle', linewidth=2)
        plt.plot(data['time'], data['current_angle'], 'b-', label='Current Angle', linewidth=2)
        plt.title(f'Steering Analysis - Run {run_number}')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Angle (degrees)')
        plt.legend()
        plt.ylim(0, max(data['target_angle'].max(), data['current_angle'].max()) * 1.1)  # Auto-scale with 10% padding
        
        # Plot 2: Angle Difference
        plt.subplot(3, 1, 2)
        plt.plot(data['time'], data['diff'], 'g-', label='Angle Difference', alpha=0.7)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Difference (degrees)')
        plt.legend()
        # Set symmetric limits based on max absolute difference
        max_diff = max(abs(data['diff'].min()), abs(data['diff'].max()))
        plt.ylim(-max_diff * 1.1, max_diff * 1.1)  # Add 10% padding
        
        # Plot 3: Control Input
        plt.subplot(3, 1, 3)
        plt.plot(data['time'], data['control'], 'm-', label='Control Input', alpha=0.7)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Control Value')
        plt.legend()
        plt.ylim(0, 2)  # Fixed scale 0-2 for control values
        
        plt.tight_layout()
        plt.savefig(output_dir / f'run_{run_number}_steering_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()


    def _process_lap_time(self, log_file):
        """Process a lap time log file and return completion times."""
        try:
            # print(f"Processing lap time file: {log_file}")  # Debug print
            
            with open(log_file, "r") as file:
                bot_time = None
                player_time = None
                
                for line in file:
                    print(f"Processing line: {line.strip()}")  # Debug print
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        game_time = self._convert_game_time(time_match.group(1))
                        
                        if 'Bot finish time:' in line:
                            print(f"Found bot time: {game_time}")  # Debug print
                            bot_time = game_time
                        elif 'Player finish time:' in line:
                            print(f"Found player time: {game_time}")  # Debug print
                            player_time = game_time
                
                if bot_time is None or player_time is None:
                    print(f"Missing times - Bot: {bot_time}, Player: {player_time}")  # Debug print
                    
                return bot_time, player_time
                
        except Exception as e:
            print(f"Error processing lap time log {log_file}: {e}")
            return None, None

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
        plt.ylim(0, 2)  # Fixed scale 0-2 for control values
        plt.savefig(output_dir / f'run_{run_number}_control_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_summary_plots(self, player_data_list, bot_data_list, output_dir, run_start):
        """Create summary plots for a set of runs."""
        if not player_data_list or not bot_data_list:
            print("No data available for summary plots")
            return
            
        self._set_plot_style()
        
        # Extract player and lag condition from path
        path_parts = output_dir.parts
        players_idx = path_parts.index('players')
        player = path_parts[players_idx + 1]
        lag_condition = path_parts[players_idx + 2]
        
        # Get global time range
        min_time, max_time = self._find_global_time_range()
        
        # Collect lap times
        player_times = []
        bot_times = []
        runs = []
        
        for i, _ in enumerate(player_data_list, start=run_start):
            lap_log = self.logs_dir / player / lag_condition / f'laptime_{i}.log'
            bot_time, player_time = self._process_lap_time(lap_log)
            
            if bot_time is not None and player_time is not None:
                player_times.append(player_time)
                bot_times.append(bot_time)
                runs.append(i)
        
        if runs:
            # Plot: Completion Times
            plt.figure(figsize=(10, 6))
            plt.scatter(runs, player_times, color='blue', marker='o', label='Player')
            plt.scatter(runs, bot_times, color='red', marker='o', label='Bot')
            plt.title('Completion Times by Run')
            plt.xlabel('Run Number')
            plt.ylabel('Time (seconds)')
            plt.legend()
            plt.xticks(runs)
            plt.ylim(min_time, max_time)  # Use global scale
            plt.savefig(output_dir / 'completion_times_summary.png', dpi=300, bbox_inches='tight')
            plt.close()

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
        
        # Get global time range
        min_time, max_time = self._find_global_time_range()
        
        # Prepare data for plotting
        stats_data = []  # Use a list of dictionaries for better control
        
        # Process both player and bot data
        for data_type in ['player', 'bot']:
            for player in all_data[data_type]:
                for lag_condition in ['0 Lag', '100 Lag']:
                    for control_type in ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance']:
                        times = []
                        start_run, end_run = self.run_mappings[player][control_type]
                        
                        # Debug print
                        print(f"Processing {player} - {lag_condition} - {control_type} - {data_type}")
                        print(f"Run range: {start_run} to {end_run}")
                        
                        for run in range(start_run, end_run + 1):
                            lap_log = self.logs_dir / player / lag_condition / f'laptime_{run}.log'
                            bot_time, player_time = self._process_lap_time(lap_log)
                            time_to_use = bot_time if data_type == 'bot' else player_time
                            if time_to_use is not None:
                                times.append(time_to_use)
                        
                        if times:
                            mean_time = np.mean(times)
                            std_time = np.std(times)
                            # Debug print
                            print(f"Found {len(times)} times, mean: {mean_time:.2f}, std: {std_time:.2f}")
                            
                            stats_data.append({
                                'condition': control_type,
                                'player': player,
                                'mean_time': mean_time,
                                'std_time': std_time,
                                'type': data_type,
                                'lag': int(lag_condition.split()[0])
                            })
        
        df = pd.DataFrame(stats_data)
        
        # Debug print
        print("\nDataFrame contents:")
        print(df)
        
        # Plot 1: Control Type Comparison
        plt.figure(figsize=(15, 8))
        conditions = df['condition'].unique()
        x = np.arange(len(conditions))
        width = 0.15
        
        # Plot for each player and bot
        for i, player in enumerate(self.players):
            # Debug prints
            print(f"\nProcessing player {player}")
            
            # Plot player data
            player_data = df[(df['player'] == player) & (df['type'] == 'player')]
            print(f"Player data shape: {player_data.shape}")
            if not player_data.empty:
                means = [player_data[player_data['condition'] == cond]['mean_time'].mean() 
                        for cond in conditions]
                stds = [player_data[player_data['condition'] == cond]['std_time'].mean() 
                       for cond in conditions]
                print(f"Player means: {means}")
                print(f"Player stds: {stds}")
                plt.errorbar(x + i*width, means, yerr=stds,
                           fmt='o', capsize=5, label=f'Player {player}')
            
            # Plot bot data
            bot_data = df[(df['player'] == player) & (df['type'] == 'bot')]
            print(f"Bot data shape: {bot_data.shape}")
            if not bot_data.empty:
                means = [bot_data[bot_data['condition'] == cond]['mean_time'].mean() 
                        for cond in conditions]
                stds = [bot_data[bot_data['condition'] == cond]['std_time'].mean() 
                       for cond in conditions]
                print(f"Bot means: {means}")
                print(f"Bot stds: {stds}")
                plt.errorbar(x + i*width + width/2, means, yerr=stds,
                           fmt='s', capsize=5, label=f'Bot {player}')
        
        plt.xticks(x + width*1.5, conditions, rotation=45)
        plt.title('Average Completion Times by Condition and Player')
        plt.xlabel('Condition')
        plt.ylabel('Time (seconds)')
        plt.legend()
        plt.ylim(min_time, max_time)
        plt.tight_layout()
        plt.savefig(output_dir / 'overall_completion_times.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Lag Comparison
        plt.figure(figsize=(12, 8))
        for player in self.players:
            # Debug print
            print(f"\nProcessing lag comparison for {player}")
            
            # Plot player performance vs lag
            player_data = df[(df['player'] == player) & (df['type'] == 'player')].groupby('lag')['mean_time'].mean()
            print(f"Player lag data: {player_data}")
            if not player_data.empty:
                plt.plot([0, 100], [player_data[0], player_data[100]], 'o-', label=f'Player {player}')
            
            # Plot bot performance vs lag
            bot_data = df[(df['player'] == player) & (df['type'] == 'bot')].groupby('lag')['mean_time'].mean()
            print(f"Bot lag data: {bot_data}")
            if not bot_data.empty:
                plt.plot([0, 100], [bot_data[0], bot_data[100]], 's--', label=f'Bot {player}')
        
        plt.title('Performance vs Lag')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Average Completion Time (seconds)')
        plt.legend()
        plt.ylim(min_time, max_time)
        plt.grid(True)
        plt.savefig(output_dir / 'lag_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save overall statistics
        stats = df.sort_values(['player', 'condition', 'lag']).round(2)
        stats.to_csv(output_dir / 'overall_statistics.csv', index=False)

    def analyze_player_run(self, player, lag_condition, control_type, run_number):
        """Analyze a single player run and its corresponding bot run."""
        print(f"\nAnalyzing {player}'s {lag_condition} {control_type} run #{run_number}")
        
        player_log = self.logs_dir / player / lag_condition / f'cardata_{run_number}.log'
        bot_log = self.logs_dir / player / lag_condition / f'botdata_{run_number}.log'
        
        try:
            # Process logs and create individual plots
            player_data = self._process_player_log(player_log)
            bot_data = self._process_bot_log(bot_log)
            
            # Save individual plots
            output_dir = self.analysis_dir / 'players' / player / lag_condition / control_type / 'Player'
            self._create_player_plots(player_data, output_dir, run_number)
            
            # Create comparison plots
            comp_dir = self.analysis_dir / 'players' / player / lag_condition / control_type / 'Comparisons'
            self._create_comparison_plots(player_data, bot_data, comp_dir, run_number)
            
            return player_data, bot_data
            
        except Exception as e:
            print(f"Error processing run: {e}")
            return None, None

    def analyze_player_set(self, player, lag_condition, control_type):
        """Analyze all runs for a player under specific conditions."""
        print(f"\nAnalyzing complete set for {player} - {lag_condition} - {control_type}")
        all_player_data = []
        all_bot_data = []
        
        start_run, end_run = self.run_mappings[player][control_type]
        
        for run in range(start_run, end_run + 1):
            p_data, b_data = self.analyze_player_run(player, lag_condition, control_type, run)
            if p_data is not None and b_data is not None:
                all_player_data.append(p_data)
                all_bot_data.append(b_data)
        
        if all_player_data:
            # Create summary plots
            summary_dir = self.analysis_dir / 'players' / player / lag_condition / control_type / 'Summary'
            self._create_summary_plots(all_player_data, all_bot_data, summary_dir, start_run)  # Added start_run parameter
            print(f"Created summary plots for {player} - {lag_condition} - {control_type}")

    def setup_directories(self):
        """Create all necessary directories for analysis."""
        print("\nSetting up directory structure...")
        
        # Store scripts directory content if it exists
        scripts_dir = self.analysis_dir / 'scripts'
        scripts_backup = None
        if scripts_dir.exists():
            scripts_backup = scripts_dir
        
        # Remove old analysis directory contents except scripts
        if self.analysis_dir.exists():
            print("Removing old analysis directory contents...")
            for item in self.analysis_dir.iterdir():
                if item.name != 'scripts':
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        else:
            self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Restore scripts directory if it was backed up
        if scripts_backup is not None:
            scripts_dir = self.analysis_dir / 'scripts'
            print("Preserving scripts directory...")
        
        # Create analysis directories
        for player in self.players:
            for lag_condition in self.lag_conditions:
                # Create player-specific directories
                for control_type in self.control_types:
                    if control_type != 'Bot':
                        for subdir in ['Player', 'Comparisons', 'Summary']:
                            dir_path = self.analysis_dir / 'players' / player / lag_condition / control_type / subdir
                            dir_path.mkdir(parents=True, exist_ok=True)
                            print(f"Created {subdir} directory for {player}/{lag_condition}/{control_type}")
                            
        # Create bot and overall analysis directories for each lag condition
        for lag_condition in self.lag_conditions:
            (self.analysis_dir / 'bot' / lag_condition).mkdir(parents=True, exist_ok=True)
            (self.analysis_dir / 'overall' / lag_condition).mkdir(parents=True, exist_ok=True)
            print(f"Created bot and overall analysis directories for {lag_condition}")

def run_complete_analysis():
    """Run the complete analysis pipeline."""
    start_time = time.time()
    
    print("=== Starting Complete Analysis ===")
    
    analyzer = DataAnalyzer()
    
    print("\n1. Setting up directory structure...")
    analyzer.setup_directories()
    
    print("\n2. Analyzing individual player runs...")
    for player in ['F', 'J', 'M']:
        for lag_condition in ['0 Lag', '100 Lag']:
            for control_type in ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance']:
                analyzer.analyze_player_set(player, lag_condition, control_type)
    
    print("\n3. Analyzing bot performance...")
    for lag_condition in ['0 Lag', '100 Lag']:
        bot_dir = analyzer.analysis_dir / 'bot' / lag_condition
        all_bot_data = []
        
        for player in ['F', 'J', 'M']:
            for run in range(1, 16):
                try:
                    bot_log = analyzer.logs_dir / player / lag_condition / f'botdata_{run}.log'
                    bot_data = analyzer._process_bot_log(bot_log)
                    if bot_data is not None:
                        all_bot_data.append(bot_data)
                except Exception as e:
                    print(f"Error processing bot data for {player} {lag_condition} run {run}: {e}")
        
        if all_bot_data:
            analyzer._create_bot_analysis_plots(all_bot_data, bot_dir)
            print(f"Created bot analysis plots for {lag_condition}")
    
    print("\n4. Creating overall analysis...")
    for lag_condition in ['0 Lag', '100 Lag']:
        all_data = {
            'player': {player: {} for player in ['F', 'J', 'M']},
            'bot': {player: {} for player in ['F', 'J', 'M']}
        }
        
        for player in ['F', 'J', 'M']:
            for control_type in ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance']:
                player_runs = []
                bot_runs = []
                
                start_run, end_run = analyzer.run_mappings[player][control_type]
                
                for run in range(start_run, end_run + 1):
                    try:
                        player_log = analyzer.logs_dir / player / lag_condition / f'cardata_{run}.log'
                        bot_log = analyzer.logs_dir / player / lag_condition / f'botdata_{run}.log'
                        
                        player_runs.append(analyzer._process_player_log(player_log))
                        bot_runs.append(analyzer._process_bot_log(bot_log))
                    except Exception as e:
                        print(f"Error processing {player} {lag_condition} {control_type} run {run}: {e}")
                
                if player_runs:
                    all_data['player'][player][control_type] = player_runs
                    all_data['bot'][player][control_type] = bot_runs
        
        overall_dir = analyzer.analysis_dir / 'overall' / lag_condition
        analyzer._create_overall_analysis_plots(all_data, overall_dir)
        print(f"Created overall analysis plots for {lag_condition}")
    
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

