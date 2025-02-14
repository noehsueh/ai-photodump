import os
import json
import random
import pytest
from core.blip_categorizer import BlipCategorizer

ALBUM_PATH = "/Users/noehsueh/Projects/Personal/photo-dump-ai/test_album"
CATEGORIES_PATH = "/Users/noehsueh/Projects/Personal/photo-dump-ai/photodump_list.txt"

@pytest.fixture
def categorizer():
    """Fixture to provide initialized BlipCategorizer"""
    return BlipCategorizer(CATEGORIES_PATH)


def test_categorize_album(categorizer):
    """Test album categorization"""
    # Run categorization
    results = categorizer.categorize_album(
        ALBUM_PATH,
        batch_size=4,
        output_file="test_blip_results.json"
    )
    
    # Check results
    assert os.path.exists("test_blip_results.json")
    assert len(results) > 0
    
    # Verify all categories are valid
    valid_categories = set(categorizer.categories)
    for category in results.values():
        assert category in valid_categories

    # Load and verify saved results
    with open("test_blip_results.json", 'r') as f:
        saved_results = json.load(f)
    assert saved_results == results
