# #EVLag input: sudo evlag -d /dev/input/event3 -l 100
import datetime
import json
import os
import subprocess

# Path to the directory where the 'Makefile' is located
# directory = "/home/parallels/Desktop/CloudGameLatencyMQP/DustRacing2D-master/build"
directory = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/build"

# log_directory = "/home/parallels/Desktop/CloudGameLatencyMQP/DustRacing2D-master"
log_directory = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master"

log_folder = os.path.join(log_directory, "logs")
log_file_path = os.path.join(log_folder, "EVLag.log")

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

def run_test_case(test_case, directory):
    command_game = [
        "./dustrac-game",
        "--lagassist", f"{test_case['lag']}:{test_case['steering_assist']}"
    ]
    result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)
    return result_game

def main():
    if result_make.returncode == 0:
        test_cases = load_test_cases()
        
        for test_case in test_cases:
            print(f"Running test case: {test_case['name']}")
            result = run_test_case(test_case, directory)
            
            if result.returncode != 0:
                print(f"Error running test case: {result.stderr}")
            else:
                print(f"Test case completed successfully")

if __name__ == "__main__":
    main()

            
