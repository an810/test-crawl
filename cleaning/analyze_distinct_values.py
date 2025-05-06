import pandas as pd
import sys
from pathlib import Path

def analyze_distinct_values(file_path):
    # Read the TSV file
    df = pd.read_csv(file_path, sep='\t')
    
    # Get column names
    columns = df.columns
    
    print("\nAnalyzing distinct values for each column:")
    print("-" * 50)
    
    analyzed_columns = ['furniture', 'direction', 'legal', 'district']

    # Analyze each column
    for column in columns:
        if column in analyzed_columns:
            distinct_values = df[column].unique()
            print(f"\nColumn: {column}")
            print(f"Number of distinct values: {len(distinct_values)}")
            print("Distinct values:")
            # Convert all values to strings for consistent sorting
            sorted_values = sorted([str(val) if not pd.isna(val) else '[NULL/NA]' for val in distinct_values])
            for value in sorted_values:
                print(f"  - {value}")

def main():
    # Get the file path from command line argument or use default
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default path to the TSV file
        file_path = "data/hn_batdongsan.tsv"
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"Error: File {file_path} does not exist!")
        sys.exit(1)
    
    try:
        analyze_distinct_values(file_path)
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 