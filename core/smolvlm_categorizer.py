import os
from typing import Dict, List
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForVision2Seq
from transformers.image_utils import load_image
from utils.image import resize_image
from utils.prompts import build_classification_prompt, add_description_to_prompt, build_description_prompt, add_assistant_prompt_classification
from utils.parsing import process_model_responses, extract_description

MODEL_NAME = "HuggingFaceTB/SmolVLM-256M-Instruct"
DEVICE = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"

def load_model():
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    model = AutoModelForVision2Seq.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    ).to(DEVICE)
    return processor, model


def describe_photos(photos: List[str], batch_size: int = 4) -> Dict[str, str]:
    """
    Describe photos.
    """
    processor, model = load_model()
    prompt = build_description_prompt()
    out = {}

    # process photos in batches
    for i in range(0, len(photos), batch_size):
        batch_photos = photos[i:i+batch_size]
        messages = [prompt] * len(batch_photos)
        images = [[resize_image(load_image(photo))] for photo in batch_photos]  

        prompts = [
            add_description_to_prompt(
                processor.apply_chat_template(message, add_generation_prompt=True)
            ) 
            for message in messages
        ]   
        # only saved model outputs text
        inputs = processor(images=images, text=prompts, return_tensors="pt", padding=True).to(DEVICE, dtype=torch.float32)
        outputs = model.generate(**inputs, max_new_tokens=1024, repetition_penalty=1.2)
        responses = processor.batch_decode(outputs, skip_special_tokens=True)
        for response, photo in zip(responses, batch_photos):
            description = extract_description(response)
            out[photo] = description
            print(description)

    return out

def from_description_to_category(descriptions: Dict[str, str], categories: str, batch_size: int = 4) -> Dict[str, str]:
    """
    Convert a description to a category number. Given a description and a list of categories,
    use the VLM model to classify the description into a category number.

    Args:
        descriptions: Dictionary of photo path and the description
        categories: String containing numbered list of categories

    Returns:
        out: Dictionary of photo path and the category it is classified into
    """
    processor, model = load_model()
    out = {}

    # process descriptions in batches
    photo_paths = list(descriptions.keys())
    for i in range(0, len(photo_paths), batch_size):
        batch_photos = photo_paths[i:i+batch_size]
        images = [[resize_image(load_image(photo))] for photo in batch_photos]
        prompts = [
            add_assistant_prompt_classification(
                processor.apply_chat_template(
                    build_classification_prompt(categories, descriptions[photo]),
                    add_generation_prompt=True
                )
            )
            for photo in batch_photos
        ]
        inputs = processor(text=prompts, 
                           images=images, 
                           return_tensors="pt", padding=True).to(DEVICE, dtype=torch.float32)
        inputs_length = inputs.input_ids.shape[1]
        outputs = model.generate(**inputs, max_new_tokens=1024, repetition_penalty=1.2)
        responses = processor.batch_decode(outputs[:, inputs_length:], skip_special_tokens=True)
        for response, photo in zip(responses, batch_photos):
            print(response)
            category = process_model_responses([response], categories)
            out[photo] = category
    return out

def save_results(results: Dict[str, int], output_file: str):
    """
    Save the results to a JSON file.
    """
    import json
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def load_results(input_file: str) -> Dict[str, int]:
    """
    Load the results from a JSON file.
    """
    import json
    with open(input_file, 'r') as f:
        return json.load(f)
