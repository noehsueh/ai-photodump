import re
from typing import List, Dict

def process_model_responses(responses: List[str], categories: str) -> List[int]:
    """
    Process the model responses to get the category number from the category list.
    Returns the index of the matching category (1-based), ignoring case.
    """
    # Split categories and extract number and text
    category_pairs = []
    for line in categories.strip().split("\n"):
        match = re.match(r"(\d+)\.\s*(.*)", line)
        if match:
            number = int(match.group(1))
            text = match.group(2).strip().lower()
            category_pairs.append((number, text))

    for response in responses:
        response = response.lower()
        for number, category_text in category_pairs:
            if category_text in response:
                return number
    return -1

def extract_description(response: str) -> str:
    """
    Extract the description from text response. Given a text, extract everything after "Assistant:\n Description: "
    """
    description_pattern = r"Assistant:\nDescription:\s*(.*)"
    match = re.search(description_pattern, response)
    if match:
        description = match.group(1)
        description = re.sub(r"^\d+\.\s*", "", description)
        return description
    else:
        return ""
