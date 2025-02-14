import os
import json
import random

import pytest
from core.smolvlm_categorizer import save_results, describe_photos, from_description_to_category, load_results

ALBUM_PATH = "/Users/noehsueh/Projects/Personal/photo-dump-ai/test_album"
CATEGORIES_PATH = "/Users/noehsueh/Projects/Personal/photo-dump-ai/photodump_list.txt"
N = 15

@pytest.fixture
def test_images():
    """Fixture to randomly select N images from a predefined album folder"""
    album_folder = ALBUM_PATH
    # Get all image files in the album folder
    all_images = [file for file in os.listdir(album_folder) if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

    if len(all_images) < N:
        raise ValueError(f"Not enough images in the album folder to select {N} images.")

    # Randomly select N images
    selected_images = random.sample(all_images, N)

    # Return the full paths of the selected images
    return [os.path.join(album_folder, image) for image in selected_images]

@pytest.fixture
def sample_categories():
    """Fixture to provide sample categories"""
    with open(CATEGORIES_PATH, 'r') as f:
        sample_categories = f.read()
    return sample_categories

@pytest.fixture
def description_file():
    """Fixture to handle results file"""
    output_file = "test_description_results.json"
    yield output_file

def test_describe_photos(test_images, description_file):
    """Test the description of photos"""
    results = describe_photos(test_images, batch_size=1)
    save_results(results, description_file)
    assert os.path.exists(description_file)
    assert len(results) == N

def test_from_description_to_category(description_file, sample_categories):
    """Test the conversion of descriptions to category numbers"""
    results = load_results(description_file)
    categories = from_description_to_category(results, sample_categories, batch_size=1)
    save_results(categories, "test_category_results.json")
    assert os.path.exists("test_category_results.json")
    assert len(categories) == N


