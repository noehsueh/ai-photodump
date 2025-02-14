import os
import shutil
from .blip_categorizer import BlipCategorizer
from .photo_ranker import get_category_list, AestheticClipSelector

class PhotoDumper:
    def __init__(self, album_path: str, categories_file: str, batch_size: int = 1,
                 pre_filter: int = 100, keep_top_k: int = 1, output_dir: str = 'output',
                 aesthetic_weight: float = 0.6):
        """Initialize PhotoDumper with configuration parameters.
        
        Args:
            album_path: Path to folder containing photos
            categories_file: Path to text file containing numbered categories
            batch_size: Number of images to process in each batch
            pre_filter: Number of photos to pre-filter per category
            keep_top_k: Number of top photos to keep per category
            output_dir: Directory to save output files
            aesthetic_weight: Weight given to aesthetic score vs CLIP score
        """
        self.album_path = album_path
        self.categories_file = categories_file
        self.batch_size = batch_size
        self.pre_filter = pre_filter
        self.keep_top_k = keep_top_k
        self.output_dir = output_dir
        self.aesthetic_weight = aesthetic_weight
        
        os.makedirs(output_dir, exist_ok=True)
        
    def process(self):
        """Run the photo processing pipeline."""
        # Step 1: Categorize photos using BLIP
        categorizer = BlipCategorizer(self.categories_file)
        category_results = categorizer.categorize_album(
            self.album_path,
            batch_size=self.batch_size,
            output_file=os.path.join(self.output_dir, "category_results.json")
        )

        # Step 2: Group photos by category
        category_list = get_category_list(
            category_results,
            save_path=os.path.join(self.output_dir, "category_list.json")
        )

        # Step 3: Rank photos using aesthetic and CLIP scores
        selector = AestheticClipSelector()
        ranked_categories = selector.rank_photos(
            category_list,
            batch_size=1,
            pre_filter=self.pre_filter,
            keep_top_k=self.keep_top_k,
            aesthetic_weight=self.aesthetic_weight,
            save_path=os.path.join(self.output_dir, "ranked_categories.json")
        )
        
        # Step 4: Organize selected photos into category folders
        for category, photos in ranked_categories.items():
            category_dir = os.path.join(self.output_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            
            for photo_path in photos:
                filename = os.path.basename(photo_path)
                src = os.path.join(self.album_path, filename)
                dst = os.path.join(category_dir, filename)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
        
        return ranked_categories