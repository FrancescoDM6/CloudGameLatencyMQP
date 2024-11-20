# AI/AI_logging_graphs.py
import re
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

def convert_game_time(time_str):
    """Convert game time string to seconds."""
    minutes, seconds = time_str.split(':')
    return float(minutes) * 60 + float(seconds)

def plot_ai_data(start_val, end_val, condition):
    """Create and save position plots for AI data."""
    plt.style.use('default')
    
    for i in range(start_val, end_val):
        ai_i_vals = []
        ai_j_vals = []
        target_x_vals = []
        target_y_vals = []
        game_times = []
        
        file_name = f"DustRacing2D-master/logs/botdata_{i}.log"
        print(f"Processing {file_name}")
        
        try:
            current_set = {'time': None, 'target_x': None, 'target_y': None, 'i': None, 'j': None}
            
            with open(file_name, "r") as file:
                for line in file:
                    # Extract game time from each line
                    time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                    if time_match:
                        game_time = time_match.group(1)
                        
                        # Check for each type of data
                        if 'targetNode X:' in line:
                            x_match = re.search(r'targetNode X:\s*(\d+\.\d+)', line)
                            if x_match:
                                current_set['target_x'] = float(x_match.group(1))
                                current_set['time'] = game_time
                        
                        elif 'targetNode Y:' in line:
                            y_match = re.search(r'targetNode Y:\s*(\d+\.\d+)', line)
                            if y_match:
                                current_set['target_y'] = float(y_match.group(1))
                        
                        elif 'car Location i:' in line:
                            i_match = re.search(r'car Location i:\s*(\d+\.\d+)', line)
                            if i_match:
                                current_set['i'] = float(i_match.group(1))
                        
                        elif 'car Location j:' in line:
                            j_match = re.search(r'car Location j:\s*(\d+\.\d+)', line)
                            if j_match:
                                current_set['j'] = float(j_match.group(1))
                                
                                # After finding j value, check if we have a complete set
                                if all(current_set.values()):
                                    game_times.append(convert_game_time(current_set['time']))
                                    target_x_vals.append(current_set['target_x'])
                                    target_y_vals.append(current_set['target_y'])
                                    ai_i_vals.append(current_set['i'])
                                    ai_j_vals.append(current_set['j'])
                                    
                                    # Reset for next set
                                    current_set = {'time': None, 'target_x': None, 'target_y': None, 'i': None, 'j': None}
            
            if ai_i_vals and ai_j_vals:
                print(f"Found {len(ai_i_vals)} data points for run {i}")
                
                plt.figure(figsize=(12, 8))
                
                # Plot car path
                plt.plot(ai_i_vals, ai_j_vals, 'b-', label='Car Path', linewidth=2, alpha=0.7)
                # plt.scatter(ai_i_vals[0], ai_j_vals[0], color='green', s=100, label='Start')
                # plt.scatter(ai_i_vals[-1], ai_j_vals[-1], color='red', s=100, label='End')
                
                # Plot target points with lighter color
                plt.plot(target_x_vals, target_y_vals, 'r--', label='Target Path', linewidth=1, alpha=0.4)
                
                plt.title(f'AI Position Track - {condition} - Run {i}')
                plt.xlabel('X Position')
                plt.ylabel('Y Position')
                plt.legend()
                plt.grid(True)
                
                # Save the plot in a condition-specific subfolder
                output_dir = Path(f'DustRacing2D-master\data analysis v2\Bot/{condition}')
                output_dir.mkdir(parents=True, exist_ok=True)
                plt.savefig(output_dir / f'ai_position_run_{i}.png', dpi=300, bbox_inches='tight')
                plt.close()
                print(f"Created plot for run {i} in {condition}")
            else:
                print(f"No valid data found for run {i} - Check if coordinates are present in the file")
            
        except FileNotFoundError:
            print(f"Log file {file_name} not found. Skipping...")
            continue
        except Exception as e:
            print(f"Error processing run {i}: {str(e)}")
            continue

if __name__ == "__main__":
    # Test run
    plot_ai_data(1, 2, "test")