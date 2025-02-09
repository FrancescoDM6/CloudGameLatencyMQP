# run_analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
import time
import sys
import seaborn as sns

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
        """Process a car log file and return structured data."""
        data = {
            'time': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': [],
            'steering_direction': []
        }
        
        try:
            with open(log_file, "r") as file:
                current_time = None
                current_set = {}
                
                for line in file:
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        
                        # Extract different types of data based on line content
                        if 'Continuous angles:' in line:
                            angles_match = re.search(r'target=([\d\.-]+), current=([\d\.-]+)', line)
                            if angles_match:
                                current_set['target_angle'] = float(angles_match.group(1))
                                current_set['current_angle'] = float(angles_match.group(2))
                                
                        elif 'Track assistance:' in line:
                            assist_match = re.search(r'angle=[\d\.-]+, cur=[\d\.-]+, diff=([\d\.-]+), control=([\d\.-]+)', line)
                            if assist_match:
                                current_set['diff'] = float(assist_match.group(1))
                                current_set['control'] = float(assist_match.group(2))
                                
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
            print(f"Error processing car log {log_file}: {e}")
            return None


    def _process_bot_log(self, log_file):
        """Process a bot log file and extract relevant data."""
        data = {
            'time': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': [],
            'car_x': [],
            'car_y': [],
            'target_x': [],
            'target_y': []
        }
        
        current_time = None
        current_set = {}  # Temporary storage for a single timestep's data
        
        print(f"Processing log file: {log_file}")
        
        with open(log_file, 'r') as f:
            for line in f:
                # Extract game time
                time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                if time_match:
                    if current_time is not None and len(current_set) == 8:  # All fields collected
                        data['time'].append(current_time)
                        data['target_angle'].append(current_set['target_angle'])
                        data['current_angle'].append(current_set['current_angle'])
                        data['diff'].append(current_set['diff'])
                        data['control'].append(current_set['control'])
                        data['car_x'].append(current_set['car_x'])
                        data['car_y'].append(current_set['car_y'])
                        data['target_x'].append(current_set['target_x'])
                        data['target_y'].append(current_set['target_y'])
                        current_set = {}  # Reset for the next timestep
                    
                    current_time = self._convert_game_time(time_match.group(1))
                    print(f"Found time: {current_time}")
                
                # Extract target position
                if 'steerControl: targetNode X:' in line:
                    x_match = re.search(r'targetNode X:\s*([\d\.-]+)', line)
                    if x_match:
                        current_set['target_x'] = float(x_match.group(1))
                        print(f"Found target_x: {current_set['target_x']}")
                
                if 'steerControl: targetNode Y:' in line:
                    y_match = re.search(r'targetNode Y:\s*([\d\.-]+)', line)
                    if y_match:
                        current_set['target_y'] = float(y_match.group(1))
                        print(f"Found target_y: {current_set['target_y']}")
                
                # Extract car position
                if 'steerControl: car Location i:' in line:
                    i_match = re.search(r'car Location i:\s*([\d\.-]+)', line)
                    if i_match:
                        current_set['car_x'] = float(i_match.group(1))
                        print(f"Found car_x: {current_set['car_x']}")
                
                if 'steerControl: car Location j:' in line:
                    j_match = re.search(r'car Location j:\s*([\d\.-]+)', line)
                    if j_match:
                        current_set['car_y'] = float(j_match.group(1))
                        print(f"Found car_y: {current_set['car_y']}")
                
                # Extract angles
                if 'Continuous angles:' in line:
                    angles_match = re.search(r'target=([\d\.-]+), current=([\d\.-]+)', line)
                    if angles_match:
                        current_set['target_angle'] = float(angles_match.group(1))
                        current_set['current_angle'] = float(angles_match.group(2))
                        print(f"Found angles: target={current_set['target_angle']}, current={current_set['current_angle']}")
                
                # Extract control values
                if 'steerControl: angle=' in line:
                    control_match = re.search(r'angle=([\d\.-]+), cur=([\d\.-]+), diff=([\d\.-]+), control=([\d\.-]+)', line)
                    if control_match:
                        current_set['diff'] = float(control_match.group(3))
                        current_set['control'] = float(control_match.group(4))
                        print(f"Found control: diff={current_set['diff']}, control={current_set['control']}")
        
        # Add the last timestep's data if it's complete
        if current_time is not None and len(current_set) == 8:
            data['time'].append(current_time)
            data['target_angle'].append(current_set['target_angle'])
            data['current_angle'].append(current_set['current_angle'])
            data['diff'].append(current_set['diff'])
            data['control'].append(current_set['control'])
            data['car_x'].append(current_set['car_x'])
            data['car_y'].append(current_set['car_y'])
            data['target_x'].append(current_set['target_x'])
            data['target_y'].append(current_set['target_y'])
        
        print(f"Processed {len(data['time'])} timesteps from {log_file}")
        return pd.DataFrame(data)

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
        self.logs_dir = self.base_dir / 'logs'
        self.analysis_dir = self.base_dir / 'data analysis' / 'bot_vs_bot'
        # self.assist_values = ['0.5', '1.0', '1.5']
        self.assist_values = ['1.0']
        self.lag_values = list(range(0, 151, 10))  # 0 to 150 ms
        self.run_count = 16

    def setup_directories(self):
        """Create all necessary directories for bot vs bot analysis."""
        print("\nSetting up directory structure...")
        
        # Create analysis directories for each assistance level
        for assist in self.assist_values:
            assist_dir = self.analysis_dir / f'assist_{assist}'
            for subdir in ['Individual', 'Comparisons', 'Summary']:
                (assist_dir / subdir).mkdir(parents=True, exist_ok=True)
                print(f"Created {subdir} directory for assist_{assist}")
        
        # Create overall analysis directory
        (self.analysis_dir / 'overall').mkdir(parents=True, exist_ok=True)
        print("Created overall analysis directory")

    def analyze_assist_level(self, assist_value):
        all_bot1_data = []
        all_bot2_data = []
        
        for run_num, lag in zip(range(0, self.run_count), self.lag_values):
            bot1_log = self.logs_dir / f'assist_{assist_value}' / f'cardata_{run_num}.log'
            bot2_log = self.logs_dir / f'assist_{assist_value}' / f'botdata_{run_num}.log'
            
            bot1_data = self._process_player_log(bot1_log)
            bot2_data = self._process_bot_log(bot2_log)
            
            if bot1_data is not None and bot2_data is not None:
                all_bot1_data.append(bot1_data)
                all_bot2_data.append(bot2_data)
        
        if all_bot1_data:
            # Create summary plots
            summary_dir = self.analysis_dir / f'assist_{assist_value}' / 'Summary'
            self._create_summary_plots(all_bot1_data, all_bot2_data, summary_dir)
            print(f"Created summary plots for assistance level {assist_value}")

    def analyze_bot_run(self, assist_value, run_number):
        """Analyze a single bot vs bot run."""
        print(f"\nAnalyzing bot vs bot run #{run_number} with assist value {assist_value}")
        
        bot1_log = self.logs_dir / f'assist_{assist_value}' / f'cardata_{run_number}.log'
        bot2_log = self.logs_dir / f'assist_{assist_value}' / f'botdata_{run_number}.log'
        
        try:
            # Process logs using appropriate methods for each file type
            bot1_data = self._process_player_log(bot1_log)  # Use player log format for cardata
            bot2_data = self._process_bot_log(bot2_log)     # Use bot log format for botdata
            
            if bot1_data is not None and bot2_data is not None:
                # Create plots for individual run
                output_dir = self.analysis_dir / f'assist_{assist_value}' / 'Individual'
                self._create_bot_plots(bot1_data, bot2_data, output_dir, run_number)
                
                comp_dir = self.analysis_dir / f'assist_{assist_value}' / 'Comparisons'
                self._create_comparison_plots(bot1_data, bot2_data, comp_dir, run_number)
                
                return bot1_data, bot2_data
            
        except Exception as e:
            print(f"Error processing run: {e}")
            return None, None

    def create_overall_analysis(self):
        """Create comprehensive comparison plots across all assistance levels."""
        print("\nCreating overall analysis")
        overall_dir = self.analysis_dir / 'overall'
        
        # Collect all data
        all_data = {assist: {'bot1': [], 'bot2': []} for assist in self.assist_values}
        
        for assist in self.assist_values:
            assist_dir = self.logs_dir / f'assist_{assist}'
            if not assist_dir.exists():
                continue
                
            cardata_files = list(assist_dir.glob('cardata_*.log'))
            run_numbers = sorted([int(f.stem.split('_')[1]) for f in cardata_files])
            
            for run in run_numbers:
                try:
                    bot1_data = self._process_player_log(assist_dir / f'cardata_{run}.log')
                    bot2_data = self._process_bot_log(assist_dir / f'botdata_{run}.log')
                    
                    if bot1_data is not None and bot2_data is not None:
                        all_data[assist]['bot1'].append(bot1_data)
                        all_data[assist]['bot2'].append(bot2_data)
                except Exception as e:
                    print(f"Error processing assist {assist} run {run}: {e}")
        
        self._create_overall_analysis_plots(all_data, overall_dir)
        print("Created overall analysis plots")

    def _process_player_log(self, log_file):
        """Process a car log file using the player format."""
        data = {
            'time': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': [],
            'steering_direction': []
        }
        
        try:
            with open(log_file, "r") as file:
                current_time = None
                current_set = {}
                
                for line in file:
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        
                        # Extract different types of data based on line content
                        if 'Continuous angles:' in line:
                            angles_match = re.search(r'target=([\d\.-]+), current=([\d\.-]+)', line)
                            if angles_match:
                                current_set['target_angle'] = float(angles_match.group(1))
                                current_set['current_angle'] = float(angles_match.group(2))
                                
                        elif 'Track assistance:' in line:
                            assist_match = re.search(r'angle=[\d\.-]+, cur=[\d\.-]+, diff=([\d\.-]+), control=([\d\.-]+)', line)
                            if assist_match:
                                current_set['diff'] = float(assist_match.group(1))
                                current_set['control'] = float(assist_match.group(2))
                                
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
            print(f"Error processing car log {log_file}: {e}")
            return None

    def _process_bot_log(self, log_file):
        """Process a bot log file."""
        data = {
            'time': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': [],
            'car_x': [],
            'car_y': [],
            'target_x': [],
            'target_y': []
        }
        
        try:
            with open(log_file, "r") as file:
                lines = file.readlines()
                
                current_time = None
                current_set = {}
                
                for line in lines:
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        if current_time is not None and len(current_set) == 8:
                            data['time'].append(current_time)
                            for key in current_set:
                                data[key].append(current_set[key])
                            current_set = {}
                        
                        current_time = self._convert_game_time(time_match.group(1))
                    
                    # Extract positions and angles
                    if 'targetNode X:' in line:
                        x_match = re.search(r'targetNode X:\s*([\d\.-]+)', line)
                        if x_match:
                            current_set['target_x'] = float(x_match.group(1))
                    
                    elif 'targetNode Y:' in line:
                        y_match = re.search(r'targetNode Y:\s*([\d\.-]+)', line)
                        if y_match:
                            current_set['target_y'] = float(y_match.group(1))
                    
                    elif 'car Location i:' in line:
                        x_match = re.search(r'car Location i:\s*([\d\.-]+)', line)
                        if x_match:
                            current_set['car_x'] = float(x_match.group(1))
                    
                    elif 'car Location j:' in line:
                        y_match = re.search(r'car Location j:\s*([\d\.-]+)', line)
                        if y_match:
                            current_set['car_y'] = float(y_match.group(1))
                    
                    elif 'Continuous angles:' in line:
                        angles_match = re.search(r'target=([\d\.-]+), current=([\d\.-]+)', line)
                        if angles_match:
                            current_set['target_angle'] = float(angles_match.group(1))
                            current_set['current_angle'] = float(angles_match.group(2))
                    
                    elif 'steerControl: angle=' in line:
                        control_match = re.search(r'diff=([\d\.-]+), control=([\d\.-]+)', line)
                        if control_match:
                            current_set['diff'] = float(control_match.group(1))
                            current_set['control'] = float(control_match.group(2))
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error processing bot log {log_file}: {e}")
            return None

    def _create_bot_plots(self, bot1_data, bot2_data, output_dir, run_number):
        """Create individual performance plots for both bots."""
        if bot1_data is None or bot2_data is None:
            print(f"No data available for run {run_number}")
            return
            
        plt.style.use('default')
        
        # Plot 1: Control Values
        plt.figure(figsize=(12, 8))
        plt.plot(bot1_data['time'], bot1_data['control'], 'b-', label='Bot 1 Control', linewidth=2)
        plt.plot(bot2_data['time'], bot2_data['control'], 'r-', label='Bot 2 Control', linewidth=2)
        plt.title(f'Control Values Comparison - Run {run_number}')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Control Value')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / f'run_{run_number}_control.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Angle Differences
        plt.figure(figsize=(12, 8))
        plt.plot(bot1_data['time'], bot1_data['diff'], 'b-', label='Bot 1 Angle Diff', alpha=0.7)
        plt.plot(bot2_data['time'], bot2_data['diff'], 'r-', label='Bot 2 Angle Diff', alpha=0.7)
        plt.title(f'Angle Differences - Run {run_number}')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Angle Difference')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / f'run_{run_number}_angles.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 3: Bot2 Trajectory (since only Bot2 has position data)
        if all(col in bot2_data.columns for col in ['car_x', 'car_y', 'target_x', 'target_y']):
            plt.figure(figsize=(12, 8))
            plt.plot(bot2_data['car_x'], bot2_data['car_y'], 'r-', label='Bot 2 Path', linewidth=2)
            plt.plot(bot2_data['target_x'], bot2_data['target_y'], 'k--', label='Target Path', alpha=0.7)
            plt.title(f'Bot 2 Trajectory - Run {run_number}')
            plt.xlabel('X Position')
            plt.ylabel('Y Position')
            plt.legend()
            plt.grid(True)
            plt.axis('equal')
            plt.savefig(output_dir / f'run_{run_number}_trajectory.png', dpi=300, bbox_inches='tight')
            plt.close()

    def _create_comparison_plots(self, bot1_data, bot2_data, output_dir, run_number):
        """Create comparison plots between both bots."""
        if bot1_data is None or bot2_data is None:
            print(f"Missing data for comparison in run {run_number}")
            return
            
        plt.style.use('default')
        
        # Plot 1: Target vs Current Angles
        plt.figure(figsize=(12, 8))
        plt.subplot(2, 1, 1)
        plt.plot(bot1_data['time'], bot1_data['target_angle'], 'b-', label='Bot 1 Target', alpha=0.7)
        plt.plot(bot1_data['time'], bot1_data['current_angle'], 'b--', label='Bot 1 Current', alpha=0.7)
        plt.title(f'Angle Tracking - Bot 1 - Run {run_number}')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Angle')
        plt.legend()
        plt.grid(True)
        
        plt.subplot(2, 1, 2)
        plt.plot(bot2_data['time'], bot2_data['target_angle'], 'r-', label='Bot 2 Target', alpha=0.7)
        plt.plot(bot2_data['time'], bot2_data['current_angle'], 'r--', label='Bot 2 Current', alpha=0.7)
        plt.title('Angle Tracking - Bot 2')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Angle')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(output_dir / f'run_{run_number}_angle_tracking.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Control Comparison
        plt.figure(figsize=(12, 6))
        plt.plot(bot1_data['time'], bot1_data['control'], 'b-', label='Bot 1', alpha=0.7)
        plt.plot(bot2_data['time'], bot2_data['control'], 'r-', label='Bot 2', alpha=0.7)
        plt.title(f'Control Input Comparison - Run {run_number}')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Control Value')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / f'run_{run_number}_control_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 3: Steering Direction Distribution (Bot 1 only)
        if 'steering_direction' in bot1_data.columns:
            plt.figure(figsize=(8, 6))
            direction_counts = bot1_data['steering_direction'].value_counts()
            plt.bar(direction_counts.index, direction_counts.values)
            plt.title(f'Bot 1 Steering Direction Distribution - Run {run_number}')
            plt.xlabel('Direction')
            plt.ylabel('Count')
            plt.savefig(output_dir / f'run_{run_number}_steering_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()

    def _create_summary_plots(self, bot1_data_list, bot2_data_list, output_dir):
        """Create summary plots for a set of runs."""
        if not bot1_data_list or not bot2_data_list:
            print("No data available for summary plots")
            return
            
        # Calculate metrics
        bot1_completion = [data['time'].max() for data in bot1_data_list]
        bot2_completion = [data['time'].max() for data in bot2_data_list]
        
        bot1_avg_control = [data['control'].abs().mean() for data in bot1_data_list]
        bot2_avg_control = [data['control'].abs().mean() for data in bot2_data_list]
        
        # Calculate angle errors
        bot1_angle_errors = [
            (data['target_angle'] - data['current_angle']).abs().mean() 
            for data in bot1_data_list
        ]
        bot2_angle_errors = [
            (data['target_angle'] - data['current_angle']).abs().mean() 
            for data in bot2_data_list
        ]
        
        plt.style.use('default')
        
        # Get lag values for this assistance level
        run_count = len(bot1_data_list)
        assist_lag_values = self.lag_values[:run_count]
        
        # Plot 1: Completion Times vs Lag
        plt.figure(figsize=(10, 6))
        plt.plot(assist_lag_values, bot1_completion, 'bo-', label='Bot 1')
        plt.plot(assist_lag_values, bot2_completion, 'ro-', label='Bot 2')
        plt.title('Completion Times vs Lag')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Time (seconds)')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / 'completion_times_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Average Control Values vs Lag
        plt.figure(figsize=(10, 6))
        plt.plot(assist_lag_values, bot1_avg_control, 'bo-', label='Bot 1')
        plt.plot(assist_lag_values, bot2_avg_control, 'ro-', label='Bot 2')
        plt.title('Average Control Input vs Lag')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Average Control Value')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / 'control_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 3: Average Angle Error vs Lag
        plt.figure(figsize=(10, 6))
        plt.plot(assist_lag_values, bot1_angle_errors, 'bo-', label='Bot 1')
        plt.plot(assist_lag_values, bot2_angle_errors, 'ro-', label='Bot 2')
        plt.title('Average Angle Error vs Lag')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Average Angle Error (degrees)')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / 'angle_error_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save summary statistics
        summary_stats = pd.DataFrame({
            'Lag': assist_lag_values,
            'Bot1_Completion_Time': bot1_completion,
            'Bot2_Completion_Time': bot2_completion,
            'Bot1_Avg_Control': bot1_avg_control,
            'Bot2_Avg_Control': bot2_avg_control,
            'Bot1_Avg_Angle_Error': bot1_angle_errors,
            'Bot2_Avg_Angle_Error': bot2_angle_errors
        })
        summary_stats.to_csv(output_dir / 'summary_statistics.csv', index=False)

    def _create_overall_analysis_plots(self, all_data, output_dir):
        metrics = {
            'assist': [],
            'lag': [],
            'bot': [],
            'completion_time': [],
            'avg_control': [],
            'avg_angle_error': []
        }
        
        for assist in self.assist_values:
            run_count = len(all_data[assist]['bot1'])
            assist_lag_values = self.lag_values[:run_count]

            # for bot1_data, bot2_data in zip(all_data['1.0']['bot1'], all_data['1.0']['bot2']):
            #     if bot1_data is not None and bot2_data is not None:
            #         metrics['assist'].append('1.0')
            #         metrics['lag'].append(self.lag_values[len(metrics['lag'])])
            #         metrics['completion_time'].append(max(bot1_data['time'].max(), bot2_data['time'].max()))
            #         metrics['avg_control'].append(bot1_data['control'].abs().mean())
            #         metrics['avg_angle_error'].append(
            #             (bot1_data['target_angle'] - bot1_data['current_angle']).abs().mean()
            #         )
            
            for bot_type in ['bot1', 'bot2']:
                for data, lag in zip(all_data[assist][bot_type], assist_lag_values):
                    if data is not None and not data.empty:
                        metrics['assist'].append(assist)
                        metrics['lag'].append(lag)
                        metrics['bot'].append(bot_type)
                        metrics['completion_time'].append(data['time'].max())
                        metrics['avg_control'].append(data['control'].abs().mean())
                        metrics['avg_angle_error'].append(
                            (data['target_angle'] - data['current_angle']).abs().mean()
                        )
        
        df = pd.DataFrame(metrics)
        
        # Completion Times vs Lag (trend)
        plt.figure(figsize=(15, 8))
        for assist in self.assist_values:
            assist_data = df[df['assist'] == assist]
            for bot in ['bot1', 'bot2']:
                bot_data = assist_data[assist_data['bot'] == bot]
                label = f'Assist {assist} - {"Bot 1" if bot == "bot1" else "Bot 2"}'
                plt.plot(bot_data['lag'], bot_data['completion_time'], 'o-', label=label, markersize=4)
        
        # Create heatmap
        plt.figure(figsize=(10, 6))
        df = pd.DataFrame(metrics)
        pivot = df.pivot_table(index='lag', values=['completion_time', 'avg_control', 'avg_angle_error'])
        sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlGnBu")
        plt.title('Performance Metrics Heatmap')
        plt.savefig(output_dir / 'metrics_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()

        plt.title('Completion Times vs Lag by Assistance Level')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Completion Time (seconds)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_dir / 'overall_completion_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Average Control vs Lag (trend)
        plt.figure(figsize=(15, 8))
        for assist in self.assist_values:
            assist_data = df[df['assist'] == assist]
            for bot in ['bot1', 'bot2']:
                bot_data = assist_data[assist_data['bot'] == bot]
                label = f'Assist {assist} - {"Bot 1" if bot == "bot1" else "Bot 2"}'
                plt.plot(bot_data['lag'], bot_data['avg_control'], 'o-', label=label, markersize=4)
        
        plt.title('Average Control Values vs Lag by Assistance Level')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Average Control Value')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_dir / 'overall_control_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Angle Error vs Lag (trend)
        plt.figure(figsize=(15, 8))
        for assist in self.assist_values:
            assist_data = df[df['assist'] == assist]
            for bot in ['bot1', 'bot2']:
                bot_data = assist_data[assist_data['bot'] == bot]
                label = f'Assist {assist} - {"Bot 1" if bot == "bot1" else "Bot 2"}'
                plt.plot(bot_data['lag'], bot_data['avg_angle_error'], 'o-', label=label, markersize=4)
        
        plt.title('Average Angle Error vs Lag by Assistance Level')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Average Angle Error (degrees)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_dir / 'overall_angle_error_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Boxplots for distributions
        lag_ranges = [(0, 100), (100, 200), (200, 300)]
        positions = range(len(lag_ranges))
        legend_elements = [
            plt.Line2D([0], [0], color=f'C{i*2+j}', label=f'Assist {assist} - {"Bot 1" if j==0 else "Bot 2"}')
            for i, assist in enumerate(self.assist_values)
            for j in range(2)
        ]
        
        # Completion Time Boxplots
        plt.figure(figsize=(15, 8))
        for i, assist in enumerate(self.assist_values):
            assist_data = df[df['assist'] == assist]
            for j, bot in enumerate(['bot1', 'bot2']):
                bot_data = assist_data[assist_data['bot'] == bot]
                
                metrics = []
                for low, high in lag_ranges:
                    range_data = bot_data[
                        (bot_data['lag'] >= low) & 
                        (bot_data['lag'] < high)
                    ]['completion_time']
                    metrics.append(range_data)
                
                pos = [p + (i*0.25) + (j*0.1) for p in positions]
                plt.boxplot(metrics, positions=pos, widths=0.1,
                          patch_artist=True,
                          boxprops=dict(facecolor=f'C{i*2 + j}', alpha=0.5))
        
        plt.xticks([p + 0.25 for p in positions], 
                  ['0-100ms', '100-200ms', '200-300ms'])
        plt.title('Completion Time Distribution by Lag Range')
        plt.xlabel('Lag Range')
        plt.ylabel('Completion Time (seconds)')
        plt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.savefig(output_dir / 'completion_time_boxplots.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Control Value Boxplots
        plt.figure(figsize=(15, 8))
        for i, assist in enumerate(self.assist_values):
            assist_data = df[df['assist'] == assist]
            for j, bot in enumerate(['bot1', 'bot2']):
                bot_data = assist_data[assist_data['bot'] == bot]
                
                metrics = []
                for low, high in lag_ranges:
                    range_data = bot_data[
                        (bot_data['lag'] >= low) & 
                        (bot_data['lag'] < high)
                    ]['avg_control']
                    metrics.append(range_data)
                
                pos = [p + (i*0.25) + (j*0.1) for p in positions]
                plt.boxplot(metrics, positions=pos, widths=0.1,
                          patch_artist=True,
                          boxprops=dict(facecolor=f'C{i*2 + j}', alpha=0.5))
        
        plt.xticks([p + 0.25 for p in positions], 
                  ['0-100ms', '100-200ms', '200-300ms'])
        plt.title('Control Value Distribution by Lag Range')
        plt.xlabel('Lag Range')
        plt.ylabel('Average Control Value')
        plt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.savefig(output_dir / 'control_value_boxplots.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Angle Error Boxplots
        plt.figure(figsize=(15, 8))
        for i, assist in enumerate(self.assist_values):
            assist_data = df[df['assist'] == assist]
            for j, bot in enumerate(['bot1', 'bot2']):
                bot_data = assist_data[assist_data['bot'] == bot]
                
                metrics = []
                for low, high in lag_ranges:
                    range_data = bot_data[
                        (bot_data['lag'] >= low) & 
                        (bot_data['lag'] < high)
                    ]['avg_angle_error']
                    metrics.append(range_data)
                
                pos = [p + (i*0.25) + (j*0.1) for p in positions]
                plt.boxplot(metrics, positions=pos, widths=0.1,
                          patch_artist=True,
                          boxprops=dict(facecolor=f'C{i*2 + j}', alpha=0.5))
        
        plt.xticks([p + 0.25 for p in positions], 
                  ['0-100ms', '100-200ms', '200-300ms'])
        plt.title('Angle Error Distribution by Lag Range')
        plt.xlabel('Lag Range')
        plt.ylabel('Average Angle Error (degrees)')
        plt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.savefig(output_dir / 'angle_error_boxplots.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Relationship Plots (colored scatter plots)
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(df['avg_control'], df['completion_time'], 
                            c=df['lag'], cmap='viridis',
                            s=100, alpha=0.6)
        plt.colorbar(scatter, label='Lag (ms)')
        plt.title('Control vs Completion Time (colored by lag)')
        plt.xlabel('Average Control Value')
        plt.ylabel('Completion Time (seconds)')
        plt.grid(True)
        plt.savefig(output_dir / 'control_vs_completion_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(df['avg_angle_error'], df['completion_time'], 
                            c=df['lag'], cmap='viridis',
                            s=100, alpha=0.6)
        plt.colorbar(scatter, label='Lag (ms)')
        plt.title('Angle Error vs Completion Time (colored by lag)')
        plt.xlabel('Average Angle Error (degrees)')
        plt.ylabel('Completion Time (seconds)')
        plt.grid(True)
        plt.savefig(output_dir / 'angle_error_vs_completion_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save overall statistics with lag information
        stats = df.groupby(['assist', 'bot', 'lag']).agg({
            'completion_time': ['mean', 'std'],
            'avg_control': ['mean', 'std'],
            'avg_angle_error': ['mean', 'std']
        }).reset_index()
        
        # Flatten column names
        stats.columns = [
            'assist', 'bot', 'lag',
            'completion_time_mean', 'completion_time_std',
            'control_mean', 'control_std',
            'angle_error_mean', 'angle_error_std'
        ]
        
        stats.to_csv(output_dir / 'overall_lag_statistics.csv', index=False)
        
    def _convert_game_time(self, time_str):
        """Convert game time string (MM:SS.ms) to seconds."""
        minutes, seconds = time_str.split(':')
        return float(minutes) * 60 + float(seconds)
    



def run_bot_analysis():
    """Run the complete bot vs bot analysis pipeline."""
    start_time = time.time()
    
    print("=== Starting Bot vs Bot Analysis ===")
    
    analyzer = BotAnalyzer()
    print("\n1. Setting up directory structure...")
    analyzer.setup_directories()
    
    print("\n2. Analyzing individual assistance levels...")
    for assist in analyzer.assist_values:
        analyzer.analyze_assist_level(assist)
    
    print("\n3. Creating overall analysis...")
    analyzer.create_overall_analysis()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n=== Analysis Complete ===")
    print(f"Total processing time: {duration:.2f} seconds")


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
import time
import sys

class LagAnalyzer:
    def __init__(self, base_dir='DustRacing2D-master'):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / 'logs'
        self.analysis_dir = self.base_dir / 'data analysis' / 'lag_analysis'
        # self.assist_values = ['1.0', '0.5', '1.5']  # In order of runs
        # self.lag_values = list(range(0, 301, 10))  # 0 to 300 by steps of 10
        
        # # Map assistance levels to run number ranges
        # self.run_ranges = {
        #     '1.0': range(1, 32),      # First 31 runs
        #     '0.5': range(32, 63),     # Next 31 runs
        #     '1.5': range(63, 94)      # Last 31 runs
        # }

        self.assist_values = ['1.0']
        self.lag_values = list(range(0, 151, 10))
        self.run_count = 16
        
    def setup_directories(self):
        """Create all necessary directories for lag analysis."""
        print("\nSetting up directory structure...")
        
        # Create analysis directories for each assistance level
        for assist in self.assist_values:
            assist_dir = self.analysis_dir / f'assist_{assist}'
            # Create summary directory for lag analysis
            (assist_dir / 'Summary').mkdir(parents=True, exist_ok=True)
            print(f"Created Summary directory for assist_{assist}")
        
        # Create overall analysis directory
        (self.analysis_dir / 'overall').mkdir(parents=True, exist_ok=True)
        print("Created overall analysis directory")

    def analyze_assist_level(self, assist_value):
        lag_data = {
            'lag': [],
            'completion_time': [],
            'avg_control': [],
            'avg_angle_error': []
        }
        
        for run_num, lag in zip(range(0, self.run_count), self.lag_values):
            bot1_log = self.logs_dir / f'assist_{assist_value}' / f'cardata_{run_num}.log'
            bot2_log = self.logs_dir / f'assist_{assist_value}' / f'botdata_{run_num}.log'
            
            try:
                bot1_data = self._process_player_log(bot1_log)
                bot2_data = self._process_bot_log(bot2_log)
                
                if bot1_data is not None and bot2_data is not None:
                    lag_data['lag'].append(lag)
                    lag_data['completion_time'].append(max(bot1_data['time'].max(), bot2_data['time'].max()))
                    lag_data['avg_control'].append(bot1_data['control'].abs().mean())
                    lag_data['avg_angle_error'].append(
                        (bot1_data['target_angle'] - bot1_data['current_angle']).abs().mean()
                    )
            
            except Exception as e:
                print(f"Error processing lag {lag}ms: {e}")
        
        if lag_data['lag']:
            summary_dir = self.analysis_dir / f'assist_{assist_value}' / 'Summary'
            self._create_lag_summary_plots(lag_data, summary_dir, assist_value)

    def _create_lag_summary_plots(self, lag_data, output_dir, assist_value):
        """Create summary plots showing the effect of lag."""
        plt.style.use('default')
        
        # Convert data to DataFrame for easier plotting
        df = pd.DataFrame(lag_data)

        # Create heatmap
        plt.figure(figsize=(10, 6))
        pivot = df.pivot_table(index='lag', values=['completion_time', 'avg_control', 'avg_angle_error'])
        sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlGnBu")
        plt.title('Lag Analysis Heatmap')
        plt.savefig(output_dir / 'lag_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 1: Completion Time vs Lag
        plt.figure(figsize=(12, 6))
        plt.plot(df['lag'], df['completion_time'], 'b-o')
        plt.title(f'Completion Time vs Lag (Assist={assist_value})')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Completion Time (seconds)')
        plt.grid(True)
        plt.savefig(output_dir / 'completion_time_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Control Effort vs Lag
        plt.figure(figsize=(12, 6))
        plt.plot(df['lag'], df['avg_control'], 'r-o')
        plt.title(f'Average Control Effort vs Lag (Assist={assist_value})')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Average Control Value')
        plt.grid(True)
        plt.savefig(output_dir / 'control_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 3: Angle Error vs Lag
        plt.figure(figsize=(12, 6))
        plt.plot(df['lag'], df['avg_angle_error'], 'b-o')
        plt.title(f'Angle Error vs Lag (Assist={assist_value})')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Angle Error (degrees)')
        plt.grid(True)
        plt.savefig(output_dir / 'angle_error_vs_lag.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save metrics to CSV
        df.to_csv(output_dir / 'lag_metrics.csv', index=False)

    def create_overall_analysis(self):
        """Create comprehensive comparison plots across all assistance levels."""
        print("\nCreating overall lag analysis")
        overall_dir = self.analysis_dir / 'overall'
        
        # Collect data for all assistance levels
        all_data = []
        
        for assist in self.assist_values:
            metrics_file = self.analysis_dir / f'assist_{assist}' / 'Summary' / 'lag_metrics.csv'
            if metrics_file.exists():
                df = pd.read_csv(metrics_file)
                df['assist'] = assist
                all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            self._create_overall_lag_plots(combined_df, overall_dir)
            print("Created overall lag analysis plots")

    def _create_overall_lag_plots(self, df, output_dir):
        """Create overall analysis plots comparing lag effects across assistance levels."""
        plt.style.use('default')
        
        # Plot 1: Completion Time vs Lag (all assistance levels)
        plt.figure(figsize=(12, 6))
        for assist in self.assist_values:
            assist_data = df[df['assist'] == assist]
            plt.plot(assist_data['lag'], assist_data['completion_time'], 'o-', 
                    label=f'Assist {assist}')
        plt.title('Completion Time vs Lag by Assistance Level')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Completion Time (seconds)')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / 'overall_completion_time.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Control Effort vs Lag (all assistance levels)
        plt.figure(figsize=(12, 6))
        for assist in self.assist_values:
            assist_data = df[df['assist'] == assist]
            plt.plot(assist_data['lag'], assist_data['avg_control'], 'o-',
                    label=f'Assist {assist}')
        plt.title('Average Control Effort vs Lag by Assistance Level')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Average Control Value')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / 'overall_control.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 3: Average Angle Error vs Lag (all assistance levels)
        plt.figure(figsize=(12, 6))
        for assist in self.assist_values:
            assist_data = df[df['assist'] == assist]
            plt.plot(assist_data['lag'], assist_data['avg_angle_error'], 'o-',
                    label=f'Assist {assist}')
        plt.title('Average Angle Error vs Lag by Assistance Level')
        plt.xlabel('Lag (ms)')
        plt.ylabel('Average Angle Error (degrees)')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / 'overall_angle_error.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save combined metrics
        df.to_csv(output_dir / 'overall_lag_metrics.csv', index=False)

    # Include the _process_player_log and _process_bot_log methods from BotAnalyzer
    def _process_player_log(self, log_file):
        """Process a car log file using the player format."""
        data = {
            'time': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': [],
            'steering_direction': []
        }
        
        try:
            with open(log_file, "r") as file:
                current_time = None
                current_set = {}
                
                for line in file:
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        
                        # Extract different types of data based on line content
                        if 'Continuous angles:' in line:
                            angles_match = re.search(r'target=([\d\.-]+), current=([\d\.-]+)', line)
                            if angles_match:
                                current_set['target_angle'] = float(angles_match.group(1))
                                current_set['current_angle'] = float(angles_match.group(2))
                                
                        elif 'Track assistance:' in line:
                            assist_match = re.search(r'angle=[\d\.-]+, cur=[\d\.-]+, diff=([\d\.-]+), control=([\d\.-]+)', line)
                            if assist_match:
                                current_set['diff'] = float(assist_match.group(1))
                                current_set['control'] = float(assist_match.group(2))
                                
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
            print(f"Error processing car log {log_file}: {e}")
            return None

    def _process_bot_log(self, log_file):
        """Process a bot log file."""
        data = {
            'time': [],
            'target_angle': [],
            'current_angle': [],
            'diff': [],
            'control': [],
            'car_x': [],
            'car_y': [],
            'target_x': [],
            'target_y': []
        }
        
        try:
            with open(log_file, "r") as file:
                lines = file.readlines()
                
                current_time = None
                current_set = {}
                
                for line in lines:
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        if current_time is not None and len(current_set) == 8:
                            data['time'].append(current_time)
                            for key in current_set:
                                data[key].append(current_set[key])
                            current_set = {}
                        
                        current_time = self._convert_game_time(time_match.group(1))
                    
                    # Extract positions and angles
                    if 'targetNode X:' in line:
                        x_match = re.search(r'targetNode X:\s*([\d\.-]+)', line)
                        if x_match:
                            current_set['target_x'] = float(x_match.group(1))
                    
                    elif 'targetNode Y:' in line:
                        y_match = re.search(r'targetNode Y:\s*([\d\.-]+)', line)
                        if y_match:
                            current_set['target_y'] = float(y_match.group(1))
                    
                    elif 'car Location i:' in line:
                        x_match = re.search(r'car Location i:\s*([\d\.-]+)', line)
                        if x_match:
                            current_set['car_x'] = float(x_match.group(1))
                    
                    elif 'car Location j:' in line:
                        y_match = re.search(r'car Location j:\s*([\d\.-]+)', line)
                        if y_match:
                            current_set['car_y'] = float(y_match.group(1))
                    
                    elif 'Continuous angles:' in line:
                        angles_match = re.search(r'target=([\d\.-]+), current=([\d\.-]+)', line)
                        if angles_match:
                            current_set['target_angle'] = float(angles_match.group(1))
                            current_set['current_angle'] = float(angles_match.group(2))
                    
                    elif 'steerControl: angle=' in line:
                        control_match = re.search(r'diff=([\d\.-]+), control=([\d\.-]+)', line)
                        if control_match:
                            current_set['diff'] = float(control_match.group(1))
                            current_set['control'] = float(control_match.group(2))
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error processing bot log {log_file}: {e}")
            return None

    def _convert_game_time(self, time_str):
        """Convert game time string (MM:SS.ms) to seconds."""
        minutes, seconds = time_str.split(':')
        return float(minutes) * 60 + float(seconds)



def run_lag_analysis():
    """Run the complete lag analysis pipeline."""
    start_time = time.time()
    
    print("=== Starting Lag Analysis ===")
    
    analyzer = LagAnalyzer()
    print("\n1. Setting up directory structure...")
    analyzer.setup_directories()
    
    print("\n2. Analyzing individual assistance levels...")
    for assist in analyzer.assist_values:
        analyzer.analyze_assist_level(assist)
    
    print("\n3. Creating overall analysis...")
    analyzer.create_overall_analysis()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n=== Analysis Complete ===")
    print(f"Total processing time: {duration:.2f} seconds")


# if __name__ == "__main__":
#     try:
#         run_lag_analysis()
#     except KeyboardInterrupt:
#         print("\nAnalysis interrupted by user")
#         sys.exit(1)
#     except Exception as e:
#         print(f"\nAn error occurred during analysis: {e}")
#         sys.exit(1)


if __name__ == "__main__":
    try:
        run_bot_analysis()
        run_lag_analysis()
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred during analysis: {e}")
        sys.exit(1)

