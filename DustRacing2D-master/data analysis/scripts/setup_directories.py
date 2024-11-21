# setup_directories.py
from pathlib import Path
import shutil

def create_directory_structure():
    """Create the complete directory structure for the new logging and analysis system."""
    
    # Base directories
    base_dir = Path('DustRacing2D-master')
    logs_dir = base_dir / 'logs'
    analysis_dir = base_dir / 'data analysis'
    
    # Store scripts directory content if it exists
    scripts_dir = analysis_dir / 'scripts'
    scripts_backup = None
    if scripts_dir.exists():
        scripts_backup = scripts_dir
    
    # Remove old analysis directory contents except scripts
    if analysis_dir.exists():
        print("Removing old analysis directory contents...")
        for item in analysis_dir.iterdir():
            if item.name != 'scripts':
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    else:
        analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Restore scripts directory if it was backed up
    if scripts_backup is not None:
        scripts_dir = analysis_dir / 'scripts'
        print("Preserving scripts directory...")
    
    # Player directories in logs
    player_dirs = ['F', 'J', 'M']
    for player in player_dirs:
        (logs_dir / player).mkdir(parents=True, exist_ok=True)
    
    # Analysis directory structure
    control_types = ['1.0 Control Assistance', '0.0 Control Assistance', '0.2 Control Assistance', 'Bot']
    player_analysis_subdirs = ['Player', 'Comparisons', 'Summary']
    
    # Create player-specific analysis directories
    players_dir = analysis_dir / 'players'
    for player in player_dirs:
        player_base = players_dir / player
        for control in control_types:
            control_dir = player_base / control
            if control != 'Bot':  # Bot doesn't need the same subdirectories
                for subdir in player_analysis_subdirs:
                    (control_dir / subdir).mkdir(parents=True, exist_ok=True)
                    print(f"Created {subdir} directory for {player}/{control}")
            else:
                control_dir.mkdir(parents=True, exist_ok=True)
                print(f"Created Bot directory for {player}")
    
    # Create bot analysis directory
    bot_dir = analysis_dir / 'bot'
    bot_dir.mkdir(parents=True, exist_ok=True)
    print("Created bot analysis directory")
    
    # Create overall analysis directory
    overall_dir = analysis_dir / 'overall'
    overall_dir.mkdir(parents=True, exist_ok=True)
    print("Created overall analysis directory")
    
    print("\nDirectory structure created successfully!")
    print("Note: 'scripts' directory was preserved")
    
    return analysis_dir

if __name__ == "__main__":
    create_directory_structure()