import re
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

time_vals = []

def game_time(end_val):
    for i in range(1, end_val):
        aidata_i = []
        aidata_j = [] 
        angle_vals = []
        cur_vals = []
        diff_vals = []
        control_vals = []
        times = []
        file_name = "DustRacing2D-master/logs/aidata_" + str(i) + ".log"
        print(file_name)
        file = open(file_name, "r")
        # print(jeff)
        # print(aidata_1)
        for line in file:
            # print(line)
            match = re.search(r'car Location i:\s*(\d+\.\d+)', line)
            time = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
            if match:
                number = match.group(1)  # Use .group(1) to get only the number part
                aidata_i.append(number)

                time_val = time.group(1)
                times.append(time_val)
            match2 = re.search(r'car Location j:\s*(\d+\.\d+)', line)
            if match2:
                number2 = match2.group(1)  # Use .group(1) to get only the number part
                aidata_j.append(number2)
            match3 = re.search(r'angle=([\d\.-]+), cur=([\d\.-]+), diff=([\d\.-]+), control=([\d\.-]+)', line)
            if match3:
                angle = float(match.group(1))
                cur = float(match.group(2))
                diff = float(match.group(3))
                control = float(match.group(4))

                angle_vals.append(angle)
                cur_vals.append(cur)
                diff_vals.append(diff)
                control_vals.append(control)
        # print(time_vals)
        print(len(angle_vals))
        print(len(cur_vals))
        print(len(diff_vals))
        print(len(control_vals))
        print(len(times))
        # print(aidata_i)
        # print(aidata_j)
        # print(time_vals)
        print(len(aidata_i))
        print(len(aidata_j))
        print(len(times))
        df = pd.DataFrame({
            'Times': times,
            'I Value': aidata_i,
            'J Value': aidata_j,            
            'Angle': angle_vals,
            'Cur': cur_vals,
            'Diff': diff_vals,
            'Control': control_vals,
        })
        # Save to CSV
        folder_path = Path('DustRacing2D-master/data analysis/AI')  # or use an absolute path like 'C:/path/to/data'
        folder_path.mkdir(parents=True, exist_ok=True)  # Create folder if it doesn't exist
        # Define the file path and save the DataFrame
        file_path = folder_path / f'AI Game Time{i}.csv'
        df.to_csv(file_path, index=False)

def irl_time(end_val):
    for i in range(1, end_val):
        aidata_i = []
        aidata_j = [] 
        times = []
        file_name = "DustRacing2D-master/logs/aidata_" + str(i) + ".log"
        print(file_name)
        file = open(file_name, "r")
        # print(jeff)
        # print(aidata_1)
        for line in file:
            # print(line)
            match = re.search(r'car Location i:\s*(\d+\.\d+)', line)
            time = re.search(r'\[SYS: \d{4}-\d{2}-\d{2} (\d{2}:\d{2}:\d{2})\]', line)   
            if match:
                number = match.group(1)  # Use .group(1) to get only the number part
                aidata_i.append(number)
                time_val = time.group(1)
                # print(time_val)
                times.append(time_val)
            match2 = re.search(r'car Location j:\s*(\d+\.\d+)', line)
            if match2:
                number2 = match2.group(1)  # Use .group(1) to get only the number part
                aidata_j.append(number2)

        # print(aidata_i)
        # print(aidata_j)
        # print(time_vals)
        print(len(aidata_i))
        print(len(aidata_j))
        print(len(times))
        df = pd.DataFrame({
            'Times': times,
            'I Value': aidata_i,
            'J Value': aidata_j
        })
        # Save to CSV
        folder_path = Path('DustRacing2D-master/data analysis/AI')  # or use an absolute path like 'C:/path/to/data'
        folder_path.mkdir(parents=True, exist_ok=True)  # Create folder if it doesn't exist
        # Define the file path and save the DataFrame
        file_path = folder_path / f'AI IRL Time{i}.csv'
        df.to_csv(file_path, index=False)

def input_params(logs):   
    game_time(logs + 1)
    irl_time(logs + 1)

#input however many log files there are for aidata
input_params(13)