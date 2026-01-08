import re
from PIL import Image, ImageDraw, ImageFont
import random
import os

def clean_filename(filename):
    """Clean filename from invalid characters"""
    # Remove invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Limit length
    if len(cleaned) > 200:
        name, ext = os.path.splitext(cleaned)
        cleaned = name[:200-len(ext)] + ext
    return cleaned

async def generate_thumbnail(mode='random'):
    """Generate thumbnail for video"""
    try:
        # Create downloads directory
        os.makedirs("downloads", exist_ok=True)
        
        # Random color
        colors = [
            (74, 144, 226),   # Blue
            (236, 100, 75),   # Red
            (255, 152, 0),    # Orange
            (67, 160, 71),    # Green
            (142, 36, 170),   # Purple
        ]
        
        color = random.choice(colors)
        
        # Create image
        img = Image.new('RGB', (1280, 720), color=color)
        draw = ImageDraw.Draw(img)
        
        # Add gradient effect (simple version)
        for i in range(720):
            alpha = i / 720
            new_color = tuple(int(c * (1 - alpha * 0.3)) for c in color)
            draw.line([(0, i), (1280, i)], fill=new_color)
        
        # Add text
        text = "Serena Lec"
        try:
            # Try to use a better font
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 100)
            except:
                font = ImageFont.load_default()
        
        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        position = ((1280 - text_width) // 2, (720 - text_height) // 2)
        
        # Add shadow
        shadow_pos = (position[0] + 3, position[1] + 3)
        draw.text(shadow_pos, text, fill=(0, 0, 0, 128), font=font)
        
        # Add main text
        draw.text(position, text, fill=(255, 255, 255), font=font)
        
        # Save thumbnail
        thumb_path = f"downloads/thumb_{random.randint(1000, 9999)}.jpg"
        img.save(thumb_path, quality=90)
        
        return thumb_path
        
    except Exception as e:
        print(f"Thumbnail generation error: {e}")
        return None

def format_duration(seconds):
    """Format duration in seconds to readable format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"
