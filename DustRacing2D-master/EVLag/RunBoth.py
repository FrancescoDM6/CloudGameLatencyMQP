# #EVLag input: sudo evlag -d /dev/input/event3 -l 100
import os
import subprocess

# Path to the directory where the 'Makefile' is located
directory = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/build"

# Step 1: Run 'make' in the specified directory
command_make = ["make"]
result_make = subprocess.run(command_make, capture_output=True, text=True, cwd=directory)

# Output the result of running 'make'
print("Output from 'make' command:")
print(result_make.stdout)

# Handle errors from 'make'
if result_make.returncode != 0:
    print(f"Error running 'make': {result_make.stderr}")
else:
    # Step 2: Run './dustrac-game' in the same terminal (after 'make' is done)
    command_game = ["./dustrac-game"]
    
    # Step 3: Run 'sudo evlag' in a new terminal during './dustrac-game'
    # Open a new terminal and run the evlag command in the background
    command_evlag = ["gnome-terminal", "--", "bash", "-c", "sudo evlag -d /dev/input/event3 -l 500; exec bash"]
    
    # Launch the evlag command in a new terminal window
    subprocess.Popen(command_evlag)
    
    # Now run the game in the current terminal
    result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)

    # Output the result of running './dustrac-game'
    print("Output from './dustrac-game':")
    print(result_game.stdout)

    # Handle errors from running './dustrac-game'
    if result_game.returncode != 0:
        print(f"Error running './dustrac-game': {result_game.stderr}")