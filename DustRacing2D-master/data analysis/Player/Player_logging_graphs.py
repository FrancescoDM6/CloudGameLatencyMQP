# Player/Player_logging_graphs.py
import re
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

def convert_game_time(time_str):
    """Convert game time string to seconds."""
    minutes, seconds = time_str.split(':')
    return float(minutes) * 60 + float(seconds)

def plot_player_data(start_val, end_val, condition):
    """Create and save steering data plots for player data."""
    plt.style.use('default')
    
    for i in range(start_val, end_val):
        target_angle_vals = []  # renamed for clarity
        current_angle_vals = []
        diff_vals = []
        control_vals = []
        game_times = []
        
        file_name = f"DustRacing2D-master/logs/cardata_{i}.log"
        print(f"Processing {file_name}")
        
        try:
            with open(file_name, "r") as file:
                for line in file:
                    match = re.search(r'angle=([\d\.-]+), cur=([\d\.-]+), diff=([\d\.-]+), control=([\d\.-]+)', line)
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    
                    if match and time_match:
                        game_time = convert_game_time(time_match.group(1))
                        target_angle_vals.append(float(match.group(1)))
                        current_angle_vals.append(float(match.group(2)))
                        diff_vals.append(float(match.group(3)))
                        control_vals.append(float(match.group(4)))
                        game_times.append(game_time)
            
            if game_times:
                plt.figure(figsize=(12, 15))
                
                # Top plot: Both target and current angles
                plt.subplot(3, 1, 1)
                plt.plot(game_times, target_angle_vals, 'r-', label='Target Angle', linewidth=2)
                plt.plot(game_times, current_angle_vals, 'b-', label='Current Angle', linewidth=2)
                plt.title(f'Player Steering Data - {condition} - Run {i}')
                plt.xlabel('Time (seconds)')
                plt.ylabel('Angle (degrees)')
                plt.legend()
                plt.grid(True)
                
                # Middle plot: Angle difference
                plt.subplot(3, 1, 2)
                plt.plot(game_times, diff_vals, 'g-', label='Angle Difference\n(Target - Current)', linewidth=2)
                plt.xlabel('Time (seconds)')
                plt.ylabel('Difference (degrees)')
                plt.legend()
                plt.grid(True)
                
                # Bottom plot: Control input
                plt.subplot(3, 1, 3)
                plt.plot(game_times, control_vals, 'm-', label='Control Input', linewidth=2)
                plt.xlabel('Time (seconds)')
                plt.ylabel('Control Value')
                plt.legend()
                plt.grid(True)
                
                plt.tight_layout()
                
                # Save the plot in a condition-specific subfolder
                output_dir = Path(f'DustRacing2D-master/data analysis/Player/plots/{condition}')
                output_dir.mkdir(parents=True, exist_ok=True)
                plt.savefig(output_dir / f'player_steering_run_{i}.png', dpi=300, bbox_inches='tight')
                plt.close()
                print(f"Created plot for run {i} in {condition}")
            
        except FileNotFoundError:
            print(f"Log file {file_name} not found. Skipping...")
            continue
        except Exception as e:
            print(f"Error processing run {i}: {str(e)}")
            continue

if __name__ == "__main__":
    # Test run
    plot_player_data(1, 2, "test")