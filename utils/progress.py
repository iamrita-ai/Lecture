import time
import math

async def progress_for_pyrogram(current, total, ud_type, message, start, filename=""):
    """
    Enhanced progress with ETA - Updates every 2-3 seconds
    """
    now = time.time()
    diff = now - start
    
    # Update every 2 seconds or at completion
    if round(diff % 2) == 0 or current == total:
        try:
            if total == 0:
                return
            
            percentage = current * 100 / total
            speed = current / diff if diff > 0 else 0
            eta_seconds = round((total - current) / speed) if speed > 0 else 0
            
            # Progress bar
            filled = math.floor(percentage / 5)
            empty = 20 - filled
            bar = "●" * filled + "○" * empty
            
            # Format time
            eta = format_time(eta_seconds)
            elapsed = format_time(int(diff))
            
            # Format sizes
            current_size = humanbytes(current)
            total_size = humanbytes(total)
            speed_fmt = humanbytes(speed)
            
            # Create message
            text = f"**{ud_type}**\n\n"
            text += f"`{filename[:40]}...`\n"
            text += f"**to server**\n\n"
            text += f"[{bar}]\n"
            text += f"◌ **Progress😉:** 〘 {percentage:.2f}% 〙\n"
            text += f"**Done:** 〘{current_size} of {total_size}〙\n"
            text += f"◌ **Speed🚀:** 〘 {speed_fmt}/s 〙\n"
            text += f"◌ **Time Left⏳:** 〘 {eta} 〙\n"
            text += f"⏱️ **Elapsed:** 〘 {elapsed} 〙"
            
            await message.edit_text(text)
            
        except Exception as e:
            pass

def humanbytes(size):
    """Convert bytes to human readable"""
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
    if seconds == 0 or seconds is None:
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
