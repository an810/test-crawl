"""
API utility functions for the Nhatot scraper.
"""
import requests
import logging

logger = logging.getLogger(__name__)

def get_api_data(region_v2, cg, start_partition, page):
    """Fetch data from Nhatot API"""
    api_gateway = 'https://gateway.chotot.com/v1/public/ad-listing?region_v2={}&cg={}&o={}&page={}&st=s,k&limit=20&w=1&key_param_included=true'
    api_url = api_gateway.format(region_v2, cg, start_partition, page)
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching data from API: {e}")
        return None 