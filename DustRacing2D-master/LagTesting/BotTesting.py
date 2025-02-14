# #EVLag input: sudo evlag -d /dev/input/event3 -l 100
import datetime
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from pynput.keyboard import Controller, Key

class GameTestConfig:
    def __init__(self, config_path=None):
        self.keyboard = Controller()
        self.directory = Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/build")
        # self.directory = Path("/home/parallels/Desktop/CloudGameLatencyMQP/CloudGameLatencyMQP/DustRacing2D-master/build")
        self.log_directory = Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/logs")
        # self.log_directory = Path("/home/parallels/Desktop/CloudGameLatencyMQP/CloudGameLatencyMQP/DustRacing2D-master/logs")
        # Temporary, only for no steering sharpness change
        self.lag_log_directory = Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/LagTesting/logs/assist_1.0")
        # self.lag_log_directory = Path("/home/parallels/Desktop/CloudGameLatencyMQP/CloudGameLatencyMQP/DustRacing2D-master/LagTesting/logs/assist_1.0")
        self.test_cases_file = config_path or Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/LagTesting/test_cases.json")
        # self.test_cases_file = config_path or Path("/home/parallels/Desktop/CloudGameLatencyMQP/CloudGameLatencyMQP/DustRacing2D-master/LagTesting/test_cases.json")
        self.init_wait_time = 7  # seconds
        self.test_duration = 60  # seconds
        self.num_runs = 3

class GameTester:
    def __init__(self, config: GameTestConfig):
        self.config = config
        self.ensure_directories()

    def ensure_directories(self):
        self.config.log_directory.mkdir(parents=True, exist_ok=True)

    def compile_game(self):
        print("Compiling game...")
        result = subprocess.run(
            ["make"],
            capture_output=True,
            text=True,
            cwd=self.config.directory
        )
        if result.returncode != 0:
            raise RuntimeError(f"Compilation failed: {result.stderr}")
        print("Compilation successful")
        return result.returncode == 0

    def generate_test_cases(self):
        """Generate test cases with specified number of runs per lag value"""
        test_cases = []
        assist_value = 1.0  # Fixed assist value
        
        # Generate test cases for each lag value
        for lag in range(0, 151, 10):  # 0 to 150 in steps of 10
            for run_number in range(1, self.config.num_runs + 1):
                test_case = {
                    'steering_assist': assist_value,
                    'lag': lag,
                    'run_number': run_number,
                    'name': f"Assist {assist_value} - Lag {lag}ms (Run {run_number})"
                }
                test_cases.append(test_case)
        
        return test_cases

    def move_run_logs(self, test_case):
        """
        Move log files for a specific test run.
        
        Args:
            test_case (dict): The test case containing assist value, lag value, and run number
        """
        # Create target directories
        assist_dir = self.config.log_directory / f"assist_{test_case['steering_assist']}"
        assist_dir.mkdir(parents=True, exist_ok=True)
        
        lag_dir = assist_dir / f"lag_{test_case['lag']}"
        lag_dir.mkdir(parents=True, exist_ok=True)
        
        # Move all log files with the correct run number
        log_files = [
            'cardata.log',
            'botdata.log',
            'laptime.log',
            'logfile.log'
        ]
        
        for log_file in log_files:
            src = self.config.log_directory / log_file
            if src.exists():
                # Rename with run number
                new_name = log_file.replace('.log', f'_{test_case["run_number"]}.log')
                dest = lag_dir / new_name
                shutil.move(src, dest)
                print(f"Moved {src} to {dest}")

    def run_test_case(self, test_case):
        """
        Run a single test case with the given configuration.
        
        Args:
            test_case (dict): The test case configuration containing assist value, lag value, and run number
        """
        command = [
            "./dustrac-game",
            "--lagassist", f"{test_case['lag']}:{test_case['steering_assist']}"
        ]
        
        try:
            print(f"Starting test case: {test_case['name']} (Run {test_case['run_number']})")
            process = subprocess.Popen(command, cwd=self.config.directory)
            
            # Wait for game to initialize
            time.sleep(self.config.init_wait_time)
            
            try:
                self.config.keyboard.press(Key.enter)
                self.config.keyboard.release(Key.enter)
            except Exception as e:
                print(f"Failed to simulate keyboard input: {e}")
                raise
            
            # Wait for test duration
            time.sleep(self.config.test_duration)
            
            # Terminate the process
            process.terminate()
            process.wait(timeout=5)
            
            print(f"Completed test case: {test_case['name']} (Run {test_case['run_number']})")
            
            # Add a small delay between runs
            time.sleep(2)
            
        except Exception as e:
            print(f"Test case failed: {test_case['name']} - {str(e)}")
            if 'process' in locals():
                process.terminate()
            raise

    def run_all_test_cases(self):
        """Run all test cases and handle log file movement."""
        test_cases = self.generate_test_cases()
        current_lag = None
        lag_test_cases = []
        
        for test_case in test_cases:
            # If we're starting a new lag condition, move previous logs
            if current_lag is not None and test_case['lag'] != current_lag:
                self._move_lag_logs(current_lag, lag_test_cases)
                lag_test_cases = []
            
            current_lag = test_case['lag']
            lag_test_cases.append(test_case)
            
            # Run the test case
            self.run_test_case(test_case)
        
        # Move logs for the last lag condition
        if lag_test_cases:
            self._move_lag_logs(current_lag, lag_test_cases)

    def _move_lag_logs(self, lag, test_cases):
        """Move all log files for a specific lag condition."""
        assist_value = test_cases[0]['steering_assist']
        
        # Create target directories
        assist_dir = self.config.log_directory / f"assist_{assist_value}"
        assist_dir.mkdir(parents=True, exist_ok=True)
        
        lag_dir = assist_dir / f"lag_{lag}"
        lag_dir.mkdir(parents=True, exist_ok=True)
        
        # Move all log files for this lag condition
        for test_case in test_cases:
            log_files = [
                'cardata.log',
                'botdata.log',
                'laptime.log',
                'logfile.log'
            ]
            
            for log_file in log_files:
                src = self.config.log_directory / log_file
                if src.exists():
                    # Rename with run number
                    new_name = log_file.replace('.log', f'_{test_case["run_number"]}.log')
                    dest = lag_dir / new_name
                    shutil.move(src, dest)
                    print(f"Moved {src} to {dest}")

