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
        self.lag_conditions = ['0 Lag', '200 Lag']
        
        # Updated run mappings
        self.run_mappings = {
            'J': {
                '0.0 Control Assistance': (1, 5),   # runs 6-10
                '0.2 Control Assistance': (11, 15),   # runs 11-15
                '1.0 Control Assistance': (6, 10),    # runs 1-5
                
            },
            'F': {
                '0.0 Control Assistance': (1, 5),     # runs 1-5
                '0.2 Control Assistance': (11, 15),    # runs 11-15
                '1.0 Control Assistance': (6, 10),    # runs 6-10
                
            },
            'M': {
                '0.0 Control Assistance': (1, 5),     # runs 1-5
                '0.2 Control Assistance': (11, 15),    # runs 11-15
                '1.0 Control Assistance': (6, 10),    # runs 6-10
                
            }
        }
        
    def _set_plot_style(self):
        """Set consistent plot styling."""
        plt.style.use('default')
        plt.rcParams['axes.grid'] = False  # Remove grid
        plt.rcParams['axes.formatter.use_locale'] = True  # For proper number formatting
        # Ensure no grids appear in any plot
        plt.rcParams['grid.alpha'] = 0
        plt.rcParams['grid.linewidth'] = 0
        
    def _convert_game_time(self, time_str):
        """Convert game time string to seconds."""
        minutes, seconds = time_str.split(':')
        return float(minutes) * 60 + float(seconds)
    
    def _find_global_time_range(self):
        """Find global min and max completion times across all conditions."""
        min_time = float('inf')
        max_time = float('-inf')
        
        for player in self.players:
            for lag_condition in ['0 Lag', '200 Lag']:
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

        self._create_comprehensive_control_analysis(all_data, overall_dir)
        self._create_comprehensive_steering_analysis(all_data, overall_dir)
        
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
                    # print(f"Processing line: {line.strip()}")  # Debug print
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        game_time = self._convert_game_time(time_match.group(1))
                        
                        if 'Bot finish time:' in line:
                            # print(f"Found bot time: {game_time}")  # Debug print
                            bot_time = game_time
                        elif 'Player finish time:' in line:
                            # print(f"Found player time: {game_time}")  # Debug print
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

    # def _create_overall_analysis_plots(self, all_data, output_dir):
    #     """Create overall analysis plots comparing all players and conditions."""
    #     self._set_plot_style()
        
    #     # Previous code remains the same...
        
    #     # Calculate and plot win percentages
    #     win_df = self._create_win_percentage_plots(output_dir)
        
    #     # Save overall statistics including win percentages
    #     stats = df.sort_values(['player', 'condition', 'lag']).round(2)
    #     stats.to_csv(output_dir / 'overall_statistics.csv', index=False)
    #     win_df.to_csv(output_dir / 'win_percentages.csv', index=False)

    def _calculate_win_percentages(self):
        """Calculate win percentage from individual run comparisons."""
        win_data = {
            'player': [],
            'condition': [],
            'lag': [],
            'win_percentage': []
        }
        
        for player in self.players:
            for lag_condition in ['0 Lag', '200 Lag']:
                for control_type in ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance']:
                    start_run, end_run = self.run_mappings[player][control_type]
                    
                    wins = 0
                    total_valid_runs = 0
                    
                    for run in range(start_run, end_run + 1):
                        lap_log = self.logs_dir / player / lag_condition / f'laptime_{run}.log'
                        bot_time, player_time = self._process_lap_time(lap_log)
                        
                        if bot_time is not None and player_time is not None:
                            if player_time <= bot_time:  # Player wins if they finish before or at same time as bot
                                wins += 1
                            total_valid_runs += 1
                    
                    if total_valid_runs > 0:
                        win_pct = (wins / total_valid_runs) * 100
                    else:
                        win_pct = 0
                        
                    win_data['player'].append(player)
                    win_data['condition'].append(control_type)
                    win_data['lag'].append(lag_condition)
                    win_data['win_percentage'].append(win_pct)
        
        return pd.DataFrame(win_data)

    def _create_win_percentage_plots(self, output_dir):
        """Create win percentage visualization plots."""
        x_positions = {
            '0.0 Control Assistance': 0.0,
            '0.2 Control Assistance': 0.2,
            '1.0 Control Assistance': 1.0
        }
        
        x_labels = ['0.0', '0.2', '1.0']
        player_markers = {
            'F': 'o',     # circle
            'J': 's',     # square
            'M': '^'      # triangle
        }
        
        win_df = self._calculate_win_percentages()
        
        # Combined plot for all players - now stacked vertically
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), height_ratios=[1, 1])
        
        # Top subplot - 0 Lag
        lag_data = win_df[win_df['lag'] == '0 Lag']
        for player in reversed(self.players):
            player_data = lag_data[lag_data['player'] == player]
            if not player_data.empty:
                player_data = player_data.sort_values(by='condition',
                    key=lambda x: [x_positions[val] for val in x])
                x_vals = [x_positions[c] for c in player_data['condition']]
                
                ax1.plot(x_vals, player_data['win_percentage'],
                        marker=player_markers[player],
                        linestyle='none',
                        label=f'Player {player}',
                        markersize=10,
                        zorder=3)
        
        ax1.set_xlabel('Steering Assistance')
        ax1.set_ylabel('Win Percentage')
        ax1.set_title('Win Percentage by Player - 0 Lag')
        ax1.set_ylim(-2, 105)
        ax1.set_xlim(-0.1, 1.1)
        ax1.set_xticks([0.0, 0.2, 1.0])
        ax1.set_xticklabels(x_labels)
        ax1.legend()
        ax1.grid(True, zorder=1)
        
        # Bottom subplot - 200 Lag
        lag_data = win_df[win_df['lag'] == '200 Lag']
        for player in reversed(self.players):
            player_data = lag_data[lag_data['player'] == player]
            if not player_data.empty:
                player_data = player_data.sort_values(by='condition',
                    key=lambda x: [x_positions[val] for val in x])
                x_vals = [x_positions[c] for c in player_data['condition']]
                
                ax2.plot(x_vals, player_data['win_percentage'],
                        marker=player_markers[player],
                        linestyle='none',
                        label=f'Player {player}',
                        markersize=10,
                        zorder=3)
        
        ax2.set_xlabel('Steering Assistance')
        ax2.set_ylabel('Win Percentage')
        ax2.set_title('Win Percentage by Player - 200 Lag')
        ax2.set_ylim(-2, 105)
        ax2.set_xlim(-0.1, 1.1)
        ax2.set_xticks([0.0, 0.2, 1.0])
        ax2.set_xticklabels(x_labels)
        ax2.legend()
        ax2.grid(True, zorder=1)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'win_percentage_combined.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Individual plots remain the same since they're already using the desired format
        for player in self.players:
            plt.figure(figsize=(15, 6))
            player_data = win_df[win_df['player'] == player]
            
            for i, lag_condition in enumerate(['0 Lag', '200 Lag']):
                plt.subplot(1, 2, i+1)
                lag_data = player_data[player_data['lag'] == lag_condition]
                lag_data = lag_data.sort_values(by='condition',
                    key=lambda x: [x_positions[val] for val in x])
                
                x_vals = [x_positions[c] for c in lag_data['condition']]
                plt.plot(x_vals, lag_data['win_percentage'], 
                        marker=player_markers[player],
                        linestyle='none',
                        markersize=10,
                        zorder=3)
                
                plt.xlabel('Steering Assistance')
                plt.ylabel('Win Percentage')
                plt.title(f'{lag_condition}')
                plt.ylim(-2, 105)
                plt.xlim(-0.1, 1.1)
                plt.xticks([0.0, 0.2, 1.0], x_labels)
                plt.grid(True, zorder=1)
            
            plt.suptitle(f'Win Percentage - Player {player}')
            plt.tight_layout()
            plt.savefig(output_dir / f'win_percentage_player_{player}.png',
                    dpi=300, bbox_inches='tight')
            plt.close()
        
        return win_df
    

    def _process_off_track_data(self, log_file):
        """Process a log file to determine time spent off track."""
        try:
            off_track_periods = []
            current_period_start = None
            last_time = None
            
            with open(log_file, "r") as file:
                for line in file:
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    off_track_match = re.search(r'isOffTrack check: left=(\d), right=(\d)', line)
                    
                    if time_match and off_track_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        left = int(off_track_match.group(1))
                        right = int(off_track_match.group(2))
                        
                        is_off_track = (left == 1 or right == 1)
                        
                        # Track first off-track moment
                        if is_off_track and current_period_start is None:
                            current_period_start = current_time
                        # Track return to track
                        elif not is_off_track and current_period_start is not None:
                            off_track_periods.append((current_period_start, current_time))
                            current_period_start = None
                        
                        last_time = current_time
            
            # Handle case where run ends while off track
            if current_period_start is not None:
                off_track_periods.append((current_period_start, last_time))
            
            # Calculate total time off track
            total_off_track_time = sum(end - start for start, end in off_track_periods)
            
            return {
                'total_time': last_time,
                'off_track_time': total_off_track_time,
                'off_track_percentage': (total_off_track_time / last_time * 100) if last_time else 0,
                'off_track_periods': off_track_periods
            }
            
        except Exception as e:
            print(f"Error processing log file {log_file}: {e}")
            return None

    def _calculate_off_track_stats(self):
        """Calculate off track statistics for all runs."""
        off_track_data = {
            'player': [],
            'condition': [],
            'lag': [],
            'off_track_percentage': []
        }
        
        for player in self.players:
            for lag_condition in ['0 Lag', '200 Lag']:
                for control_type in ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance']:
                    start_run, end_run = self.run_mappings[player][control_type]
                    
                    run_percentages = []
                    for run in range(start_run, end_run + 1):
                        log_file = self.logs_dir / player / lag_condition / f'logfile_{run}.log'
                        stats = self._process_off_track_data(log_file)
                        
                        if stats is not None:
                            run_percentages.append(stats['off_track_percentage'])
                    
                    if run_percentages:
                        off_track_data['player'].append(player)
                        off_track_data['condition'].append(control_type)
                        off_track_data['lag'].append(lag_condition)
                        off_track_data['off_track_percentage'].append(np.mean(run_percentages))
        
        return pd.DataFrame(off_track_data)

    def _create_off_track_plots(self, off_track_df, output_dir):
        """Create visualizations for off track analysis."""
        x_positions = {
            '0.0 Control Assistance': 0.0,
            '0.2 Control Assistance': 0.2,
            '1.0 Control Assistance': 1.0
        }
        x_labels = ['0.0', '0.2', '1.0']
        
        # Find global min and max for consistent scaling across both plots
        min_pct = off_track_df['off_track_percentage'].min()
        max_pct = off_track_df['off_track_percentage'].max()
        range_pad = (max_pct - min_pct) * 0.1
        y_min = max(0, min_pct - range_pad)
        y_max = max_pct + range_pad
        
        # Create stacked plots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), height_ratios=[1, 1])
        
        # Top subplot - 0 Lag
        lag_data = off_track_df[off_track_df['lag'] == '0 Lag']
        for player in self.players:
            player_data = lag_data[lag_data['player'] == player]
            player_data = player_data.sort_values(by='condition',
                key=lambda x: [x_positions[val] for val in x])
            
            x_vals = [x_positions[c] for c in player_data['condition']]
            ax1.plot(x_vals, player_data['off_track_percentage'], 
                    'o', markersize=10, label=f'Player {player}',
                    zorder=3)
        
        ax1.set_xlabel('Steering Assistance')
        ax1.set_ylabel('Time Off Track (%)')
        ax1.set_title('Off Track Time - 0 Lag')
        ax1.set_ylim(y_min, y_max)
        ax1.set_xlim(-0.1, 1.1)
        ax1.set_xticks([0.0, 0.2, 1.0])
        ax1.set_xticklabels(x_labels)
        ax1.legend()
        ax1.grid(True, alpha=0.3, zorder=1)
        
        # Bottom subplot - 200 Lag
        lag_data = off_track_df[off_track_df['lag'] == '200 Lag']
        for player in self.players:
            player_data = lag_data[lag_data['player'] == player]
            player_data = player_data.sort_values(by='condition',
                key=lambda x: [x_positions[val] for val in x])
            
            x_vals = [x_positions[c] for c in player_data['condition']]
            ax2.plot(x_vals, player_data['off_track_percentage'], 
                    'o', markersize=10, label=f'Player {player}',
                    zorder=3)
        
        ax2.set_xlabel('Steering Assistance')
        ax2.set_ylabel('Time Off Track (%)')
        ax2.set_title('Off Track Time - 200 Lag')
        ax2.set_ylim(y_min, y_max)
        ax2.set_xlim(-0.1, 1.1)
        ax2.set_xticks([0.0, 0.2, 1.0])
        ax2.set_xticklabels(x_labels)
        ax2.legend()
        ax2.grid(True, alpha=0.3, zorder=1)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'off_track_percentage.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_lag_performance_plots(self, df, output_dir, min_time, max_time):
        """Create lag performance plots."""
        # Performance vs Lag by Player and Bot
        plt.figure(figsize=(12, 8))
        
        # Plot player data
        for player in self.players:
            player_data = df[(df['player'] == player) & (df['type'] == 'player')]
            lag_means = []
            lag_stds = []
            for lag in ['0 Lag', '200 Lag']:
                lag_subset = player_data[player_data['lag'] == lag]
                lag_means.append(lag_subset['mean_time'].mean())
                lag_stds.append(np.sqrt((lag_subset['std_time']**2).mean()))
            
            plt.errorbar(['0 Lag', '200 Lag'], lag_means, yerr=lag_stds,
                        fmt='o-', label=f'Player {player}',
                        capsize=5, markersize=8, zorder=3)
        
        # Add bot data to same plot
        bot_data = df[df['type'] == 'bot']
        lag_means = []
        lag_stds = []
        for lag in ['0 Lag', '200 Lag']:
            lag_subset = bot_data[bot_data['lag'] == lag]
            lag_means.append(lag_subset['mean_time'].mean())
            lag_stds.append(np.sqrt((lag_subset['std_time']**2).mean()))
        
        plt.errorbar(['0 Lag', '200 Lag'], lag_means, yerr=lag_stds,
                    fmt='s-', label='Bot', color='red',
                    capsize=5, markersize=8, zorder=3)
        
        plt.xlabel('Lag Condition')
        plt.ylabel('Average Completion Time (seconds)')
        plt.title('Performance vs Lag')
        plt.legend()
        plt.grid(True, alpha=0.3, zorder=1)
        plt.ylim(min_time, max_time)
        
        plt.savefig(output_dir / 'lag_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Performance vs Lag by Control Condition and Bot
        plt.figure(figsize=(12, 8))
        conditions = df['condition'].unique()
        markers = ['o', 's', '^']
        
        # Plot player data by control condition
        for i, condition in enumerate(conditions):
            player_data = df[(df['type'] == 'player') & (df['condition'] == condition)]
            lag_means = []
            lag_stds = []
            for lag in ['0 Lag', '200 Lag']:
                lag_subset = player_data[player_data['lag'] == lag]
                lag_means.append(lag_subset['mean_time'].mean())
                lag_stds.append(np.sqrt((lag_subset['std_time']**2).mean()))
            
            plt.errorbar(['0 Lag', '200 Lag'], lag_means, yerr=lag_stds,
                        fmt=f'{markers[i]}-', label=f'Control {condition}',
                        capsize=5, markersize=8, zorder=3)
        
        # Add bot data
        bot_data = df[df['type'] == 'bot']
        lag_means = []
        lag_stds = []
        for lag in ['0 Lag', '200 Lag']:
            lag_subset = bot_data[bot_data['lag'] == lag]
            lag_means.append(lag_subset['mean_time'].mean())
            lag_stds.append(np.sqrt((lag_subset['std_time']**2).mean()))
        
        plt.errorbar(['0 Lag', '200 Lag'], lag_means, yerr=lag_stds,
                    fmt='d-', label='Bot', color='red',
                    capsize=5, markersize=8, zorder=3)
        
        plt.xlabel('Lag Condition')
        plt.ylabel('Average Completion Time (seconds)')
        plt.title('Performance vs Lag by Control Level')
        plt.legend()
        plt.grid(True, alpha=0.3, zorder=1)
        plt.ylim(min_time, max_time)
        
        plt.savefig(output_dir / 'lag_performance_by_control.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_overall_analysis_plots(self, all_data, output_dir):
        """Create overall analysis plots comparing all players and conditions."""
        self._set_plot_style()
        
        # Get global time range
        min_time, max_time = self._find_global_time_range()
        print(f"\nGlobal time range: {min_time} to {max_time}")

        # Prepare data for plotting
        stats_data = []
        
        # Process both player and bot data
        for data_type in ['player', 'bot']:
            for player in all_data[data_type]:
                for lag_condition in ['0 Lag', '200 Lag']:
                    for control_type in ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance']:
                        times = []
                        start_run, end_run = self.run_mappings[player][control_type]

                        print(f"\nProcessing {data_type} {player} {lag_condition} {control_type}")
                        print(f"Runs {start_run} to {end_run}")
                        
                        for run in range(start_run, end_run + 1):
                            lap_log = self.logs_dir / player / lag_condition / f'laptime_{run}.log'
                            bot_time, player_time = self._process_lap_time(lap_log)
                            time_to_use = bot_time if data_type == 'bot' else player_time
                            if time_to_use is not None:
                                times.append(time_to_use)
                        
                        if times:
                            print(f"Found times: {times}")
                            stats_data.append({
                                'condition': control_type,
                                'player': player if data_type == 'player' else 'Bot',  # All bots combined
                                'mean_time': np.mean(times),
                                'std_time': np.std(times),
                                'type': data_type,
                                'lag': lag_condition
                            })
        
        df = pd.DataFrame(stats_data)
        print("\nFull DataFrame:")
        print(df)

        x_positions = {
            '0.0 Control Assistance': 0.0,
            '0.2 Control Assistance': 0.2,
            '1.0 Control Assistance': 1.0
        }
        
        # Define x-axis labels
        x_labels = ['0.0', '0.2', '1.0']
        
        for lag_condition in ['0 Lag', '200 Lag']:
            print(f"\nPlotting {lag_condition}")

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 12), height_ratios=[1, 1])
            conditions = sorted(df['condition'].unique(), key=lambda x: x_positions[x])

            lag_df = df[df['lag'] == lag_condition]
            print(f"\nFiltered DataFrame for {lag_condition}:")
            print(lag_df)
            
            # Plot player data in top subplot
            for i, player in enumerate(self.players):
                player_data = lag_df[(lag_df['player'] == player) & (lag_df['type'] == 'player')]
                if not player_data.empty:
                    # Ensure we have data for all conditions
                    means = []
                    stds = []
                    x_vals = []
                    
                    for condition in conditions:
                        condition_data = player_data[player_data['condition'] == condition]
                        if not condition_data.empty:
                            means.append(condition_data['mean_time'].mean())
                            stds.append(condition_data['std_time'].mean())
                            x_vals.append(x_positions[condition])
                    
                    if means:  # Only plot if we have data
                        ax1.errorbar(x_vals, means, yerr=stds,
                                   fmt='o', capsize=5,
                                   label=f'Player {player}')
                        
                    
            ax1.set_title(f'Player Completion Times - {lag_condition}')
            ax1.set_ylabel('Time (seconds)')
            ax1.legend()
            ax1.set_ylim(min_time, max_time)
            ax1.set_xlim(-0.1, 1.1)
            ax1.set_xticks([0.0, 0.2, 1.0])
            ax1.set_xticklabels(x_labels)
            ax1.set_xlabel('Steering Assistance')
            
            # Plot combined bot data in bottom subplot
            bot_data = lag_df[lag_df['type'] == 'bot']
            if not bot_data.empty:
                means = []
                stds = []
                x_vals = []
                
                for condition in conditions:
                    condition_data = bot_data[bot_data['condition'] == condition]
                    if not condition_data.empty:
                        means.append(condition_data['mean_time'].mean())
                        stds.append(condition_data['std_time'].mean())
                        x_vals.append(x_positions[condition])
                
                if means:  # Only plot if we have data
                    ax2.errorbar(x_vals, means, yerr=stds,
                               fmt='s', capsize=5,
                               label='Bot')
            
            ax2.set_title(f'Bot Completion Times - {lag_condition}')
            ax2.set_xlabel('Steering Assistance')
            ax2.set_ylabel('Time (seconds)')
            ax2.legend()
            ax2.set_ylim(min_time, max_time)
            ax2.set_xlim(-0.1, 1.1)
            ax2.set_xticks([0.0, 0.2, 1.0])
            ax2.set_xticklabels(x_labels)
            
            # Remove internal x-axis padding
            ax2.margins(x=0.1)  # Reduce horizontal margins
            
            # Adjust layout to be tighter
            plt.subplots_adjust(left=0.15, right=0.95)  # Reduce left and right margins
            plt.savefig(output_dir / f'overall_completion_times_{lag_condition.replace(" ", "_")}.png', 
                    dpi=300, bbox_inches='tight')
            plt.close()
        
        self._create_lag_performance_plots(df, output_dir, min_time, max_time)

        
        # Calculate and plot win percentages
        win_df = self._create_win_percentage_plots(output_dir)

        off_track_df = self._calculate_off_track_stats()
        self._create_off_track_plots(off_track_df, output_dir)
        off_track_df.to_csv(output_dir / 'off_track_statistics.csv', index=False)
        
        # Save overall statistics
        stats = df.sort_values(['player', 'condition', 'lag']).round(2)
        stats.to_csv(output_dir / 'overall_statistics.csv', index=False)
        win_df.to_csv(output_dir / 'win_percentages.csv', index=False)

    def _create_comprehensive_control_analysis(self, all_data, output_dir):
        """Create comprehensive control input analysis across all players."""
        # Structure for aggregated data
        aggregated_data = {
            player: {
                lag: {
                    control: {
                        'control_values': [],
                        'times': []
                    } for control in ['0.0 Control Assistance', '0.2 Control Assistance', '1.0 Control Assistance']
                } for lag in ['0 Lag', '200 Lag']
            } for player in self.players
        }
        
        # Aggregate data from all runs
        for player in self.players:
            for lag in ['0 Lag', '200 Lag']:
                for control in ['0.0 Control Assistance', '0.2 Control Assistance', '1.0 Control Assistance']:
                    start_run, end_run = self.run_mappings[player][control]
                    for run in range(start_run, end_run + 1):
                        try:
                            data = self._process_player_log(self.logs_dir / player / lag / f'cardata_{run}.log')
                            if data is not None and not data.empty:
                                aggregated_data[player][lag][control]['control_values'].extend(data['control'].tolist())
                                aggregated_data[player][lag][control]['times'].extend(data['time'].tolist())
                        except Exception as e:
                            print(f"Error processing run {run} for {player} {lag} {control}: {e}")
        
        # Define x-axis positions and labels
        x_positions = {
            '0.0 Control Assistance': 0.0,
            '0.2 Control Assistance': 0.2,
            '1.0 Control Assistance': 1.0
        }
        x_labels = ['0.0', '0.2', '1.0']
        
        # Find global min/max for y-axis
        all_means = []
        for player in self.players:
            for lag in ['0 Lag', '200 Lag']:
                for control in sorted(x_positions.keys()):
                    values = aggregated_data[player][lag][control]['control_values']
                    if values:
                        all_means.append(np.mean(np.abs(values)))
        
        y_min = min(all_means)
        y_max = max(all_means)
        range_pad = (y_max - y_min) * 0.1
        y_min = max(0, y_min - range_pad)
        y_max = y_max + range_pad
        
        # Create plot with both subplots sharing the same y-axis range
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), height_ratios=[1, 1])
        
        # Top subplot - 0 Lag
        for player in self.players:
            means = []
            stds = []
            x_vals = []
            
            for control in sorted(x_positions.keys()):
                values = aggregated_data[player]['0 Lag'][control]['control_values']
                if values:
                    means.append(np.mean(np.abs(values)))
                    stds.append(np.std(np.abs(values)) / np.sqrt(len(values)))
                    x_vals.append(x_positions[control])
            
            ax1.errorbar(x_vals, means, yerr=stds, 
                        fmt='o', label=f'Player {player}',
                        capsize=5, markersize=8, zorder=3)
        
        ax1.set_xlabel('Steering Assistance')
        ax1.set_ylabel('Average Control Input Magnitude')
        ax1.set_title('Control Input Analysis - 0 Lag')
        ax1.legend()
        ax1.grid(True, alpha=0.3, zorder=1)
        ax1.set_xticks([0.0, 0.2, 1.0])
        ax1.set_xticklabels(x_labels)
        ax1.set_ylim(y_min, y_max)
        ax1.set_xlim(-0.1, 1.1)
        
        # Bottom subplot - 200 Lag
        for player in self.players:
            means = []
            stds = []
            x_vals = []
            
            for control in sorted(x_positions.keys()):
                values = aggregated_data[player]['200 Lag'][control]['control_values']
                if values:
                    means.append(np.mean(np.abs(values)))
                    stds.append(np.std(np.abs(values)) / np.sqrt(len(values)))
                    x_vals.append(x_positions[control])
            
            ax2.errorbar(x_vals, means, yerr=stds, 
                        fmt='o', label=f'Player {player}',
                        capsize=5, markersize=8, zorder=3)
        
        ax2.set_xlabel('Steering Assistance')
        ax2.set_ylabel('Average Control Input Magnitude')
        ax2.set_title('Control Input Analysis - 200 Lag')
        ax2.legend()
        ax2.grid(True, alpha=0.3, zorder=1)
        ax2.set_xticks([0.0, 0.2, 1.0])
        ax2.set_xticklabels(x_labels)
        ax2.set_ylim(y_min, y_max)
        ax2.set_xlim(-0.1, 1.1)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'control_input_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_comprehensive_steering_analysis(self, all_data, output_dir):
        """Create comprehensive steering analysis across all players."""
        # Structure for aggregated data
        aggregated_data = {
            player: {
                lag: {
                    control: {
                        'target_angles': [],
                        'current_angles': [],
                        'angle_diffs': [],
                        'times': []
                    } for control in ['0.0 Control Assistance', '0.2 Control Assistance', '1.0 Control Assistance']
                } for lag in ['0 Lag', '200 Lag']
            } for player in self.players
        }
        
        # Aggregate data from all runs
        for player in self.players:
            for lag in ['0 Lag', '200 Lag']:
                for control in ['0.0 Control Assistance', '0.2 Control Assistance', '1.0 Control Assistance']:
                    start_run, end_run = self.run_mappings[player][control]
                    for run in range(start_run, end_run + 1):
                        try:
                            data = self._process_player_log(self.logs_dir / player / lag / f'cardata_{run}.log')
                            if data is not None and not data.empty:
                                agg_data = aggregated_data[player][lag][control]
                                agg_data['target_angles'].extend(data['target_angle'].tolist())
                                agg_data['current_angles'].extend(data['current_angle'].tolist())
                                agg_data['angle_diffs'].extend(data['diff'].tolist())
                                agg_data['times'].extend(data['time'].tolist())
                        except Exception as e:
                            print(f"Error processing run {run} for {player} {lag} {control}: {e}")
        
        x_positions = {
            '0.0 Control Assistance': 0.0,
            '0.2 Control Assistance': 0.2,
            '1.0 Control Assistance': 1.0
        }
        x_labels = ['0.0', '0.2', '1.0']
        
        # Find global min/max for y-axis
        all_means = []
        for player in self.players:
            for lag in ['0 Lag', '200 Lag']:
                for control in sorted(x_positions.keys()):
                    diffs = aggregated_data[player][lag][control]['angle_diffs']
                    if diffs:
                        all_means.append(np.mean(np.abs(diffs)))
        
        y_min = min(all_means)
        y_max = max(all_means)
        range_pad = (y_max - y_min) * 0.1
        y_min = max(0, y_min - range_pad)
        y_max = y_max + range_pad
        
        # Plot average angle difference - vertically stacked
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), height_ratios=[1, 1])
        
        # Top subplot - 0 Lag
        for player in self.players:
            means = []
            stds = []
            x_vals = []
            
            for control in sorted(x_positions.keys()):
                diffs = aggregated_data[player]['0 Lag'][control]['angle_diffs']
                if diffs:
                    means.append(np.mean(np.abs(diffs)))
                    stds.append(np.std(np.abs(diffs)) / np.sqrt(len(diffs)))
                    x_vals.append(x_positions[control])
            
            ax1.errorbar(x_vals, means, yerr=stds, 
                        fmt='o', label=f'Player {player}',
                        capsize=5, markersize=8, zorder=3)
        
        ax1.set_xlabel('Steering Assistance')
        ax1.set_ylabel('Average Angle Difference (degrees)')
        ax1.set_title('Steering Angle Difference Analysis - 0 Lag')
        ax1.legend()
        ax1.grid(True, alpha=0.3, zorder=1)
        ax1.set_xticks([0.0, 0.2, 1.0])
        ax1.set_xticklabels(x_labels)
        ax1.set_ylim(y_min, y_max)
        ax1.set_xlim(-0.1, 1.1)
        
        # Bottom subplot - 200 Lag
        for player in self.players:
            means = []
            stds = []
            x_vals = []
            
            for control in sorted(x_positions.keys()):
                diffs = aggregated_data[player]['200 Lag'][control]['angle_diffs']
                if diffs:
                    means.append(np.mean(np.abs(diffs)))
                    stds.append(np.std(np.abs(diffs)) / np.sqrt(len(diffs)))
                    x_vals.append(x_positions[control])
            
            ax2.errorbar(x_vals, means, yerr=stds, 
                        fmt='o', label=f'Player {player}',
                        capsize=5, markersize=8, zorder=3)
        
        ax2.set_xlabel('Steering Assistance')
        ax2.set_ylabel('Average Angle Difference (degrees)')
        ax2.set_title('Steering Angle Difference Analysis - 200 Lag')
        ax2.legend()
        ax2.grid(True, alpha=0.3, zorder=1)
        ax2.set_xticks([0.0, 0.2, 1.0])
        ax2.set_xticklabels(x_labels)
        ax2.set_ylim(y_min, y_max)
        ax2.set_xlim(-0.1, 1.1)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'steering_angle_difference.png', dpi=300, bbox_inches='tight')
        plt.close()

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
        
        # Create player-specific directories with lag conditions
        for player in self.players:
            for lag_condition in self.lag_conditions:
                for control_type in self.control_types:
                    if control_type != 'Bot':
                        for subdir in ['Player', 'Comparisons', 'Summary']:
                            dir_path = self.analysis_dir / 'players' / player / lag_condition / control_type / subdir
                            dir_path.mkdir(parents=True, exist_ok=True)
                            print(f"Created {subdir} directory for {player}/{lag_condition}/{control_type}")
        
        # Create single bot and overall directories without lag condition subdirectories
        (self.analysis_dir / 'bot').mkdir(parents=True, exist_ok=True)
        print("Created bot analysis directory")
        
        (self.analysis_dir / 'overall').mkdir(parents=True, exist_ok=True)
        print("Created overall analysis directory")

