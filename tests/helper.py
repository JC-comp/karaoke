import os

def check_file_exists(file_path: str) -> bool:
    """
    Check if a file exists and is not empty.
    """
    return os.path.exists(file_path) and os.path.getsize(file_path) > 0