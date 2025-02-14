import json
from typing import Dict

def save_results(results: Dict[str, str], output_file: str) -> None:
    """Save categorization results to a JSON file.
    
    Args:
        results: Dictionary mapping photo paths to categories
        output_file: Path to save results JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)


def load_categories(categories_file: str) -> Dict[int, str]:
    """Load categories from a text file, stripping numbers and whitespace."""
    categories = {0: "None"}  # Add None category with id 0
    with open(categories_file, 'r') as f:
        for i, line in enumerate(f, 1):
            category = line.strip()
            if '. ' in category:
                category = category.split('. ')[1]
            categories[i] = category
    return categories