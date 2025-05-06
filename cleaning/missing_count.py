import pandas as pd
import os

# Create output directory if it doesn't exist
os.makedirs('cleaning/output', exist_ok=True)

def analyze_missing_values(df, output_file):
    # Count missing values for each column
    missing_counts = df.isnull().sum()
    missing_percentages = (missing_counts / len(df)) * 100

    # Create a summary DataFrame
    summary = pd.DataFrame({
        'Column Name': missing_counts.index,
        'Missing Count': missing_counts.values,
        'Missing Percentage': missing_percentages.values
    })

    # Sort by missing count in descending order
    summary = summary.sort_values('Missing Count', ascending=False)

    # Write results to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Missing Values Summary\n")
        f.write("=====================\n\n")
        f.write(summary.to_string(index=False))
        f.write(f"\n\nTotal number of rows: {len(df)}")

# Read and analyze batdongsan data
df_bds = pd.read_csv('cleaning/data/hn_batdongsan.tsv', sep='\t')
analyze_missing_values(df_bds, 'cleaning/output/missing_values_bds.txt')

# Read and analyze nhatot data
df_nhatot = pd.read_csv('cleaning/data/nhatot.tsv', sep='\t')
analyze_missing_values(df_nhatot, 'cleaning/output/missing_values_nhatot.txt')
