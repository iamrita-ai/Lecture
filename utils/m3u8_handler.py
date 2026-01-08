import subprocess
import asyncio
import os
from typing import Optional

async def download_m3u8_video(url: str, output_path: str) -> bool:
    """Download M3U8 stream using ffmpeg"""
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "downloads", exist_ok=True)
        
        # FFmpeg command
        command = [
            'ffmpeg',
            '-i', url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            '-y',
            output_path
        ]
        
        # Run ffmpeg
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        await process.communicate()
        
        return process.returncode == 0 and os.path.exists(output_path)
        
    except Exception as e:
        print(f"M3U8 download error: {e}")
        return False
