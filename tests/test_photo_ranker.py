import json
import pytest
from core.photo_ranker import get_category_list, AestheticClipSelector

@pytest.fixture
def test_category_results():
    return {
        "test_album/GOPR0381.JPG": {
            "categoryName": "A funny or imperfect shot",
            "categoryNumber": 6,
            "probability": 0.0919189453125
        },
        "test_album/20230102_113011.jpg": {
            "categoryName": "None", 
            "categoryNumber": 0,
            "probability": 0.0889892578125
        },
        "test_album/20230102_115105.jpg": {
            "categoryName": "A close-up shot",
            "categoryNumber": 11,
            "probability": 0.0887451171875
        },
        "test_album/GOPR0383.JPG": {
            "categoryName": "A funny or imperfect shot",
            "categoryNumber": 6,
            "probability": 0.09136962890625
        },
        "test_album/GOPR0386.JPG": {
            "categoryName": "A funny or imperfect shot",
            "categoryNumber": 6,
            "probability": 0.0994873046875
        },
        "test_album/GOPR0384.JPG": {
            "categoryName": "A funny or imperfect shot",
            "categoryNumber": 6,
            "probability": 0.09173583984375
        },
        "test_album/GOPR0385.JPG": {
            "categoryName": "Polaroid or film-style capture",
            "categoryNumber": 8,
            "probability": 0.09149169921875
        },
        "test_album/20230102_075719.jpg": {
            "categoryName": "A candid group photo",
            "categoryNumber": 2,
            "probability": 0.0909423828125
        },
        "test_album/20230106_204443.jpg": {
            "categoryName": "A night picture",
            "categoryNumber": 9,
            "probability": 0.09686279296875
        },
        "test_album/4453ffcc-601b-40a3-ae54-346ae7f1dcb0.jpg": {
            "categoryName": "A candid group photo",
            "categoryNumber": 2,
            "probability": 0.09619140625
        },
        "test_album/20230102_075720.jpg": {
            "categoryName": "A candid group photo",
            "categoryNumber": 2,
            "probability": 0.0919189453125
        },
        "test_album/20230102_112952.jpg": {
            "categoryName": "A candid group photo",
            "categoryNumber": 2,
            "probability": 0.0924072265625
        },
        "test_album/20230102_115218.jpg": {
            "categoryName": "Polaroid or film-style capture",
            "categoryNumber": 8,
            "probability": 0.0859375
        },
        "test_album/20230102_112947.jpg": {
            "categoryName": "A candid group photo",
            "categoryNumber": 2,
            "probability": 0.09136962890625
        },
        "test_album/20230102_075649.jpg": {
            "categoryName": "None",
            "categoryNumber": 0,
            "probability": 0.088623046875
        },
        "test_album/IMG_20230106_201909397.jpg": {
            "categoryName": "A night picture",
            "categoryNumber": 9,
            "probability": 0.095458984375
        },
        "test_album/20230106_020137.jpg": {
            "categoryName": "A funny or imperfect shot",
            "categoryNumber": 6,
            "probability": 0.08978271484375
        },
        "test_album/20230102_113009.jpg": {
            "categoryName": "A funny or imperfect shot",
            "categoryNumber": 6,
            "probability": 0.0892333984375
        }
    }

def test_photo_ranker(test_category_results, tmp_path):
    # Create temporary files for testing
    test_category_results_file = tmp_path / "test_category_results.json"
    test_category_list_file = tmp_path / "test_category_list.json"
    test_ranked_categories_file = tmp_path / "test_ranked_categories.json"
    
    # Save test data
    with open(test_category_results_file, "w") as f:
        json.dump(test_category_results, f, indent=2)
    
    # Test get_category_list
    category_list = get_category_list(test_category_results, str(test_category_list_file))
    assert isinstance(category_list, dict)
    assert len(category_list) > 0
    
    # Test AestheticClipSelector
    selector = AestheticClipSelector()
    ranked_categories = selector.rank_photos(
        category_list,
        save_path=str(test_ranked_categories_file)
    )
    
    assert isinstance(ranked_categories, dict)
    assert len(ranked_categories) > 0
    assert test_ranked_categories_file.exists()


