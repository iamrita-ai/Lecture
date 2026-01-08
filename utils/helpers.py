import re
from PIL import Image, ImageDraw, ImageFont
import random

def clean_filename(filename):
    """Clean filename from invalid characters"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

async def generate_thumbnail(mode='random'):
    """Generate thumbnail for video"""
    if mode == 'random' and random.randint(1, 3) != 1:
        return None
    
    # Create a simple thumbnail
    img = Image.new('RGB', (1280, 720), color=(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
    draw = ImageDraw.Draw(img)
    
    # Add text
    text = "Serena Lec"
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((1280 - text_width) // 2, (720 - text_height) // 2)
    draw.text(position, text, fill=(255, 255, 255), font=font)
    
    thumb_path = f"thumb_{random.randint(1000, 9999)}.jpg"
    img.save(thumb_path)
    return thumb_path
