# setup_directories.py
from pathlib import Path

def create_directory_structure():
    """Create the complete directory structure for the new logging and analysis system."""
    
    # Base directories
    base_dir = Path('DustRacing2D-master')
    logs_dir = base_dir / 'logs'
    analysis_dir = base_dir / 'data analysis'
    
    # Player directories in logs
    player_dirs = ['F', 'J', 'M']
    for player in player_dirs:
        (logs_dir / player).mkdir(parents=True, exist_ok=True)
    
    # Analysis directory structure
    control_types = ['Full AI', 'Full Player', 'Mixed', 'Bot']
    analysis_subdirs = ['graphs', 'data']
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
            else:
                control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create bot analysis directory
    bot_dir = analysis_dir / 'bot'
    bot_dir.mkdir(parents=True, exist_ok=True)
    
    # Create overall analysis directory
    overall_dir = analysis_dir / 'overall'
    overall_dir.mkdir(parents=True, exist_ok=True)
    
    print("Directory structure created successfully!")
    return analysis_dir

if __name__ == "__main__":
    create_directory_structure()