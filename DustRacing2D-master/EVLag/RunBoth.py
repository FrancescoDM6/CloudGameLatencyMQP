import subprocess

#EVLag input: sudo evlag -d /dev/input/event3 -l 100
# Define the commands to run the two programs
def run_both(lag_val=100):
    run = "Desktop/CloudGameLatencyMQP/DustRacing2D-master/build/ make"
    make = "Desktop/CloudGameLatencyMQP/DustRacing2D-master/build/ ./dustrac-game"
    evlag = f"Desktop/ sudo evlag -d /dev/input/event3 -l {lag_val}"

    # Run the first program
    run += " && " + make
    make_process = subprocess.Popen(make, shell=True)
    run_process = subprocess.Popen(run, shell=True)

    # Run the second program
    evlag_process = subprocess.Popen(evlag, shell=True)


    # Wait for both programs to complete
    make_process.wait()
    run_process.wait()
    evlag_process.wait()
    return

run_both()
