# #EVLag input: sudo evlag -d /dev/input/event3 -l 100
import datetime
import os
import subprocess

# Path to the directory where the 'Makefile' is located
directory = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master/build"

log_directory = "/home/claypool/Desktop/CloudGameLatencyMQP/DustRacing2D-master"

log_folder = os.path.join(log_directory, "logs")
log_file_path = os.path.join(log_folder, "EVLag.log")

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
    command_evlag = ["gnome-terminal", "--", "bash", "-c", "sudo evlag -d /dev/input/event3 -l 200; exec bash"]
    
    # Launch the evlag command in a new terminal window
    evlag_process = subprocess.Popen(command_evlag)
    # subprocess.Popen(command_evlag)
    
    # Now run the game in the current terminal
    result_game = subprocess.run(command_game, capture_output=True, text=True, cwd=directory)

    # Output the result of running './dustrac-game'
    print("Output from './dustrac-game':")
    print(result_game.stdout)

    # Handle errors from running './dustrac-game'
    if result_game.returncode != 0:
        print(f"Error running './dustrac-game': {result_game.stderr}")
    else:
        # Step 4: Log the evlag status to the existing log file (EVLag.log)
        # Example: 'evlag -d /dev/input/event3 -l 500' -> '500' is the number to log
        evlag_number = 200  # You can set this dynamically if needed based on the command or output

        # Prepare the log message
        log_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - EVLag was ON with number: {evlag_number}\n"

        # Check if the logs folder exists, if not, create it
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
    if evlag_process.poll() is None:  # Check if evlag process is still running
        print("Stopping EVlag...")
        evlag_process.terminate()  # Terminate the evlag process
        evlag_process.wait()  # Wait for the evlag process to fully terminate
        print("EVlag stopped.")
        # Open the log file and append the log message
        with open(log_file_path, "a") as log_file:
            log_file.write(log_message)

        print(f"Logged EVLag status to {log_file_path}")
