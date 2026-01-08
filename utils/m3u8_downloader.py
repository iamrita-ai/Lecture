import aiohttp
import aiofiles
import asyncio
import os
import subprocess
from typing import Optional

async def download_m3u8(url: str, output_path: str, progress_callback=None) -> Optional[str]:
    """
    Download M3U8 stream and convert to MP4 using ffmpeg
    """
    try:
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except:
            print("FFmpeg not found, installing...")
            # Install ffmpeg (for Ubuntu/Debian)
            subprocess.run(['apt-get', 'update'], check=False)
            subprocess.run(['apt-get', 'install', '-y', 'ffmpeg'], check=False)
        
        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Download using ffmpeg
        command = [
            'ffmpeg',
            '-i', url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            '-y',  # Overwrite output file
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for completion
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return output_path
        else:
            print(f"FFmpeg error: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"M3U8 Download Error: {e}")
        return None


async def download_with_progress(url: str, output_path: str, status_msg, filename: str):
    """
    Download M3U8 with progress tracking
    """
    try:
        # Start download
        await status_msg.edit_text(
            f"📥 **Downloading M3U8 Stream**\n\n"
            f"`{filename}`\n\n"
            f"⏳ Converting to MP4...\n"
            f"This may take a while..."
        )
        
        result = await download_m3u8(url, output_path)
        
        if result:
            await status_msg.edit_text(
                f"✅ **Download Complete**\n\n"
                f"`{filename}`\n\n"
                f"📤 Uploading..."
            )
            return result
        else:
            await status_msg.edit_text(
                f"❌ **Download Failed**\n\n"
                f"`{filename}`"
            )
            return None
            
    except Exception as e:
        print(f"Download with progress error: {e}")
        return None
