import time
import math
import asyncio
from config import Config

async def progress_for_pyrogram(current, total, ud_type, message, start, filename=""):
    """
    Stylish progress bar with minimal space
    """
    now = time.time()
    diff = now - start
    
    # Update progress every X seconds or at completion
    if round(diff % Config.ETA_UPDATE_INTERVAL) == 0 or current == total:
        try:
            percentage = current * 100 / total
            speed = current / diff if diff > 0 else 0
            eta_seconds = round((total - current) / speed) if speed > 0 else 0
            
            # Progress bar
            filled_length = math.floor(percentage / 5)
            empty_length = 20 - filled_length
            progress_bar = "●" * filled_length + "○" * empty_length
            
            # Format time
            eta_formatted = format_time(eta_seconds)
            
            # Format bytes
            current_mb = humanbytes(current)
            total_mb = humanbytes(total)
            speed_formatted = humanbytes(speed)
            
            # Create progress message
            progress_text = f"""
**{ud_type}**

`{filename}`
**to my server**

[{progress_bar}]
◌ **Progress😉:** 〘 {percentage:.2f}% 〙
**Done:** 〘{current_mb} of {total_mb}〙
◌ **Speed🚀:** 〘 {speed_formatted}/s 〙
◌ **Time Left⏳:** 〘 {eta_formatted} 〙
"""
            
            await message.edit_text(text=progress_text)
        except Exception as e:
            pass

def humanbytes(size):
    """Convert bytes to human readable format"""
    if not size or size == 0:
        return "0 B"
    
    power = 1024
    n = 0
    units = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    
    while size > power and n < 4:
        size /= power
        n += 1
    
    return f"{size:.2f} {units[n]}"

def format_time(seconds):
    """Format seconds to readable time"""
    if seconds == 0:
        return "0s"
    
    periods = [
        ('d', 86400),
        ('h', 3600),
        ('m', 60),
        ('s', 1)
    ]
    
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            if period_value > 0:
                result.append(f"{int(period_value)}{period_name}")
    
    return ', '.join(result[:2]) if result else "0s"

async def progress_bar(current, total, status_msg, action="Downloading"):
    """
    Simple progress bar for quick updates
    """
    try:
        percentage = (current / total) * 100
        filled = math.floor(percentage / 5)
        bar = "●" * filled + "○" * (20 - filled)
        
        await status_msg.edit_text(
            f"**{action}...**\n\n"
            f"[{bar}]\n"
            f"Progress: {percentage:.1f}%"
        )
    except:
        pass