def run_complete_analysis():
    """Run the complete analysis pipeline."""
    start_time = time.time()
    
    print("=== Starting Complete Analysis ===")
    
    analyzer = DataAnalyzer()
    
    print("\n1. Setting up directory structure...")
    analyzer.setup_directories()
    
    print("\n2. Analyzing individual player runs...")
    for player in ['F', 'J', 'M']:
        for lag_condition in ['0 Lag', '200 Lag']:
            for control_type in ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance']:
                analyzer.analyze_player_set(player, lag_condition, control_type)
    
    print("\n3. Analyzing bot performance...")
    # Collect all bot data together instead of separating by lag condition
    bot_dir = analyzer.analysis_dir / 'bot'
    all_bot_data = []
    
    for lag_condition in ['0 Lag', '200 Lag']:
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
        print("Created bot analysis plots")
    
    print("\n4. Creating overall analysis...")
    # Collect all data for both lag conditions
    all_data = {
        'player': {player: {} for player in ['F', 'J', 'M']},
        'bot': {player: {} for player in ['F', 'J', 'M']}
    }
    
    for lag_condition in ['0 Lag', '200 Lag']:
        for player in ['F', 'J', 'M']:
            if lag_condition not in all_data['player'][player]:
                all_data['player'][player][lag_condition] = {}
                all_data['bot'][player][lag_condition] = {}
                
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
                    all_data['player'][player][lag_condition][control_type] = player_runs
                    all_data['bot'][player][lag_condition][control_type] = bot_runs
    
    # Create overall analysis plots with all data
    overall_dir = analyzer.analysis_dir / 'overall'
    analyzer._create_overall_analysis_plots(all_data, overall_dir)
    print("Created overall analysis plots")
    
    # Create the new comprehensive analyses
    analyzer._create_comprehensive_control_analysis(all_data, overall_dir)
    analyzer._create_comprehensive_steering_analysis(all_data, overall_dir)
    print("Created comprehensive analysis plots")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n=== Analysis Complete ===")
    print(f"Total processing time: {duration:.2f} seconds")

if __name__ == "__main__":
    import matplotlib
    print(matplotlib.__version__)

    try:
        run_complete_analysis()
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred during analysis: {e}")
        sys.exit(1)

