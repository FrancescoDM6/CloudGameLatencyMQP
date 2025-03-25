# #EVLag input: sudo evlag -d /dev/input/event3 -l 100
import csv
import datetime
import json
import os
import random
import shutil
import subprocess
import time
import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path
import tkinter as tk
from pynput.keyboard import Controller, Key

LatinSquare = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/Latin Square Setup.csv"

class GameTestConfig:
   
   def __init__(self, config_path=None):
       self.keyboard = Controller()
       self.directory = Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/build")
       # self.directory = Path("/home/parallels/Desktop/CloudGameLatencyMQP/CloudGameLatencyMQP/DustRacing2D-master/build")
       self.log_directory = Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/logs")
       self.playtesting_log_directory = Path("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/playtesting/logs")
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
        self.scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name("/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/universal-team-451821-f3-3f572ea732c1.json"        )
        self.client = gspread.authorize(self.creds)
        self.spreadsheet = self.client.open("Playtesting Survey")
        self.sheet = self.spreadsheet.sheet1

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

    def move_run_logs(self, test_case):
        """
        Move log files for a specific test run.

        Args:
            test_case (dict): The test case containing assist value, lag value, and run number
        """
        assist_dir = self.config.playtesting_log_directory / f"assist_{test_case['steering_assist']}"
        assist_dir.mkdir(parents=True, exist_ok=True)

        lag_dir = assist_dir / f"lag_{test_case['lag']}"
        lag_dir.mkdir(parents=True, exist_ok=True)

        for log_file in self.config.log_directory.glob("*.log"):
            new_filename = log_file.name
            shutil.move(log_file, lag_dir / new_filename)
            print(f"Moved {log_file} to {lag_dir}/{new_filename}")

    def window_exists(self, name):
        result = os.popen(f"wmctrl -l | grep '{name}'").read()
        return name in result

    def monitor_sheet(self, poll_interval=2):
        last_row_count = len(self.sheet.get_all_values())

        while True:
            try:
                current_rows = self.sheet.get_all_values()
                current_row_count = len(current_rows)

                if current_row_count > last_row_count:
                    last_row_count = current_row_count
                    return True

                time.sleep(poll_interval)
            except Exception as e:
                print("Error")
                time.sleep(poll_interval)
                return False



    def run_test_case(self, rounds):
        """
        Run a single test case with the given configuration.
        
        Args:
            test_case (dict): The test case configuration containing assist value, lag value, and run number
            player_id (int or str): The participant ID to use when reading round values
        """
        

        
        # Define the dictionary of 16 codes once
        code_mapping = {
            "1": (0, 0),
            "2": (0, 2),
            "3": (0, 4),
            "4": (0, 6),
            "5": (100, 0),
            "6": (100, 2),
            "7": (100, 4),
            "8": (100, 6),
            "9": (150, 0),
            "10": (150, 2),
            "11": (150, 4),
            "12": (150, 6),
            "13": (200, 0),
            "14": (200, 2),
            "15": (200, 4),
            "16": (200, 6)
        }

        
        # Process rounds (for example, from Round 3 to Round 21)
        for i in range(3, 22):
            round_key = f"Round {i}"
            print(f"Round {i}: {rounds[round_key]}")

            round_value = int(rounds[round_key])

            lag_value = int(code_mapping[round_key][0])
            tick_value = int(code_mapping[round_key][1])

            command = [
            "./dustrac-game",
            "--lagassist", f"{lag_value}:{tick_value}"
            ]
            
            # Convert round_value to a string to match keys in code_mapping.
            # This assumes that the code you want to look up is the same as round_value.
            code_key = str(round_value)
            if code_key in code_mapping:
                additional_values = code_mapping[code_key]
                print(f"Additional values for code {code_key}: {additional_values}")
                # Here you can integrate the additional_values as needed.
                # For example, you might add them to the test_case dictionary,
                # or use them to fill out fields on your form.
            else:
                print(f"No mapping for round value {round_value}")
        
            # Continue with existing logic to load the URL/form
            url = "https://docs.google.com/forms/d/e/1FAIpQLSetSCdvxYuVnnXDkr3iABTVI7jyy5CWpMY4SzpGFokm4Wy2TA/viewform"
            if not self.window_exists('Dust Racing 2D 2.1.1') and not self.window_exists('Playtesting Survey — Mozilla Firefox'):
                try:
                    process = subprocess.Popen(command, cwd=self.config.directory)
                    time.sleep(10)

                    while True:
                        if not self.window_exists('Dust Racing 2D 2.1.1'):
                            process.terminate()
                            process.wait(timeout=5)
                            break

                    self.config.num_runs += 1

                    if self.config.num_runs == 1:
                        self.move_run_logs(test_case)
                        self.config.num_runs = 0

                    time.sleep(2)

                    process = subprocess.Popen(["xdg-open", url])
                    time.sleep(2)
                    while True:
                        if self.monitor_sheet():
                            subprocess.run(
                                ['xdotool', 'search', '--name', 'Playtesting Survey — Mozilla Firefox', 'windowfocus', 'key', 'Ctrl+w'],
                                check=True
                            )
                            process.terminate()
                            process.wait()
                            break

                except Exception as e:
                    if 'process' in locals():
                        process.terminate()
                    raise

def read_rounds(player_id):
    csv_path = LatinSquare
    with open(csv_path, mode='r', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row.get("Participant #") == str(player_id):
                # Return the entire row as a dictionary
                return row
    raise ValueError(f"Player id {player_id} not found in CSV file.")

def main():
    player_id = 1
    set = read_rounds(player_id)
    try:
        config = GameTestConfig()
        tester = GameTester(config)
        
        if not tester.compile_game():
            return
        
        tester.run_test_case(set)


    except Exception as e:
        print(f"Test execution failed: {e}")

if __name__ == "__main__":
   main()               
