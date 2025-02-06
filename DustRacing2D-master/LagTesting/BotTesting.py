# #EVLag input: sudo evlag -d /dev/input/event3 -l 100
import datetime
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from pynput.keyboard import Controller, Key

# Initialize keyboard controller
keyboard = Controller()

# Path to the directory where the 'Makefile' is located
# directory = "/home/parallels/Desktop/CloudGameLatencyMQP/DustRacing2D-master/build"
directory = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/build"
log_directory = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/logs"

# Ensure logs directory exists
log_folder = Path(log_directory)
log_folder.mkdir(parents=True, exist_ok=True)

# log_directory = "/home/parallels/Desktop/CloudGameLatencyMQP/DustRacing2D-master"
# log_directory = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master"

# log_folder = os.path.join(log_directory, "logs")
# log_file_path = os.path.join(log_folder, "EVLag.log")

# Step 1: Run 'make' in the specified directory
command_make = ["make"]
result_make = subprocess.run(command_make, capture_output=True, text=True, cwd=directory)

# Output the result of running 'make'
print("Output from 'make' command:")
print(result_make.stdout)

# # Handle errors from 'make'
# if result_make.returncode != 0:
#     print(f"Error running 'make': {result_make.stderr}")
# else:
#     for i in range(1300):
#         if i <= 100:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 0:1"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
#         if i <= 200:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 100:1"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
#         if i <= 300:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 200:1"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)

#         if i <= 400:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 300:1"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)

#         if i <= 500:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 0:.5"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
#         if i <= 600:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 100:.5"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
#         if i <= 700:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 200:.5"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
#         if i <= 800:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 300:.5"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
#         if i <= 900:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 0:1.5"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
#         if i <= 1000:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 100:1.5"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
#         if i <= 1100:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 200:1.5"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
#         if i <= 1200:
#             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
#             command_game = ["./dustrac-game --lagassist 300:1.5"]
    
#             # Now run the game in the current terminal
#             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)

def load_test_cases(config_file='/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/LagTesting/test_cases.json'):
    with open(config_file) as f:
        return json.load(f)

# Generate expanded test cases with lag increments
def generate_expanded_test_cases():
    base_test_cases = load_test_cases()
    expanded_test_cases = []
    
    for test_case in base_test_cases:
        for lag in range(0, 10, 10):  # 0 to 300ms in 10ms increments
            expanded_test_case = test_case.copy()
            expanded_test_case['lag'] = lag
            expanded_test_case['name'] = f"{test_case['name']} - {lag}ms lag"
            expanded_test_cases.append(expanded_test_case)
    
    return expanded_test_cases

# Move runs of an assist value to a dedicated directory
def move_runs_to_directory(assist_value, logs_dir):
    """Move all relevant log files for a specific assist value to a dedicated directory."""
    assist_dir = logs_dir / f"assist_{assist_value}"
    assist_dir.mkdir(parents=True, exist_ok=True)
    
    # Move cardata, logfile, botdata, and laptime files
    for run_number in range(1, 101):  # Adjust range based on expected number of runs
        for prefix in ["cardata", "logfile", "botdata", "laptime"]:
            source_file = logs_dir / f"{prefix}_{run_number}.log"
            if source_file.exists():
                shutil.move(source_file, assist_dir)
                print(f"Moved {source_file} to {assist_dir}")

# Run a single test case
def run_test_case(test_case, directory):
    command_game = [
        "./dustrac-game",
        "--lagassist", f"{test_case['lag']}:{test_case['steering_assist']}"
    ]
    
    try:
        # Start the game process
        result_game = subprocess.Popen(command_game, cwd=directory)
        
        # Wait for game to initialize
        time.sleep(5)
        
        # Send enter key
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        
        # Wait for game to complete
        time.sleep(60)  # Adjust based on test duration
        
        # Properly terminate the process
        result_game.terminate()
        result_game.wait(timeout=5)  # Wait for process to exit
        
    except Exception as e:
        print(f"Error running test case: {str(e)}")
        if 'result_game' in locals():
            result_game.terminate()
        raise

# Main testing logic
def main():
    if result_make.returncode == 0:
        # Load and expand test cases
        test_cases = generate_expanded_test_cases()
        
        for test_case in test_cases:
            print(f"Running test case: {test_case['name']}")
            run_test_case(test_case, directory)
            
            # After all runs for an assist value are complete, move the logs
            if test_case['lag'] == 0:  # Last lag value for this assist
                move_runs_to_directory(test_case['steering_assist'], log_folder)

if __name__ == "__main__":
    main()

            
