import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Define directories
DATA_DIR = './cleaning/data'
OUTPUT_DIR = './cleaning/output'

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

def convert_number_format(value):
    """
    Convert number string to float handling both comma and dot cases:
    - "84,7" -> 84.7
    - "3.600" -> 3600.0
    - "1.957,5" -> 1957.5
    """
    if pd.isna(value):
        return 0.0
    
    value = str(value).strip()
    if not value:
        return 0.0

    # Remove any non-numeric characters except dots and commas
    value = ''.join(c for c in value if c.isdigit() or c in '.,')
    if not value:
        return 0.0
            
    # If there's both comma and dot, handle as thousand separator + decimal
    if ',' in value and '.' in value:
        # Remove dots (thousand separators) first, then replace comma with dot
        return float(value.replace('.', '').replace(',', '.'))
    
    # If there's only a comma, it's a decimal separator
    if ',' in value:
        return float(value.replace(',', '.'))
    
    # If there's only a dot, check if it's a thousand separator
    if '.' in value:
        # If there are multiple dots or the number after dot is 3 digits,
        # it's likely a thousand separator
        parts = value.split('.')
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            return float(value.replace('.', ''))
        # Otherwise, it's a decimal point
        return float(value)
        
    # If no special characters, just convert to float
    return float(value)

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

def convert_price_to_billion(value, area=None):
    """
    Convert price string to float in billion VND:
    - "165 triệu/m2" -> area * 0.165 (if area provided)
    - "3.5 tỷ" -> 3.5
    - "1.234,5 triệu" -> 1.2345
    """
    if pd.isna(value):
        return 0.0
    
    value = str(value).strip()
    if not value:
        return 0.0

    try:
        # Handle price per square meter
        if any(unit in value.lower() for unit in ['triệu/m2', '/m2', '/m²']):
            # Extract the number part
            price_per_m2 = convert_number_format(value.lower().split('/')[0].strip())
            if area is not None and not pd.isna(area) and area > 0:
                # Convert to billion: (price_per_m2 * area) / 1000
                return (price_per_m2 * area) / 1000
            return 0.0

        # Handle total price
        if 'tỷ' in value.lower():
            # Remove 'tỷ' and convert to float
            return convert_number_format(value.lower().replace('tỷ', '').strip())
        elif 'triệu' in value.lower():
            # Convert million to billion
            million_value = convert_number_format(value.lower().replace('triệu', '').strip())
            return million_value / 1000
        
        # If no unit specified, assume it's already in billion
        return convert_number_format(value)
    except Exception as e:
        logging.warning(f"Error converting price value '{value}': {str(e)}")
        return 0.0

# Set the display options
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Specify the file path
input_file_path = os.path.join(DATA_DIR, 'hn_batdongsan.tsv')

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
df['area'] = df['area'].apply(convert_number_format)

df['width'] = df['width'].str.replace(' m', '')
df['width'] = df['width'].apply(convert_number_format)

# Process price
df['price'] = df.apply(lambda row: convert_price_to_billion(row['price'], row['area']), axis=1)

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
output_file_path = os.path.join(OUTPUT_DIR, 'processed_hn_batdongsan.tsv')
try:
    df.to_csv(output_file_path, sep='\t', index=False)
    logging.info(f"Successfully saved processed data to {output_file_path}")
except Exception as e:
    logging.error(f"Error saving output file: {e}")
    exit(1)