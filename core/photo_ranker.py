from typing import Dict, List, Optional
from PIL import Image
from torchmetrics.multimodal.clip_score import CLIPScore
import torch
from aesthetics_predictor import AestheticsPredictorV1
from transformers import CLIPProcessor, CLIPModel

def get_category_list(photo_dict: Dict[str, Dict], save_path: str = None) -> Dict[str, List[str]]:
    """
    Convert a dictionary of photo paths and their category details into a dictionary
    where each category name maps to a list of photos sorted by probability.

    Args:
        photo_dict: Dictionary mapping photo paths to dictionaries containing categoryName and probability
        save_path: Optional path to save the category list as a JSON file

    Returns:
        out_dict: A dictionary where each category name maps to a list of photo paths,
                 sorted by descending probability
    """
    category_list = {}
    for photo, details in photo_dict.items():
        category = details["categoryName"]
        probability = details["probability"]
        if category not in category_list:
            category_list[category] = []
        category_list[category].append((photo, probability))
    
    # Sort photos in each category by probability
    for category in category_list:
        category_list[category].sort(key=lambda x: x[1], reverse=True)
        category_list[category] = [photo for photo, _ in category_list[category]]
    
    if save_path:
        import json
        with open(save_path, 'w') as f:
            json.dump(category_list, f, indent=2)
    
    return category_list

class ClipSelector:
    def __init__(self, model_name_or_path: str = 'openai/clip-vit-large-patch14'):
        """Initialize CLIP-based photo selector."""
        self.clip_model = CLIPScore(model_name_or_path=model_name_or_path)

    def _preprocess_image(self, photo_path: str) -> torch.Tensor:
        """Convert image to RGB tensor."""
        with Image.open(photo_path) as img:
            img = img.convert('RGB')
            return torch.tensor(list(img.getdata())).reshape(3, img.size[1], img.size[0])

    def _get_clip_scores(self, photos: List[str], prompt: str, batch_size: int) -> List[tuple]:
        """Get CLIP similarity scores for photos."""
        scored_photos = []
        for i in range(0, len(photos), batch_size):
            batch = photos[i:i + batch_size]
            images = [self._preprocess_image(photo) for photo in batch]
            prompts = [prompt] * len(batch)
            
            scores = []
            for img, txt in zip(images, prompts):
                score = float(self.clip_model(img, txt).detach())
                scores.append(score)
                
            scored_photos.extend(zip(batch, scores))
        return scored_photos

    def rank_photos_in_categories(self, category_photos: Dict[str, List[str]],
                                batch_size: int = 4, pre_filter: int = 100, keep_top_k: int = 1,
                                save_path: Optional[str] = None) -> Dict[str, List[str]]:
        """Rank photos in each category by CLIP similarity to the category name."""
        ranked_categories = {}
        scored_categories = {}  # For saving scores
        filtered_photos = {
            category: photos[:pre_filter] if pre_filter else photos 
            for category, photos in category_photos.items()
            if category != "None"
        }
        
        for category, photos in filtered_photos.items():
            scored_photos = self._get_clip_scores(photos, category, batch_size)
            scored_photos.sort(key=lambda x: x[1], reverse=True)
            ranked_categories[category] = [photo for photo, _ in scored_photos[:keep_top_k]]
            scored_categories[category] = {
                photo: score for photo, score in scored_photos[:keep_top_k]
            }
            
        if save_path:
            import json
            with open(save_path, 'w') as f:
                json.dump(scored_categories, f, indent=2)
                
        return ranked_categories

class AestheticClipSelector:
    def __init__(
        self,
        aestethic_model_id: str = "shunk031/aesthetics-predictor-v1-vit-large-patch14",
        clip_model_id: str = "openai/clip-vit-large-patch14"
    ):
        """Initialize the aesthetic predictor model."""
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.predictor = AestheticsPredictorV1.from_pretrained(aestethic_model_id).to(self.device)
        self.clip = CLIPModel.from_pretrained(clip_model_id).to(self.device)
        self.predictor_processor = CLIPProcessor.from_pretrained(aestethic_model_id)
        self.clip_processor = CLIPProcessor.from_pretrained(clip_model_id)

    def _get_aesthetic_clip_score(
        self,
        photo_path: str,
        clip_prompt: str = "a high quality photo",
        aestethic_weight: float = 0.3
    ) -> float:
        """Get aesthetic score for a single photo."""
        with Image.open(photo_path) as img:
            img = img.convert('RGB')
            # Get aesthetic score
            aesthetic_inputs = self.predictor_processor(images=img, return_tensors="pt")
            aesthetic_inputs = {k: v.to(self.device) for k, v in aesthetic_inputs.items()}
            
            # Get CLIP score
            clip_inputs = self.clip_processor(
                text=[clip_prompt], 
                images=img, 
                return_tensors="pt",
                padding=True
            )
            clip_inputs = {k: v.to(self.device) for k, v in clip_inputs.items()}
            
            with torch.no_grad():
                # Get aesthetic score
                aesthetic_outputs = self.predictor(**aesthetic_inputs)
                aesthetic_score = float(aesthetic_outputs.logits[0])
                
                # Get CLIP score
                clip_outputs = self.clip(**clip_inputs)
                clip_score = float(clip_outputs.logits_per_image[0][0])
                
                # Combine scores using convex combination
                final_score = aestethic_weight * aesthetic_score + (1 - aestethic_weight) * clip_score
                
                return final_score

    def rank_photos(self, photos: Dict[str, List[str]], batch_size: int = 1,
                   pre_filter: int = 100, keep_top_k: int = 10,
                   aesthetic_weight: float = 0.3,
                   save_path: Optional[str] = None) -> Dict[str, List[str]]:
        """Rank photos in each category by aesthetic and CLIP scores.
        
        Args:
            photos: Dictionary mapping categories to lists of photo paths
            batch_size: Number of photos to process at once
            pre_filter: Number of photos to pre-filter per category 
            keep_top_k: Number of top photos to keep per category
            aesthetic_weight: Weight given to aesthetic score vs CLIP score
            save_path: Optional path to save scores
            
        Returns:
            Dictionary mapping categories to lists of top ranked photos
        """
        ranked_categories = {}
        scored_categories = {}
        
        filtered_photos = {
            category: photos[:pre_filter] if pre_filter else photos
            for category, photos in photos.items() 
            if category != "None"
        }
        
        for category, category_photos in filtered_photos.items():
            scored_photos = []
            for i in range(0, len(category_photos), batch_size):
                batch_photos = category_photos[i:i + batch_size]
                for photo in batch_photos:
                    score = self._get_aesthetic_clip_score(photo, clip_prompt=f"{category}", aestethic_weight=aesthetic_weight)
                    scored_photos.append((photo, score))
                    
            scored_photos.sort(key=lambda x: x[1], reverse=True)
            ranked_categories[category] = [photo for photo, _ in scored_photos[:keep_top_k]]
            scored_categories[category] = {
                photo: score for photo, score in scored_photos[:keep_top_k]
            }
            
        if save_path:
            import json
            with open(save_path, 'w') as f:
                json.dump({
                    category: {
                        photo: score for photo, score in photos.items()
                    } for category, photos in scored_categories.items()
                }, f, indent=2)
        return ranked_categories
