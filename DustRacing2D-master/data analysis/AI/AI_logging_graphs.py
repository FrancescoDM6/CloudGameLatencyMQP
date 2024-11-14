import re
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

time_vals = []

def game_time():
    for i in range(1, 11):
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
        file_path = folder_path / f'AI Game Time{i}.csv'
        df.to_csv(file_path, index=False)

def irl_time():
    for i in range(1, 11):
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

game_time()
irl_time()