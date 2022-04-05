
import os

def dir_contains_valid_files(dir):
    """
    Check if `dir` contains any of the valid files
    """

    valid_files = [
        'metadata.csv',
        'basics.csv',
        'autosections.csv',
        'mansections.csv',
    ]

    files = os.listdir(dir)
    for file in files:
        if file in valid_files:
            return True
    return False