import pandas as pd
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BatDongSanProcessor:
    def __init__(self, input_dir='/opt/airflow/data', output_dir='/opt/airflow/data/cleaned'):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.ensure_directories_exist()

    def ensure_directories_exist(self):
        """Create output directories if they don't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logging.info(f"Created directory: {self.output_dir}")

    def convert_phaply_to_int(self, value):
        if any(substring in str(value) for substring in ['chưa', 'Chưa', 'đang', 'Đang', 'chờ', 'Chờ', 'làm sổ']):
            return 0
        elif any(substring in str(value) for substring in ['Hợp đồng', 'hợp đồng', 'HĐMB', 'HDMB']):
            return 1
        elif any(substring in str(value) for substring in ['sổ đỏ', 'Sổ đỏ', 'SỔ ĐỎ', 'Có sổ', 'Sổ hồng', 'sổ hồng', 'SỔ HỒNG', 'Đã có', 'đã có', 'sẵn sổ', 'Sẵn sổ', 'sổ đẹp', 'Sổ đẹp', 'đầy đủ', 'Đầy đủ', 'rõ ràng', 'Rõ ràng', 'chính chủ', 'Chính chủ', 'sẵn sàng', 'Sẵn sàng']):
            return 2
        else:
            return -1
    
    def one_hot_encoder_huongnha(self, value):
        directions = ['Bắc', 'Đông', 'Nam', 'Tây']
        return ''.join(['1' if direction in str(value) else '0' for direction in directions])

    def process_data(self):
        """Process the scraped data and save cleaned version"""
        try:
            # Set pandas display options
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)

            # Read input file
            input_file_path = os.path.join(self.input_dir, 'hn_batdongsan.tsv')
            if not os.path.exists(input_file_path):
                raise FileNotFoundError(f"Input file not found: {input_file_path}")

            df = pd.read_csv(input_file_path, delimiter='\t')
            logging.info(f"Successfully loaded data from {input_file_path}")

            # Process area
            df['area'] = df['area'].str.replace(' m²', '')
            df['area'] = pd.to_numeric(df['area'], errors='coerce')
            df['area'] = df['area'].fillna(0).astype(int)

            # Process width - handle decimal numbers with commas
            df['width'] = df['width'].str.replace(' m', '')
            df['width'] = df['width'].str.replace(',', '.')  # Replace comma with dot for decimal
            df['width'] = pd.to_numeric(df['width'], errors='coerce')
            df['width'] = df['width'].fillna(0).astype(float)  # Keep as float to preserve decimals

            # Process price
            df['price'] = df['price'].str.replace(' tỷ', '')
            df['price'] = df['price'].str.replace(',', '.')  # Replace comma with dot for decimal
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df['price'] = df['price'].fillna(0).astype(float)  # Keep as float to preserve decimals

            # Process bedrooms
            df['number_of_bedrooms'] = df['number_of_bedrooms'].str.replace(' phòng', '')
            df['number_of_bedrooms'] = pd.to_numeric(df['number_of_bedrooms'], errors='coerce')
            df['number_of_bedrooms'] = df['number_of_bedrooms'].fillna(0).astype(int)

            # Process toilets
            df['number_of_toilets'] = df['number_of_toilets'].str.replace(' phòng', '')
            df['number_of_toilets'] = pd.to_numeric(df['number_of_toilets'], errors='coerce')
            df['number_of_toilets'] = df['number_of_toilets'].fillna(0).astype(int)

            # Process direction and legal status
            df['direction'] = df['direction'].apply(self.one_hot_encoder_huongnha)
            df['legal'] = df['legal'].apply(self.convert_phaply_to_int)

            # Save processed data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file_path = os.path.join(self.output_dir, f'hn_batdongsan_cleaned_{timestamp}.tsv')
            df.to_csv(output_file_path, sep='\t', index=False)
            logging.info(f"Successfully saved processed data to {output_file_path}")

            return True

        except Exception as e:
            logging.error(f"Error processing data: {e}")
            return False

def process_data():
    """Function to be called from the DAG"""
    processor = BatDongSanProcessor()
    return processor.process_data() 