def main():
    try:
        config = GameTestConfig()
        tester = GameTester(config)
        
        if not tester.compile_game():
            return
        
        # Run all test cases with proper log handling
        tester.run_all_test_cases()

    except Exception as e:
        print(f"Test execution failed: {e}")

if __name__ == "__main__":
    main()

# # log_directory = "/home/parallels/Desktop/CloudGameLatencyMQP/DustRacing2D-master"
# # log_directory = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master"

# # log_folder = os.path.join(log_directory, "logs")
# # log_file_path = os.path.join(log_folder, "EVLag.log")

# # Step 1: Run 'make' in the specified directory
# command_make = ["make"]
# result_make = subprocess.run(command_make, capture_output=True, text=True, cwd=directory)

# # Output the result of running 'make'
# print("Output from 'make' command:")
# print(result_make.stdout)

# # # Handle errors from 'make'
# # if result_make.returncode != 0:
# #     print(f"Error running 'make': {result_make.stderr}")
# # else:
# #     for i in range(1300):
# #         if i <= 100:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 0:1"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
# #         if i <= 200:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 100:1"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
# #         if i <= 300:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 200:1"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)

# #         if i <= 400:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 300:1"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)

# #         if i <= 500:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 0:.5"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
# #         if i <= 600:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 100:.5"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
# #         if i <= 700:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 200:.5"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
# #         if i <= 800:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 300:.5"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
# #         if i <= 900:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 0:1.5"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
# #         if i <= 1000:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 100:1.5"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
# #         if i <= 1100:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 200:1.5"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
# #         if i <= 1200:
# #             # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
# #             command_game = ["./dustrac-game --lagassist 300:1.5"]
    
# #             # Now run the game in the current terminal
# #             result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)

# def load_test_cases(config_file='/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/LagTesting/test_cases.json'):
#     with open(config_file) as f:
#         return json.load(f)

# # Generate expanded test cases with lag increments
# def generate_expanded_test_cases():
#     base_test_cases = load_test_cases()
#     expanded_test_cases = []
    
#     for test_case in base_test_cases:
#         for lag in range(0, 10, 10):  # 0 to 300ms in 10ms increments
#             expanded_test_case = test_case.copy()
#             expanded_test_case['lag'] = lag
#             expanded_test_case['name'] = f"{test_case['name']} - {lag}ms lag"
#             expanded_test_cases.append(expanded_test_case)
    
#     return expanded_test_cases

# # Move runs of an assist value to a dedicated directory
# def move_runs_to_directory(assist_value, logs_dir):
#     """Move all relevant log files for a specific assist value to a dedicated directory."""
#     # Create directory with only assist value in the name
#     assist_dir = logs_dir / f"assist_{assist_value}"
#     assist_dir.mkdir(parents=True, exist_ok=True)
    
#     # Move cardata, logfile, botdata, and laptime files
#     for run_number in range(1, 2):  # Adjust range based on expected number of runs
#         for prefix in ["cardata", "logfile", "botdata", "laptime"]:
#             source_file = logs_dir / f"{prefix}_{run_number}.log"
#             if source_file.exists():
#                 # Create new filename with only assist value
#                 new_filename = f"{prefix}_assist_{assist_value}_{run_number}.log"
#                 shutil.move(source_file, assist_dir / new_filename)
#                 print(f"Moved {source_file} to {assist_dir}/{new_filename}")

# # Run a single test case
# def run_test_case(test_case, directory):
#     command_game = [
#         "./dustrac-game",
#         "--lagassist", f"{test_case['lag']}:{test_case['steering_assist']}"
#     ]
    
#     try:
#         # Start the game process
#         result_game = subprocess.Popen(command_game, cwd=directory)
        
#         # Wait for game to initialize
#         time.sleep(5)
        
#         # Send enter key
#         keyboard.press(Key.enter)
#         keyboard.release(Key.enter)
        
#         # Wait for game to complete
#         time.sleep(60)  # Adjust based on test duration
        
#         # Properly terminate the process
#         result_game.terminate()
#         result_game.wait(timeout=5)  # Wait for process to exit
        
#     except Exception as e:
#         print(f"Error running test case: {str(e)}")
#         if 'result_game' in locals():
#             result_game.terminate()
#         raise

# # Main testing logic
# def main():
#     if result_make.returncode == 0:
#         # Load and expand test cases
#         test_cases = generate_expanded_test_cases()
        
#         for test_case in test_cases:
#             print(f"Running test case: {test_case['name']}")
#             run_test_case(test_case, directory)
            
#             # After each run, move the logs with only assist value
#             move_runs_to_directory(test_case['steering_assist'], log_folder)

# if __name__ == "__main__":
#     main()

            
