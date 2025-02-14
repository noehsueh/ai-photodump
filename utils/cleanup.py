import os
import shutil
from pathlib import Path

def remove_temp_files(base_path: Path, temp_paths: list):
    """
    Remove temporary files and directories.

    Parameters:
        base_path (Path): The base directory to reference.
        temp_paths (list): List of relative paths (str) to remove.
    """
    base_dir = Path(base_path)
    for temp in temp_paths:
        temp_path = base_dir / temp
        if temp_path.exists():
            try:
                if temp_path.is_dir():
                    shutil.rmtree(temp_path)
                else:
                    os.remove(temp_path)
            except Exception as e:
                print(f"Failed to remove {temp_path}: {e}")

def clear_directory(directory: Path):
    """
    Clear all contents of the given directory without removing the directory itself.

    Parameters:
        directory (Path): The directory to clear.
    """
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        return
    for item in dir_path.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                os.remove(item)
        except Exception as e:
            print(f"Failed to clear {item}: {e}")