import os
import json
import torch
from PIL import Image
from typing import Dict, List, Optional
from transformers import AutoProcessor, Blip2ForImageTextRetrieval
from utils.utils import load_categories, save_results

class BlipCategorizer:
    def __init__(self, categories_file: str):
        """
        Initialize the BlipCategorizer with categories from a file.
        
        Args:
            categories_file: Path to text file containing numbered categories
        """
        self.categories = load_categories(categories_file)
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.model = Blip2ForImageTextRetrieval.from_pretrained(
            "Salesforce/blip2-itm-vit-g", 
            torch_dtype=torch.float16
        )
        self.processor = AutoProcessor.from_pretrained("Salesforce/blip2-itm-vit-g")
        self.model.to(self.device)


    def categorize_album(self, album_path: str, batch_size: int = 4, output_file: Optional[str] = None) -> Dict[str, dict]:
        """
        Categorize all photos in an album using BLIP-2 model.
        
        Args:
            album_path: Path to folder containing photos
            batch_size: Number of images to process in each batch
            output_file: Optional path to save results as JSON
            
        Returns:
            Dictionary mapping photo paths to their category details
        """
        results = {}
        image_paths = []

        # Collect valid image paths
        for filename in os.listdir(album_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(album_path, filename)
                image_paths.append(image_path)

        # Process images in batches
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_images = [Image.open(path) for path in batch_paths]
            
            # Prepare text prompts
            texts = [f"A photo of {c}" for c in self.categories.values()]
            
            # Get model predictions
            inputs = self.processor(
                images=batch_images,
                text=texts,
                return_tensors="pt",
                padding=True
            ).to(self.device, torch.float16)

            with torch.no_grad():
                outputs = self.model(
                    **inputs,
                    use_image_text_matching_head=False
                )
                # Get similarity scores and probabilities
                logits = outputs.logits_per_image
                probs = logits.softmax(dim=1)
                
                # Get best matching categories and probabilities for batch
                category_indices = probs.argmax(dim=1)
                best_probs = probs.max(dim=1).values
                
                # Store results
                for path, category_idx, prob in zip(batch_paths, category_indices, best_probs):
                    category_num = category_idx.item()
                    results[path] = {
                        "categoryName": self.categories[category_num],
                        "categoryNumber": int(category_num),
                        "probability": float(prob)
                    }

        if output_file:
            save_results(results, output_file)
                
        return results
