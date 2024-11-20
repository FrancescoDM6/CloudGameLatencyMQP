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
        
        # Only change is here - using cardata instead of playerdata in filename
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
                        # Only change is here - using cardata instead of playerdata
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
                    # Extract game time
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        current_time = self._convert_game_time(time_match.group(1))
                        
                        # Extract different types of data based on line content
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
                                
                                # If we have all data for this timestep, add it to our main data structure
                                if len(current_set) == 8:  # All values except time
                                    data['time'].append(current_time)
                                    data['target_x'].append(current_set['target_x'])
                                    data['target_y'].append(current_set['target_y'])
                                    data['car_x'].append(current_set['car_x'])
                                    data['car_y'].append(current_set['car_y'])
                                    data['target_angle'].append(current_set['target_angle'])
                                    data['current_angle'].append(current_set['current_angle'])
                                    data['diff'].append(current_set['diff'])
                                    data['control'].append(current_set['control'])
                                    current_set = {}
                                    
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error processing bot log {log_file}: {e}")
            return None

    def _create_player_plots(self, data, output_dir, run_number):
        """Create individual player performance plots."""
        pass

    def _create_comparison_plots(self, player_data, bot_data, output_dir, run_number):
        """Create comparison plots between player and bot."""
        pass

    def _create_summary_plots(self, player_data_list, bot_data_list, output_dir):
        """Create summary plots for a set of runs."""
        pass

    def _create_bot_analysis_plots(self, bot_data_list, output_dir):
        """Create comprehensive bot analysis plots."""
        pass

    def _create_overall_analysis_plots(self, all_data, output_dir):
        """Create overall analysis plots comparing all players and conditions."""
        pass

def run_complete_analysis():
    """Run the complete analysis pipeline."""
    start_time = time.time()
    
    print("=== Starting Complete Analysis ===")
    
    analyzer = DataAnalyzer()
    
    print("\n1. Setting up directory structure...")
    analyzer.setup_directories()
    
    print("\n2. Analyzing individual player runs...")
    for player in ['F', 'J', 'M']:
        for control_type in ['Full AI', 'Full Player', 'Mixed']:
            analyzer.analyze_player_set(player, control_type)
    
    print("\n3. Analyzing bot performance...")
    analyzer.analyze_bot_performance()
    
    print("\n4. Creating overall analysis...")
    analyzer.create_overall_analysis()
    
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