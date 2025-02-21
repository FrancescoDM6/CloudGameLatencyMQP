# #EVLag input: sudo evlag -d /dev/input/event3 -l 100
import datetime
import json
import os
import shutil
import subprocess
import time
import cv2
from pathlib import Path
from pynput.keyboard import Controller, Key


class GameTestConfig:
   
   def __init__(self, config_path=None):
       self.keyboard = Controller()
       self.directory = Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/build")
       # self.directory = Path("/home/parallels/Desktop/CloudGameLatencyMQP/CloudGameLatencyMQP/DustRacing2D-master/build")
       self.log_directory = Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/playtesting/logs")
       # self.log_directory = Path("/home/parallels/Desktop/CloudGameLatencyMQP/CloudGameLatencyMQP/DustRacing2D-master/logs")
       # Temporary, only for no steering sharpness change
       self.lag_log_directory = Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/playtesting/logs/assist_1.0")
       # self.lag_log_directory = Path("/home/parallels/Desktop/CloudGameLatencyMQP/CloudGameLatencyMQP/DustRacing2D-master/LagTesting/logs/assist_1.0")
       self.test_cases_file = config_path or Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/playtesting/test_cases.json")
       # self.test_cases_file = config_path or Path("/home/parallels/Desktop/CloudGameLatencyMQP/CloudGameLatencyMQP/DustRacing2D-master/LagTesting/test_cases.json")
       self.init_wait_time = 7  # seconds
       self.test_duration = 60  # seconds
       self.num_runs = 0


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
       """Generate test cases for a single assist value with varying lag values"""
       test_cases = []
       assist_value = 1.0  # Fixed assist value
      
       # Generate lag values from 0 to 150 in steps of 10
       # Set to 11 for testing
       for run_number, lag in enumerate(range(0, 151, 10), 1):
           for i in range(0, 1):
               test_case = {
                   'steering_assist': assist_value,
                   'lag': lag,
                   'run_number': run_number,
                   'name': f"Assist {assist_value} - Lag {lag}ms"
               }
               print(f"{lag}")
               test_cases.append(test_case)
      
       return test_cases


   def move_run_logs(self, test_case):
       """
       Move log files for a specific test run.
      
       Args:
           test_case (dict): The test case containing assist value, lag value, and run number
       """
       assist_dir = self.config.log_directory / f"assist_{test_case['steering_assist']}"
       assist_dir.mkdir(parents=True, exist_ok=True)
       lag_dir = self.config.lag_log_directory / f"lag_{test_case['lag']}"
       lag_dir.mkdir(parents=True, exist_ok=True)
      
       # Move all .log files into the assist directory
       for log_file in self.config.log_directory.glob("*.log"):
           new_filename = log_file.name
           shutil.move(log_file, lag_dir / new_filename)
           print(f"Moved {log_file} to {lag_dir}/{new_filename}")


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
           time.sleep(10)
          
           if cv2.getWindowProperty('DustRacing2D 2.1.1', cv2.WND_PROP_VISIBLE) == -1:
                process.terminate()
                process.wait(timeout=5)
           
           self.config.num_runs += 1
          
           if self.config.num_runs == 30:
               # Move the logs immediately after the run while we know which configuration it was
               # self.move_run_logs(test_case)
               print(f"Completed test case: {test_case['name']} (Run {test_case['run_number']})")
               self.config.num_runs = 0
          
           # Add a small delay between runs
           time.sleep(2)
          
       except Exception as e:
           print(f"Test case failed: {test_case['name']} - {str(e)}")
           if 'process' in locals():
               process.terminate()
           raise


def main():
   try:
       config = GameTestConfig()
       tester = GameTester(config)
      
       if not tester.compile_game():
           return
      
       test_cases = tester.generate_test_cases()
       for test_case in test_cases:
           try:
               # if cv2.getWindowProperty('Dust Racing 2D 2.1.1', cv2.WND_PROP_VISIBLE) == -1:
                    tester.run_test_case(test_case)
           except Exception as e:
               print(f"Failed to run test case {test_case['name']}: {e}")
               continue


   except Exception as e:
       print(f"Test execution failed: {e}")


if __name__ == "__main__":
   main()               
