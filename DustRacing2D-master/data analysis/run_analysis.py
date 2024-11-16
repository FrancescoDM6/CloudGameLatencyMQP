# run_analysis.py
import os
import sys
from pathlib import Path
from AI.AI_logging_graphs import plot_ai_data
from Player.Player_logging_graphs import plot_player_data
from race_analysis.all_race_analysis import run_race_analysis

import time

def create_analysis_structure():
    """Create the necessary directory structure for analysis."""
    base_dir = Path('DustRacing2D-master/data analysis')
    
    # Create main directories
    dirs = [
        base_dir / 'AI' / 'plots' / 'No_Assist',
        base_dir / 'AI' / 'plots' / 'Full_AI',
        base_dir / 'AI' / 'plots' / 'With_Assist',
        base_dir / 'Player' / 'plots' / 'No_Assist',
        base_dir / 'Player' / 'plots' / 'Full_AI',
        base_dir / 'Player' / 'plots' / 'With_Assist'
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def clear_existing_plots():
    """Clear any existing plots from the plots directory."""
    base_dir = Path('DustRacing2D-master/data analysis')
    for plot_dir in ['AI/plots', 'Player/plots']:
        full_path = base_dir / plot_dir
        if full_path.exists():
            for path in full_path.glob('**/*.png'):
                try:
                    path.unlink()
                    print(f"Removed existing plot: {path}")
                except Exception as e:
                    print(f"Error removing {path}: {e}")

def generate_summary():
    """Generate a summary of all created plots."""
    base_dir = Path('DustRacing2D-master/data analysis')
    print("\nGenerated Files Summary:")
    
    for category in ['AI', 'Player']:
        plots_dir = base_dir / category / 'plots'
        if plots_dir.exists():
            print(f"\n{category} Plots:")
            for condition_dir in plots_dir.iterdir():
                if condition_dir.is_dir():
                    plot_count = len(list(condition_dir.glob('*.png')))
                    print(f"  {condition_dir.name}: {plot_count} plots")
                    for plot_file in sorted(condition_dir.glob('*.png')):
                        print(f"    - {plot_file.name}")

def run_full_analysis():
    """Run the complete analysis pipeline."""
    start_time = time.time()
    
    print("\n=== Starting Full Analysis ===")
    print("\n1. Setting up directory structure...")
    create_analysis_structure()
    
    print("\n2. Clearing existing plots...")
    clear_existing_plots()
    
    conditions = [
        (1, 6, "No_Assist"),
        (6, 11, "Full_AI"),
        (11, 16, "With_Assist")
    ]
    
    print("\n3. Processing AI data...")
    for start, end, condition in conditions:
        print(f"\nProcessing AI {condition} condition (Files {start}-{end-1})")
        try:
            plot_ai_data(start, end, condition)
        except Exception as e:
            print(f"Error processing AI data for {condition}: {e}")
    
    print("\n4. Processing Player data...")
    for start, end, condition in conditions:
        print(f"\nProcessing Player {condition} condition (Files {start}-{end-1})")
        try:
            plot_player_data(start, end, condition)
        except Exception as e:
            print(f"Error processing Player data for {condition}: {e}")

    print("\n5. Performing Race Time Analysis...")
    run_race_analysis()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n=== Analysis Complete ===")
    print(f"Total processing time: {duration:.2f} seconds")
    
    generate_summary()

if __name__ == "__main__":
    try:
        run_full_analysis()
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred during analysis: {e}")
        sys.exit(1)