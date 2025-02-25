# run_analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
import time
import sys
import seaborn as sns
from collections import defaultdict

class DataAnalyzer:
    def __init__(self, base_dir='DustRacing2D-master'):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / 'logs'
        self.analysis_dir = self.base_dir / 'data analysis'
        self.players = ['F', 'J', 'M']
        self.control_types = ['Full AI', 'Full Player', 'Mixed', 'Bot']
        
    def setup_directories(self):
        """Create all necessary directories for analysis."""
        print("\nSetting up directory structure...")
        
        # Create logs directories
        for player in self.players:
            (self.logs_dir / player).mkdir(parents=True, exist_ok=True)
            print(f"Created logs directory for player {player}")
        
        # Create analysis directories
        player_analysis_subdirs = ['Player', 'Comparisons', 'Summary']
        
        for player in self.players:
            player_base = self.analysis_dir / 'players' / player
            for control in self.control_types:
                control_dir = player_base / control
                if control != 'Bot':
                    for subdir in player_analysis_subdirs:
                        (control_dir / subdir).mkdir(parents=True, exist_ok=True)
                        print(f"Created {subdir} directory for {player}/{control}")
                else:
                    control_dir.mkdir(parents=True, exist_ok=True)
                    print(f"Created Bot directory for {player}")
        
        # Create bot and overall analysis directories
        (self.analysis_dir / 'bot').mkdir(parents=True, exist_ok=True)
        (self.analysis_dir / 'overall').mkdir(parents=True, exist_ok=True)
        print("Created bot and overall analysis directories")

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
        
        for run in range(1, 6):  # 5 runs per condition
            p_data, b_data = self.analyze_player_run(player, control_type, run)
            if p_data is not None and b_data is not None:
                all_player_data.append(p_data)
                all_bot_data.append(b_data)
        
        if all_player_data:
            # Create summary plots
            summary_dir = self.analysis_dir / 'players' / player / control_type / 'Summary'
            self._create_summary_plots(all_player_data, all_bot_data, summary_dir)
            print(f"Created summary plots for {player} - {control_type}")

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

    # Placeholder methods - to be implemented based on actual log formats
    def _process_player_log(self, log_file):
        """Process a player log file."""
        data = {
            'time': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': [],
            'steering_direction': []
        }
        
        try:
            with open(log_file, "r", encoding='utf-8') as file:  # Ensure proper encoding
                current_time = None
                current_set = {}
                
                for line in file:
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        
                        # Extract different types of data based on line content
                        if 'Track assistance:' in line:
                            assist_match = re.search(r'angle=([\d\.-]+), cur=([\d\.-]+), diff=([\d\.-]+), control=([\d\.-]+)', line)
                            if assist_match:
                                current_set['target_angle'] = float(assist_match.group(1))
                                current_set['current_angle'] = float(assist_match.group(2))
                                current_set['diff'] = float(assist_match.group(3))
                                current_set['control'] = float(assist_match.group(4))
                                
                        elif 'Steering' in line:
                            direction_match = re.search(r'Steering (LEFT|RIGHT)', line)
                            if direction_match:
                                current_set['steering_direction'] = direction_match.group(1)
                                
                                # If we have all data for this timestep, add it to our main data structure
                                if len(current_set) == 5:  # All values except time
                                    data['time'].append(current_time)
                                    data['target_angle'].append(current_set['target_angle'])
                                    data['current_angle'].append(current_set['current_angle'])
                                    data['diff'].append(current_set['diff'])
                                    data['control'].append(current_set['control'])
                                    data['steering_direction'].append(current_set['steering_direction'])
                                    current_set = {}
                                    
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error processing player log {log_file}: {e}")
            return None

    def _process_bot_log(self, log_file):
        """Process a bot log file."""
        data = {
            'time': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': [],
            'steering_direction': []
        }
        
        try:
            with open(log_file, "r", encoding='utf-8') as file:  # Ensure proper encoding
                current_time = None
                current_set = {}
                
                for line in file:
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        
                        # Extract different types of data based on line content
                        if 'steerControl:' in line:
                            assist_match = re.search(r'angle=([\d\.-]+), cur=([\d\.-]+), diff=([\d\.-]+), control=([\d\.-]+)', line)
                            if assist_match:
                                current_set['target_angle'] = float(assist_match.group(1))
                                current_set['current_angle'] = float(assist_match.group(2))
                                current_set['diff'] = float(assist_match.group(3))
                                current_set['control'] = float(assist_match.group(4))
                                
                        elif 'Car turned/is turning' in line:
                            direction_match = re.search(r'Car turned/is turning (LEFT|RIGHT)', line)
                            if direction_match:
                                current_set['steering_direction'] = direction_match.group(1)
                                
                                # If we have all data for this timestep, add it to our main data structure
                                if len(current_set) == 5:  # All values except time
                                    data['time'].append(current_time)
                                    data['target_angle'].append(current_set['target_angle'])
                                    data['current_angle'].append(current_set['current_angle'])
                                    data['diff'].append(current_set['diff'])
                                    data['control'].append(current_set['control'])
                                    data['steering_direction'].append(current_set['steering_direction'])
                                    current_set = {}
                                    
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error processing bot log {log_file}: {e}")
            return None

    def _parse_laptime_log(self, log_file):
        """Parse the laptime log file to get finish times."""
        try:
            with open(log_file, "r") as file:
                bot_time = None
                player_time = None
                
                for line in file:
                    if 'Bot finish time:' in line:
                        bot_match = re.search(r'Bot finish time:\s*([\d\.]+)', line)
                        if bot_match:
                            bot_time = float(bot_match.group(1))
                    elif 'Player finish time:' in line:
                        player_match = re.search(r'Player finish time:\s*([\d\.]+)', line)
                        if player_match:
                            player_time = float(player_match.group(1))
                            
                return player_time, bot_time
                
        except Exception as e:
            print(f"Error processing laptime log {log_file}: {e}")
            return None, None

    def _create_player_plots(self, data, output_dir, run_number):
        """Create individual player performance plots."""
        if data is None or data.empty:
            print(f"No data available for run {run_number}")
            return
            
        plt.style.use('default')
        
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
        plt.grid(True)
        
        # Control Input and Difference
        plt.subplot(2, 1, 2)
        plt.plot(data['time'], data['diff'], 'g-', label='Angle Difference', alpha=0.7)
        plt.plot(data['time'], data['control'], 'm-', label='Control Input', alpha=0.7)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Value')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(output_dir / f'run_{run_number}_steering.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_comparison_plots(self, player_data, bot_data, output_dir, run_number):
        """Create comparison plots between player and bot."""
        if player_data is None or bot_data is None or player_data.empty or bot_data.empty:
            print(f"Missing data for comparison in run {run_number}")
            return
            
        plt.style.use('default')
        
        # Plot 1: Control Comparison
        plt.figure(figsize=(12, 8))
        plt.plot(player_data['time'], player_data['control'], 'b-', label='Player Control', alpha=0.7)
        plt.plot(bot_data['time'], bot_data['control'], 'r-', label='Bot Control', alpha=0.7)
        plt.title(f'Control Input Comparison - Run {run_number}')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Control Value')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / f'run_{run_number}_control_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Trajectory Comparison (for bot data only as it has position)
        plt.figure(figsize=(12, 8))
        plt.plot(bot_data['car_x'], bot_data['car_y'], 'b-', label='Actual Path', linewidth=2)
        plt.plot(bot_data['target_x'], bot_data['target_y'], 'r--', label='Target Path', alpha=0.7)
        plt.title(f'Bot Trajectory - Run {run_number}')
        plt.xlabel('X Position')
        plt.ylabel('Y Position')
        plt.legend()
        plt.grid(True)
        plt.axis('equal')  # Equal aspect ratio
        plt.savefig(output_dir / f'run_{run_number}_trajectory.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_summary_plots(self, player_data_list, bot_data_list, output_dir):
        """Create summary plots for a set of runs."""
        if not player_data_list or not bot_data_list:
            print("No data available for summary plots")
            return
            
        # Calculate average control values for each run
        player_avg_control = [data['control'].mean() for data in player_data_list]
        bot_avg_control = [data['control'].mean() for data in bot_data_list]
        
        # Calculate average completion times
        player_completion = [data['time'].max() for data in player_data_list]
        bot_completion = [data['time'].max() for data in bot_data_list]
        
        plt.style.use('default')
        
        # Plot 1: Average Control Values Comparison
        plt.figure(figsize=(10, 6))
        runs = range(1, len(player_data_list) + 1)
        plt.plot(runs, player_avg_control, 'bo-', label='Player')
        plt.plot(runs, bot_avg_control, 'ro-', label='Bot')
        plt.title('Average Control Input by Run')
        plt.xlabel('Run Number')
        plt.ylabel('Average Control Value')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / 'average_control_summary.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Completion Times
        plt.figure(figsize=(10, 6))
        plt.plot(runs, player_completion, 'bo-', label='Player')
        plt.plot(runs, bot_completion, 'ro-', label='Bot')
        plt.title('Completion Times by Run')
        plt.xlabel('Run Number')
        plt.ylabel('Time (seconds)')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / 'completion_times_summary.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save summary statistics to CSV
        summary_stats = pd.DataFrame({
            'Run': runs,
            'Player_Avg_Control': player_avg_control,
            'Bot_Avg_Control': bot_avg_control,
            'Player_Completion_Time': player_completion,
            'Bot_Completion_Time': bot_completion
        })
        summary_stats.to_csv(output_dir / 'summary_statistics.csv', index=False)

    def _create_bot_analysis_plots(self, bot_data_list, output_dir):
        """Create comprehensive bot analysis plots."""
        if not bot_data_list:
            print("No bot data available for analysis")
            return
            
        # Collect statistics across all runs
        completion_times = []
        avg_controls = []
        path_deviations = []  # Average distance from target path
        
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
        
        plt.style.use('default')
        
        # Plot 1: Distribution of Completion Times
        plt.figure(figsize=(10, 6))
        plt.hist(completion_times, bins=15, alpha=0.7)
        plt.axvline(np.mean(completion_times), color='r', linestyle='--', label='Mean')
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
        plt.grid(True)
        plt.savefig(output_dir / 'bot_control_vs_deviation.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_overall_analysis_plots(self, all_data, output_dir):
        """Create overall analysis plots comparing all players and conditions."""
        plt.style.use('default')
        
        # Prepare data for plotting
        completion_times = {
            'condition': [],
            'player': [],
            'time': [],
            'type': []
        }
        
        for data_type in ['player', 'bot']:
            for player in all_data[data_type]:
                for condition in all_data[data_type][player]:
                    for run_data in all_data[data_type][player][condition]:
                        if run_data is not None and not run_data.empty:
                            completion_times['condition'].append(condition)
                            completion_times['player'].append(player)
                            completion_times['time'].append(run_data['time'].max())
                            completion_times['type'].append(data_type)
        
        df = pd.DataFrame(completion_times)
        
        # Plot 1: Completion Times by Condition and Player
        plt.figure(figsize=(15, 8))
        positions = range(len(df['condition'].unique()))
        
        for i, player in enumerate(['F', 'J', 'M']):
            player_data = df[df['player'] == player]
            
            # Plot player times
            plt.boxplot([player_data[player_data['condition'] == cond]['time'] 
                        for cond in df['condition'].unique()],
                       positions=[p + i*0.3 for p in positions],
                       widths=0.2,
                       patch_artist=True,
                       boxprops=dict(facecolor=f'C{i}', alpha=0.5))
        
        plt.xticks([p + 0.3 for p in positions], df['condition'].unique())
        plt.title('Completion Times by Condition and Player')
        plt.xlabel('Condition')
        plt.ylabel('Time (seconds)')
        plt.legend(['Player F', 'Player J', 'Player M'])
        plt.grid(True, axis='y')
        plt.savefig(output_dir / 'overall_completion_times.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save overall statistics
        stats = df.groupby(['condition', 'player', 'type'])['time'].agg([
            'mean', 'std', 'min', 'max'
        ]).round(2)
        stats.to_csv(output_dir / 'overall_statistics.csv')

    def _convert_game_time(self, time_str):
        """Convert game time string (MM:SS.ms) to seconds."""
        minutes, seconds = time_str.split(':')
        return float(minutes) * 60 + float(seconds)
    

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
import time
import sys

class BotAnalyzer:
    def __init__(self, base_dir='DustRacing2D-master'):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / 'LagTesting' / 'logs' / 'assist_1.0'
        self.analysis_dir = self.base_dir / 'data analysis' / 'bot_vs_bot'
        
        # Configurable parameters
        self.excluded_lags = [50, 100, 150]  # Add/remove lag values to exclude
        self.lag_values = sorted([int(f.name.split('_')[1]) for f in self.logs_dir.glob('lag_*') 
                                if int(f.name.split('_')[1]) not in self.excluded_lags])
        self.max_runs = 30  # Maximum number of runs to process per lag condition
        
        self.setup_directories()

    def setup_directories(self):
        """Create all necessary directories for bot vs bot analysis."""
        print("\nSetting up directory structure...")
        
        # Create analysis directories for each assistance level
        for assist in self.lag_values:
            assist_dir = self.analysis_dir / f'assist_{assist}'
            for subdir in ['Individual', 'Comparisons', 'Summary']:
                (assist_dir / subdir).mkdir(parents=True, exist_ok=True)
                print(f"Created {subdir} directory for assist_{assist}")
        
        # Create overall analysis directory
        (self.analysis_dir / 'overall').mkdir(parents=True, exist_ok=True)
        print("Created overall analysis directory")

    def analyze_all_lag_conditions(self):
        """Analyze all lag conditions and generate comprehensive plots."""
        all_bot1_data = []
        all_bot2_data = []
        completion_times = []
        lag_values = []
        incomplete_runs = {lag: 0 for lag in self.lag_values}  # Track incomplete runs
        
        for lag in self.lag_values:
            lag_dir = self.logs_dir / f'lag_{lag}'
            if not lag_dir.exists():
                continue
                
            for run_num in range(1, self.max_runs + 1):
                try:
                    bot1_log = lag_dir / f'cardata_{run_num}.log'
                    bot2_log = lag_dir / f'botdata_{run_num}.log'
                    laptime_log = lag_dir / f'laptime_{run_num}.log'
                    
                    if not all(f.exists() for f in [bot1_log, bot2_log, laptime_log]):
                        continue
                        
                    bot1_data = self._process_player_log(bot1_log)
                    bot2_data = self._process_bot_log(bot2_log)
                    bot1_time, bot2_time = self._parse_laptime_log(laptime_log)
                    
                    # Skip incomplete runs (where either bot did not finish)
                    if bot1_time is None or bot2_time is None:
                        incomplete_runs[lag] += 1
                        continue
                    
                    if bot1_data is not None and bot2_data is not None:
                        all_bot1_data.append(bot1_data)
                        all_bot2_data.append(bot2_data)
                        completion_times.append((bot1_time, bot2_time))
                        lag_values.append(lag)
                        
                except Exception as e:
                    print(f"Error processing lag {lag} run {run_num}: {e}")
                    continue
        
        if all_bot1_data:
            # Create comprehensive analysis plots
            self._create_comprehensive_plots(all_bot1_data, all_bot2_data, completion_times, lag_values)
        
        # Print incomplete run statistics
        print("\nIncomplete Runs Statistics:")
        for lag, count in incomplete_runs.items():
            print(f"Lag {lag}ms: {count} incomplete runs")

    def _process_player_log(self, log_file):
        """Process a player log file."""
        data = {
            'time': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': [],
            'steering_direction': []
        }
        
        try:
            with open(log_file, "r", encoding='utf-8') as file:  # Ensure proper encoding
                current_time = None
                current_set = {}
                
                for line in file:
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        
                        # Extract different types of data based on line content
                        if 'Track assistance:' in line:
                            assist_match = re.search(r'angle=([\d\.-]+), cur=([\d\.-]+), diff=([\d\.-]+), control=([\d\.-]+)', line)
                            if assist_match:
                                current_set['target_angle'] = float(assist_match.group(1))
                                current_set['current_angle'] = float(assist_match.group(2))
                                current_set['diff'] = float(assist_match.group(3))
                                current_set['control'] = float(assist_match.group(4))
                                
                        elif 'Steering' in line:
                            direction_match = re.search(r'Steering (LEFT|RIGHT)', line)
                            if direction_match:
                                current_set['steering_direction'] = direction_match.group(1)
                                
                                # If we have all data for this timestep, add it to our main data structure
                                if len(current_set) == 5:  # All values except time
                                    data['time'].append(current_time)
                                    data['target_angle'].append(current_set['target_angle'])
                                    data['current_angle'].append(current_set['current_angle'])
                                    data['diff'].append(current_set['diff'])
                                    data['control'].append(current_set['control'])
                                    data['steering_direction'].append(current_set['steering_direction'])
                                    current_set = {}
                                    
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error processing player log {log_file}: {e}")
            return None

    def _process_bot_log(self, log_file):
        """Process a bot log file."""
        data = {
            'time': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': [],
            'steering_direction': []
        }
        
        try:
            with open(log_file, "r", encoding='utf-8') as file:  # Ensure proper encoding
                current_time = None
                current_set = {}
                
                for line in file:
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        
                        # Extract different types of data based on line content
                        if 'steerControl:' in line:
                            assist_match = re.search(r'angle=([\d\.-]+), cur=([\d\.-]+), diff=([\d\.-]+), control=([\d\.-]+)', line)
                            if assist_match:
                                current_set['target_angle'] = float(assist_match.group(1))
                                current_set['current_angle'] = float(assist_match.group(2))
                                current_set['diff'] = float(assist_match.group(3))
                                current_set['control'] = float(assist_match.group(4))
                                
                        elif 'Car turned/is turning' in line:
                            direction_match = re.search(r'Car turned/is turning (LEFT|RIGHT)', line)
                            if direction_match:
                                current_set['steering_direction'] = direction_match.group(1)
                                
                                # If we have all data for this timestep, add it to our main data structure
                                if len(current_set) == 5:  # All values except time
                                    data['time'].append(current_time)
                                    data['target_angle'].append(current_set['target_angle'])
                                    data['current_angle'].append(current_set['current_angle'])
                                    data['diff'].append(current_set['diff'])
                                    data['control'].append(current_set['control'])
                                    data['steering_direction'].append(current_set['steering_direction'])
                                    current_set = {}
                                    
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error processing bot log {log_file}: {e}")
            return None

    def _parse_laptime_log(self, log_file):
        """Parse the laptime log file to get completion times from timestamps."""
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                bot1_time = None
                bot2_time = None
                
                for line in lines:
                    if 'Player finish time:' in line:
                        time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                        if time_match:
                            bot1_time = self._convert_game_time(time_match.group(1))
                    elif 'Bot finish time:' in line:
                        time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                        if time_match:
                            bot2_time = self._convert_game_time(time_match.group(1))
                
                return bot1_time, bot2_time
        except Exception as e:
            print(f"Error parsing laptime log {log_file}: {e}")
            return None, None

    def _create_comprehensive_plots(self, all_bot1_data, all_bot2_data, completion_times, lag_values):
        """Create comprehensive analysis plots with confidence intervals."""
        # Create DataFrame for analysis
        df = pd.DataFrame({
            'Lag': lag_values,
            'Bot1_Time': [t[0] for t in completion_times],
            'Bot2_Time': [t[1] for t in completion_times],
            'Bot1_Steering_Effort': [data['control'].abs().mean() for data in all_bot1_data],
            'Bot2_Steering_Effort': [data['control'].abs().mean() for data in all_bot2_data],
            'Bot1_Angle_Error': [(data['target_angle'] - data['current_angle']).abs().mean() for data in all_bot1_data],
            'Bot2_Angle_Error': [(data['target_angle'] - data['current_angle']).abs().mean() for data in all_bot2_data]
        })
        
        # Group by lag and calculate statistics
        grouped = df.groupby('Lag').agg({
            'Bot1_Time': ['mean', 'std', 'count'],
            'Bot2_Time': ['mean', 'std', 'count'],
            'Bot1_Steering_Effort': ['mean', 'std', 'count'],
            'Bot2_Steering_Effort': ['mean', 'std', 'count'],
            'Bot1_Angle_Error': ['mean', 'std', 'count'],
            'Bot2_Angle_Error': ['mean', 'std', 'count']
        })

        # Calculate 95% confidence intervals
        def calculate_ci(std, count):
            return 1.96 * (std / np.sqrt(count))

        # Plot 1: Laptime vs Lag with trendline
        plt.figure(figsize=(12, 6))
        
        # Bot 1
        bot1_ci = calculate_ci(grouped['Bot1_Time']['std'], grouped['Bot1_Time']['count'])
        plt.errorbar(grouped.index, grouped['Bot1_Time']['mean'], 
                    yerr=bot1_ci, fmt='bo-', capsize=5, label='Bot 1 Time')
        z1 = np.polyfit(grouped.index, grouped['Bot1_Time']['mean'], 1)
        p1 = np.poly1d(z1)
        plt.plot(grouped.index, p1(grouped.index), 'b--', label='Bot 1 Trend')
        
        # Bot 2
        bot2_ci = calculate_ci(grouped['Bot2_Time']['std'], grouped['Bot2_Time']['count'])
        plt.errorbar(grouped.index, grouped['Bot2_Time']['mean'], 
                    yerr=bot2_ci, fmt='ro-', capsize=5, label='Bot 2 Time')
        z2 = np.polyfit(grouped.index, grouped['Bot2_Time']['mean'], 1)
        p2 = np.poly1d(z2)
        plt.plot(grouped.index, p2(grouped.index), 'r--', label='Bot 2 Trend')
        
        plt.title('Lap Time vs Lag')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Lap Time (seconds)')
        plt.legend()
        plt.grid(True)
        plt.savefig(self.analysis_dir / 'laptime_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Steering Effort vs Lag with trendline
        plt.figure(figsize=(12, 6))
        
        # Bot 1
        bot1_steering_ci = calculate_ci(grouped['Bot1_Steering_Effort']['std'], grouped['Bot1_Steering_Effort']['count'])
        plt.errorbar(grouped.index, grouped['Bot1_Steering_Effort']['mean'], 
                    yerr=bot1_steering_ci, fmt='go-', capsize=5, label='Bot 1 Steering Effort')
        z1 = np.polyfit(grouped.index, grouped['Bot1_Steering_Effort']['mean'], 1)
        p1 = np.poly1d(z1)
        plt.plot(grouped.index, p1(grouped.index), 'g--', label='Bot 1 Trend')
        
        # Bot 2
        bot2_steering_ci = calculate_ci(grouped['Bot2_Steering_Effort']['std'], grouped['Bot2_Steering_Effort']['count'])
        plt.errorbar(grouped.index, grouped['Bot2_Steering_Effort']['mean'], 
                    yerr=bot2_steering_ci, fmt='mo-', capsize=5, label='Bot 2 Steering Effort')
        z2 = np.polyfit(grouped.index, grouped['Bot2_Steering_Effort']['mean'], 1)
        p2 = np.poly1d(z2)
        plt.plot(grouped.index, p2(grouped.index), 'm--', label='Bot 2 Trend')
        
        plt.title('Steering Effort vs Lag')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Average Steering Effort')
        plt.legend()
        plt.grid(True)
        plt.savefig(self.analysis_dir / 'steering_effort_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 3: Angle Error vs Lag
        plt.figure(figsize=(12, 6))
        
        # Bot 1
        bot1_angle_ci = calculate_ci(grouped['Bot1_Angle_Error']['std'], grouped['Bot1_Angle_Error']['count'])
        plt.errorbar(grouped.index, grouped['Bot1_Angle_Error']['mean'], 
                    yerr=bot1_angle_ci, fmt='co-', capsize=5, label='Bot 1 Angle Error')
        
        # Bot 2
        bot2_angle_ci = calculate_ci(grouped['Bot2_Angle_Error']['std'], grouped['Bot2_Angle_Error']['count'])
        plt.errorbar(grouped.index, grouped['Bot2_Angle_Error']['mean'], 
                    yerr=bot2_angle_ci, fmt='yo-', capsize=5, label='Bot 2 Angle Error')
        
        plt.title('Angle Error vs Lag')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Average Angle Error (degrees)')
        plt.legend()
        plt.grid(True)
        plt.savefig(self.analysis_dir / 'angle_error_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save statistics
        grouped.to_csv(self.analysis_dir / 'summary_statistics.csv')

    def _convert_game_time(self, time_str):
        """Convert game time string (MM:SS.ms) to seconds."""
        minutes, seconds = time_str.split(':')
        return float(minutes) * 60 + float(seconds)
    
    def create_overall_analysis(self):
        """Create overall analysis combining all lag conditions."""
        # Load all individual statistics
        all_stats = []
        for lag in self.lag_values:
            stats_file = self.analysis_dir / f'assist_1.0' / f'lag_{lag}' / 'summary_statistics.csv'
            if stats_file.exists():
                stats = pd.read_csv(stats_file)
                stats['Lag'] = lag
                all_stats.append(stats)
        
        if not all_stats:
            print("No statistics found for overall analysis")
            return
        
        # Combine all statistics
        combined_stats = pd.concat(all_stats)
        
        # Create overall analysis directory
        overall_dir = self.analysis_dir / 'overall'
        overall_dir.mkdir(parents=True, exist_ok=True)
        
        # Plot 1: Overall Laptime vs Lag with trendline
        plt.figure(figsize=(12, 6))
        for bot in ['Bot1', 'Bot2']:
            grouped = combined_stats.groupby('Lag')[f'{bot}_Time'].agg(['mean', 'std'])
            
            # Plot data points
            plt.errorbar(grouped.index, grouped['mean'], 
                        yerr=grouped['std'], fmt='o-', capsize=5, label=f'{bot} Time')
            
            # Add trendline
            z = np.polyfit(grouped.index, grouped['mean'], 1)
            p = np.poly1d(z)
            plt.plot(grouped.index, p(grouped.index), "--", label=f'{bot} Trend')
            
        plt.title('Overall Lap Time vs Lag')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Lap Time (seconds)')
        plt.legend()
        plt.grid(True)
        plt.savefig(overall_dir / 'overall_laptime_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save combined statistics
        combined_stats.to_csv(overall_dir / 'overall_statistics.csv', index=False)

    def analyze_collisions(self):
        """Analyze collision events per lag value."""
        collision_counts = {}
        lag_values = sorted([int(f.name.split('_')[1]) for f in self.logs_dir.glob('lag_*')])

        for lag in lag_values:
            lag_dir = self.logs_dir / f'lag_{lag}'
            if not lag_dir.exists():
                print(f"Warning: Directory for lag {lag}ms does not exist: {lag_dir}")
                continue

            collision_count = 0
            for run_num in range(1, 31):  # Assuming max 30 runs per lag
                log_file = lag_dir / f'logfile_{run_num}.log'
                if not log_file.exists():
                    print(f"Warning: Log file for lag {lag}ms, run {run_num} does not exist: {log_file}")
                    continue

                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    prev_line_was_collision = False
                    for line in lines:
                        if 'Collision event' in line:
                            if not prev_line_was_collision:
                                collision_count += 1
                                prev_line_was_collision = True
                        else:
                            prev_line_was_collision = False

            collision_counts[lag] = collision_count
            print(f"Lag {lag}ms: {collision_count} collision events")

        return collision_counts

    def plot_collisions(self):
        """Plot the number of collision events per lag value."""
        collision_counts = self.analyze_collisions()
        if not collision_counts:
            print("Error: No collision events found.")
            return

        lags = sorted(collision_counts.keys())
        counts = [collision_counts[lag] for lag in lags]

        overall_dir = self.analysis_dir / 'overall'
        overall_dir.mkdir(parents=True, exist_ok=True)

        # Verify analysis_dir path
        print(f"Saving plot to: {overall_dir / 'collisions_vs_lag.png'}")

        try:
            plt.figure(figsize=(12, 6))
            plt.bar(lags, counts, color='red', alpha=0.7)
            plt.title('Collision Events vs Lag')
            plt.xlabel('Lag (ms)')
            plt.ylabel('Number of Collision Events')
            plt.grid(True)
            plt.savefig(overall_dir / 'collisions_vs_lag.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("Plot saved successfully.")
        except Exception as e:
            print(f"Error saving plot: {e}")

# def run_bot_analysis():
#     """Run the complete bot vs bot analysis pipeline."""
#     start_time = time.time()
    
#     print("=== Starting Bot vs Bot Analysis ===")
    
#     analyzer = BotAnalyzer()
#     print("\n1. Setting up directory structure...")
#     analyzer.setup_directories()
    
#     print("\n2. Analyzing individual assistance levels...")
#     analyzer.analyze_all_lag_conditions()

#     print("\n2.5. plotting collisions...")
#     analyzer.plot_collisions()
    
#     print("\n3. Creating overall analysis...")
#     analyzer.create_overall_analysis()
    
#     end_time = time.time()
#     duration = end_time - start_time
    
#     print("\n=== Analysis Complete ===")
#     print(f"Total processing time: {duration:.2f} seconds")


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
import time
import sys

class LagAnalyzer(BotAnalyzer):
    def __init__(self, base_dir='DustRacing2D-master'):
        super().__init__(base_dir)
        self.analysis_dir = self.base_dir / 'data analysis' / 'lag_analysis'
        
    def analyze_all_lag_conditions(self):
        """Analyze all lag conditions with focus on lag impact."""
        super().analyze_all_lag_conditions()
        
        # Additional lag-specific analysis
        self._create_lag_impact_plots()

    def _create_lag_impact_plots(self):
        """Create plots specifically analyzing lag impact."""
        try:
            # Load previously saved statistics
            stats = pd.read_csv(self.analysis_dir / 'summary_statistics.csv', index_col=0)
            
            # Ensure data is properly aggregated
            if not isinstance(stats, pd.DataFrame):
                print("Error: Statistics data is not in the expected format")
                return
            
            # Plot 1: Lag Impact on Performance with trendline
            plt.figure(figsize=(12, 6))
            metrics = {
                'Bot1_Time': ('bo-', 'Bot 1 Time'),
                'Bot1_Control': ('go-', 'Bot 1 Control'),
                'Bot1_Angle_Error': ('co-', 'Bot 1 Angle Error')
            }
            
            for metric, (style, label) in metrics.items():
                # Check if metric exists in stats
                if metric not in stats.columns:
                    print(f"Warning: Metric {metric} not found in statistics")
                    continue
                
                # Get mean and std values
                mean_values = stats[metric].mean() if isinstance(stats[metric], pd.DataFrame) else stats[metric]
                std_values = stats[metric].std() if isinstance(stats[metric], pd.DataFrame) else 0
                
                # Ensure mean_values and std_values are numeric
                if not pd.api.types.is_numeric_dtype(mean_values):
                    print(f"Warning: Metric {metric} contains non-numeric data")
                    continue
                
                # Plot data points
                plt.errorbar(stats.index, mean_values, 
                            yerr=std_values, fmt=style, capsize=5, label=label)
                
                # Add trendline
                z = np.polyfit(stats.index, mean_values, 1)
                p = np.poly1d(z)
                plt.plot(stats.index, p(stats.index), "--", label=f'{label} Trend')
                
            plt.title('Lag Impact on Bot Performance')
            plt.xlabel('Lag (ms)')
            plt.ylabel('Performance Metrics')
            plt.legend()
            plt.grid(True)
            plt.savefig(self.analysis_dir / 'lag_impact.png', dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"Error creating lag impact plots: {e}")

def run_analysis():
    """Run the complete analysis pipeline."""
    start_time = time.time()
    
    print("=== Starting Analysis ===")
    
    bot_analyzer = BotAnalyzer()
    print("\n1. Analyzing bot performance...")
    bot_analyzer.analyze_all_lag_conditions()

    print("\n.1.5 analyze collisions...")
    bot_analyzer.plot_collisions()
    
    lag_analyzer = LagAnalyzer()
    print("\n2. Analyzing lag impact...")
    lag_analyzer.analyze_all_lag_conditions()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n=== Analysis Complete ===")
    print(f"Total processing time: {duration:.2f} seconds")

if __name__ == "__main__":
    try:
        run_analysis()
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred during analysis: {e}")
        sys.exit(1)

