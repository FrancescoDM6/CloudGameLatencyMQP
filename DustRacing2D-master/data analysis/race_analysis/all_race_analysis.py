# race_analysis.py
import re
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from statistics import mean, stdev

def extract_race_time(log_file):
    """Extract the final time from a log file."""
    try:
        with open(log_file, "r") as file:
            content = file.readlines()
            
            # Get the last game time entry from the file
            game_times = []
            for line in content:
                time_match = re.search(r'\[GAME:\s*(\d{2}:\d{2}\.\d{2})\]', line)
                if time_match:
                    minutes, seconds = time_match.group(1).split(':')
                    total_seconds = float(minutes) * 60 + float(seconds)
                    game_times.append(total_seconds)
            
            if game_times:
                return max(game_times)
    except Exception as e:
        print(f"Error processing {log_file}: {e}")
    return None

def analyze_race_times(start_val, end_val):
    """Analyze race times for all conditions."""
    conditions = {
        "No_Assist": (1, 6),
        "Full_AI": (6, 11),
        "With_Assist": (11, 16)
    }
    
    race_data = {
        "Condition": [],
        "Run": [],
        "Time": []
    }
    
    # Extract times for each condition
    for condition, (start, end) in conditions.items():
        for i in range(start, end):
            # Check both AI and Player logs
            ai_file = f"DustRacing2D-master/logs/aidata_{i}.log"
            player_file = f"DustRacing2D-master/logs/cardata_{i}.log"
            
            # Try both files, use the one that has data
            time = extract_race_time(ai_file)
            if time is None:
                time = extract_race_time(player_file)
            
            if time is not None:
                race_data["Condition"].append(condition)
                race_data["Run"].append(i)
                race_data["Time"].append(time)
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(race_data)
    
    # Calculate statistics
    stats = df.groupby('Condition')['Time'].agg(['mean', 'std', 'min', 'max']).round(2)
    
    # Create visualizations
    plt.style.use('default')
    
    # 1. Box plot of race times by condition
    plt.figure(figsize=(12, 6))
    plt.boxplot([df[df['Condition'] == cond]['Time'] for cond in conditions.keys()],
                labels=conditions.keys())
    plt.title('Distribution of Race Times by Condition')
    plt.ylabel('Time (seconds)')
    plt.grid(True)
    
    output_dir = Path('DustRacing2D-master/data analysis/race_analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / 'race_times_boxplot.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Bar plot of individual race times
    plt.figure(figsize=(15, 6))
    bars = plt.bar(range(len(df)), df['Time'])
    
    # Color bars by condition
    colors = {'No_Assist': 'skyblue', 'Full_AI': 'lightgreen', 'With_Assist': 'salmon'}
    for i, bar in enumerate(bars):
        bar.set_color(colors[df.iloc[i]['Condition']])
    
    plt.xticks(range(len(df)), df['Run'], rotation=45)
    plt.title('Individual Race Times')
    plt.xlabel('Run Number')
    plt.ylabel('Time (seconds)')
    plt.legend(handles=[plt.Rectangle((0,0),1,1, color=c, label=l) for l, c in colors.items()])
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_dir / 'individual_race_times.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save statistics to file
    stats.to_csv(output_dir / 'race_statistics.csv')
    
    # Generate text summary
    with open(output_dir / 'race_analysis_summary.txt', 'w') as f:
        f.write("Race Time Analysis Summary\n")
        f.write("=========================\n\n")
        
        for condition in conditions.keys():
            condition_data = df[df['Condition'] == condition]
            f.write(f"{condition}:\n")
            f.write(f"  Average Time: {condition_data['Time'].mean():.2f} seconds\n")
            f.write(f"  Best Time: {condition_data['Time'].min():.2f} seconds\n")
            f.write(f"  Worst Time: {condition_data['Time'].max():.2f} seconds\n")
            f.write(f"  Standard Deviation: {condition_data['Time'].std():.2f} seconds\n\n")
            
        # Add overall analysis
        f.write("\nOverall Analysis:\n")
        f.write(f"Best Overall Time: {df['Time'].min():.2f} seconds ")
        best_run = df.loc[df['Time'].idxmin()]
        f.write(f"(Run {best_run['Run']}, {best_run['Condition']})\n")
        
        f.write(f"Average Overall Time: {df['Time'].mean():.2f} seconds\n")
        f.write(f"Total Races Analyzed: {len(df)}\n")
    
    return df, stats

def run_race_analysis():
    print("\nRunning Race Time Analysis...")
    df, stats = analyze_race_times(1, 16)
    print("\nRace analysis complete. Results saved in 'data analysis/race_analysis' directory.")
    
    # Print summary to console
    print("\nQuick Summary:")
    print(stats)
    print("\nDetailed results available in race_analysis_summary.txt")

if __name__ == "__main__":
    run_race_analysis()