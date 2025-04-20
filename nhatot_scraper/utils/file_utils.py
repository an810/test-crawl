"""
File utility functions for the Nhatot scraper.
"""
import os
import logging

logger = logging.getLogger(__name__)

def ensure_directories_exist(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def clear_file(file_path):
    """Clear the contents of a file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.truncate(0)
    logger.info(f"Cleared file: {file_path}")

def write_links(file_path, links):
    """Write links to a file"""
    clear_file(file_path)
    with open(file_path, 'w', encoding='utf-8') as f:
        for link in sorted(links):
            f.write(link + '\n')
    logger.info(f"✅ Written {len(links)} links to {file_path}")

def load_links(file_path):
    """Load links from a file"""
    if not os.path.exists(file_path):
        return set()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return set(f.read().splitlines()) 