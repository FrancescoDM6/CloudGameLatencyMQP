import os

def rename_aidata_files(directory):
    for filename in os.listdir(directory):
        if filename.startswith("aidata") and filename.endswith(".log"):
            base, ext = os.path.splitext(filename)
            try:
                number = int(base[7:])  # Extract the number after 'aidata'
                new_filename = f"botdata_{number + 10}{ext}"
                os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
                print(f"Renamed {filename} to {new_filename}")
            except ValueError:
                print(f"Skipping {filename}, as it does not end with a number")
        elif filename.startswith("cardata") and filename.endswith(".log"):
            base, ext = os.path.splitext(filename)
            try:
                number = int(base[8:])  # Extract the number after 'cardata'
                new_filename = f"cardata_{number + 10}{ext}"
                os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
                print(f"Renamed {filename} to {new_filename}")
            except ValueError:
                print(f"Skipping {filename}, as it does not end with a number")
        elif filename.startswith("logfile") and filename.endswith(".log"):
            base, ext = os.path.splitext(filename)
            try:
                number = int(base[8:])  # Extract the number after 'logfile'
                new_filename = f"logfile_{number + 10}{ext}"
                os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
                print(f"Renamed {filename} to {new_filename}")
            except ValueError:
                print(f"Skipping {filename}, as it does not end with a number")
# Example usage
rename_aidata_files('DustRacing2D-master\logs')