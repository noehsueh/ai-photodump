import re

def remove_number_prefix(categories: str) -> str:
    """
    Given a numbered list of categories, remove the number prefix.
    """
    return re.sub(r"^\d+\.\s*", "", categories)

def build_classification_prompt(categories: str, description: str) -> str:
    """
    Build the prompt for image classification.
    
    Args:
        categories: String containing numbered list of categories
        description: String containing the description of the image
    Returns:
        Formatted prompt string for the VLM, where the text is: "Given the description of the image: " + description + "Categorize into the following categories: " + categories
    """
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Given this image:"
                },
                {
                    "type": "image"
                },
                {
                    "type": "text",
                    "text": "and its description : \"" + description + "\"" +
                    "\nTo which of the following categories does it belong to?\n" + remove_number_prefix(categories)
                }
            ]
        }
    ]
    
def build_description_prompt() -> str:
    """
    Build the prompt for image description.
    """
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "image"
                },
                {
                    "type": "text",
                    "text": (
                        "Can you describe the image?"
                    )
                }
            ]
        }
    ]

def add_description_to_prompt(prompt: str) -> str:
    """
    Add the assistant prompt to the help the model start generating from the json format.
    """
    return prompt + """\nDescription: """

def add_assistant_prompt_classification(prompt: str) -> str:
    """
    Add the assistant prompt to the help the model start generating from the json format.
    """
    return prompt + """"""