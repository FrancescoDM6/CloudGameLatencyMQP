# #EVLag input: sudo evlag -d /dev/input/event3 -l 100
# Link for survey: https://docs.google.com/forms/d/e/1FAIpQLSfm0YFOO7FThiGeUU0znvlpNp-hrbmTQT_HHskD10qAZQtXGA/viewform?usp=header
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

LatinSquare = "/home/claypool/Desktop/CloudGameLatencyMQP/Latin Square Setup(1).csv"

player_id = 12

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
        # self.player_id = 1

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
        # assist_dir = self.config.playtesting_log_directory / f"assist_{test_case['steering_assist']}"
        # assist_dir.mkdir(parents=True, exist_ok=True)

        # lag_dir = assist_dir / f"lag_{test_case['lag']}"
        # lag_dir.mkdir(parents=True, exist_ok=True)

        id_dir = self.config.playtesting_log_directory / f"playerid{player_id}"
        id_dir.mkdir(parents=True, exist_ok=True)

        for log_file in self.config.log_directory.glob("*.log"):
            new_filename = log_file.name
            shutil.move(log_file, id_dir / new_filename)
            print(f"Moved {log_file} to {id_dir}/{new_filename}")

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

    def generate_test_case(self, rounds):
        """Generate test cases for a single assist value with varying lag values"""
        test_cases = []
        code_mapping = {
            1: (0, 0),
            2: (0, 1),
            3: (0, 2),
            4: (0, 3),
            5: (75, 0),
            6: (75, 1),
            7: (75, 2),
            8: (75, 3),
            9: (150, 0),
            10: (150, 1),
            11: (150, 2),
            12: (150, 3),
            13: (225, 0),
            14: (225, 1),
            15: (225, 2),
            16: (225, 3)
        }

    #    for assist_value in enumerate(range(0, 1.0, 0.1)):
        for i in range(1, 21):
            round_key = f"Round {i}"
            round_value = int(rounds[round_key])

            print(f"Round {i}:", round_value)


            print("Round value:", round_value)

            lag_value = int(code_mapping[round_value][0])
            tick_value = int(code_mapping[round_value][1])

            print("Lag value:", lag_value)
            print("Tick value:", tick_value)
            print("Broke after 141")

            setup = {
                        # 'tick_value': tick_value,
                        'steering_assist': tick_value,
                        'lag': lag_value,
                        'run_number': i,
                        # 'name': f"Assist {tick} - Lag 1ms"
                    }
            print("Broke after 145")
            test_cases.append(setup)
            print("Broke after 147")
        return test_cases


    def run_test_case(self, rounds):
        """
        Run a single test case with the given configuration.
        
        Args:
            test_case (dict): The test case configuration containing assist value, lag value, and run number
            player_id (int or str): The participant ID to use when reading round values
        """
        

        
        # Define the dictionary of 16 codes once
        
        test_cases = self.generate_test_case(rounds)
        
        # Process rounds (for example, from Round 3 to Round 21)
        print(test_cases)
        print("broke after command")

        for test_case in test_cases:
            command = [
            "./dustrac-game",
            "--lagassist", f"{test_case['lag']}:{test_case['steering_assist']}"
            ]
            command_evlag = [
                "gnome-terminal",
                "--disable-factory",
                "--title=evlag_terminal",
                "--",
                "bash",
                "-c",
                f"sudo evlag -d /dev/input/event3 -l {test_case['lag']};"
            ]

            print(command)
            print(command_evlag)
            print({test_case['steering_assist']})
            
            print("broke during command")
            # Continue with existing logic to load the URL/form
            url = "https://docs.google.com/forms/d/e/1FAIpQLSetSCdvxYuVnnXDkr3iABTVI7jyy5CWpMY4SzpGFokm4Wy2TA/viewform"
            if not self.window_exists('Dust Racing 2D 2.1.1') and not self.window_exists('Playtesting Survey — Mozilla Firefox'):
                try:
    
                    # Launch the evlag command in a new terminal window
                    evlag_process = subprocess.Popen(command_evlag)
                    time.sleep(.1)
                    process = subprocess.Popen(command, cwd=self.config.directory)
                    time.sleep(10)

                    while True:
                        if not self.window_exists('Dust Racing 2D 2.1.1'):
                            process.terminate()
                            process.wait(timeout=5)
                            evlag_process.terminate()  # Terminate the evlag process
                            evlag_process.wait()
                            subprocess.run(["wmctrl", "-c", "evlag_terminal"])
                            break

                    self.config.num_runs += 1

                    if self.config.num_runs == 20:
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
    set = read_rounds(player_id)
    print(set)
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
