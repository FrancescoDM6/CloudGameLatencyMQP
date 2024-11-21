import os
from pathlib import Path
import shutil

def manuevere_Player():
    try: 
        os.makedirs("DustRacing2D-master/logs/Player", exist_ok=True)
    except Exception as e:
        print(f"An error occured: {e}") 
    for item in os.listdir("DustRacing2D-master/logs"):
        if item.startswith("cardata_"):
            source = Path(f"DustRacing2D-master/logs/{item}")
            destination = Path(f"DustRacing2D-master/logs/Player/{item}")
            try:
                shutil.move(str(source), str(destination))
                print(f"Moved {source} to {destination}")
            except Exception as e:
                print(f"Movement Error: {e}")
        if item.startswith("botdata_"):
            source = Path(f"DustRacing2D-master/logs/{item}")
            destination = Path(f"DustRacing2D-master/logs/Player/{item}")
            try:
                shutil.copy(str(source), str(destination))
                print(f"Moved {source} to {destination}")
            except Exception as e:
                print(f"Movement Error: {e}")

def manuevere_Bot():
    try: 
        os.makedirs("DustRacing2D-master/logs/Bot", exist_ok=True)
    except Exception as e:
        print(f"An error occured: {e}") 
    for item in os.listdir("DustRacing2D-master/logs"):
        if item.startswith("botdata_"):
            source = Path(f"DustRacing2D-master/logs/{item}")
            destination = Path(f"DustRacing2D-master/logs/Bot/{item}")
            try:
                shutil.copy(str(source), str(destination))
                print(f"Moved {source} to {destination}")
            except Exception as e:
                print(f"Movement Error: {e}")

manuevere_Player()
manuevere_Bot()
            