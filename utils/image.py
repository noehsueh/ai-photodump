from PIL import Image

def resize_image(image, max_height=1536, max_width=1536):
    """Resize the image only if it exceeds the specified dimensions."""
    original_width, original_height = image.size
    
    # Check if resizing is needed
    if original_width > max_width or original_height > max_height:
        print(f"Resizing image from {original_width}x{original_height} to {max_width}x{max_height}")
        # Calculate the new size maintaining the aspect ratio
        aspect_ratio = original_width / original_height
        if original_width > original_height:
            new_width = max_width
            new_height = int(max_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(max_height * aspect_ratio)
        
        # Resize the image using LANCZOS for high-quality downscaling
        return image.resize((new_width, new_height), Image.LANCZOS)
    else:
        return image