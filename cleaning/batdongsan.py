import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Define directories
DATA_DIR = './data'
OUTPUT_DIR = './data/cleaned'

# Create directories if they don't exist
def ensure_directories_exist():
    """Create output directories if they don't exist"""
    directories = [DATA_DIR, OUTPUT_DIR]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"Created directory: {directory}")

# Call this function at the beginning
ensure_directories_exist()

def convert_phaply_to_int(value):
    if any(substring in str(value) for substring in ['chưa', 'Chưa', 'đang', 'Đang', 'chờ', 'Chờ', 'làm sổ']):
        return 0
    elif any(substring in str(value) for substring in ['Hợp đồng', 'hợp đồng', 'HĐMB', 'HDMB']):
        return 1
    elif any(substring in str(value) for substring in ['sổ đỏ', 'Sổ đỏ', 'SỔ ĐỎ', 'Có sổ', 'Sổ hồng', 'sổ hồng', 'SỔ HỒNG', 'Đã có', 'đã có', 'sẵn sổ', 'Sẵn sổ', 'sổ đẹp', 'Sổ đẹp', 'đầy đủ', 'Đầy đủ', 'rõ ràng', 'Rõ ràng', 'chính chủ', 'Chính chủ', 'sẵn sàng', 'Sẵn sàng']):
        return 2
    else:
        return -1
    
def one_hot_encoder_huongnha(value):
    directions = ['Bắc', 'Đông', 'Nam', 'Tây']
    return ''.join(['1' if direction in str(value) else '0' for direction in directions])

# Set the display options
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Specify the file path
input_file_path = os.path.join(DATA_DIR, 'hn_batdongsan_old.tsv')

# Check if input file exists
if not os.path.exists(input_file_path):
    logging.error(f"Input file not found: {input_file_path}")
    exit(1)

# Read the TSV file
try:
    df = pd.read_csv(input_file_path, delimiter='\t')
    logging.info(f"Successfully loaded data from {input_file_path}")
except Exception as e:
    logging.error(f"Error reading input file: {e}")
    exit(1)

# # Check for missing values
# print(df.isnull().sum())

# Convert the data to a DataFrame
df['area'] = df['area'].str.replace(' m²', '')
df['area'] = pd.to_numeric(df['area'], errors='coerce')
df['area'] = df['area'].fillna(0).astype(int)

df['width'] = df['width'].str.replace(' m', '')
df['width'] = df['width'].str.replace(',', '.')  # Replace comma with dot for decimal
df['width'] = pd.to_numeric(df['width'], errors='coerce')
df['width'] = df['width'].fillna(0).astype(float)  # Keep as float to preserve decimals

# Process price
df['price'] = df['price'].str.replace(' tỷ', '')
df['price'] = df['price'].str.replace(',', '.')  # Replace comma with dot for decimal
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['price'] = df['price'].fillna(0).astype(float)  # Keep as float to preserve decimals


df['number_of_bedrooms'] = df['number_of_bedrooms'].str.replace(' phòng', '')
df['number_of_bedrooms'] = pd.to_numeric(df['number_of_bedrooms'], errors='coerce')
df['number_of_bedrooms'] = df['number_of_bedrooms'].fillna(0).astype(int)

df['number_of_toilets'] = df['number_of_toilets'].str.replace(' phòng', '')
df['number_of_toilets'] = pd.to_numeric(df['number_of_toilets'], errors='coerce')
df['number_of_toilets'] = df['number_of_toilets'].fillna(0).astype(int)

df['direction'] = df['direction'].apply(one_hot_encoder_huongnha)
df['legal'] = df['legal'].apply(convert_phaply_to_int)

# Count and print the unique values of the 'direction' column
value_counts = df['furniture'].value_counts()
filtered_counts = value_counts[value_counts > 10]
# print(filtered_counts)

# Print the data
# print(df[['area', 'width', 'number_of_bedrooms', 'number_of_toilets', 'price', 'lat', 'lon', 'furniture', 'legal']].head(10))

# Save the processed data
output_file_path = os.path.join(OUTPUT_DIR, 'hn_batdongsan_old.tsv')
try:
    df.to_csv(output_file_path, sep='\t', index=False)
    logging.info(f"Successfully saved processed data to {output_file_path}")
except Exception as e:
    logging.error(f"Error saving output file: {e}")
    exit(1)