import aiohttp
import aiofiles
import asyncio
import os
import subprocess
from typing import Optional

async def download_m3u8_video(url: str, output_path: str, status_msg=None, filename="video") -> Optional[str]:
    """Download M3U8 with ffmpeg - Simple & Reliable"""
    try:
        os.makedirs("downloads", exist_ok=True)
        
        if status_msg:
            await status_msg.edit_text(
                f"📥 **Downloading M3U8**\n\n"
                f"`{filename}`\n\n"
                f"⏳ Starting download..."
            )
        
        print(f"🎥 Downloading M3U8: {url}")
        print(f"📁 Output: {output_path}")
        
        # Use ffmpeg directly - most reliable
        command = [
            'ffmpeg',
            '-i', url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            '-y',
            '-loglevel', 'error',
            '-stats',
            output_path
        ]
        
        if status_msg:
            await status_msg.edit_text(
                f"📥 **Downloading M3U8**\n\n"
                f"`{filename}`\n\n"
                f"⏳ Processing with ffmpeg...\n"
                f"This may take a few minutes..."
            )
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"✅ Download successful: {os.path.getsize(output_path)} bytes")
                return output_path
            else:
                print(f"❌ File empty or doesn't exist")
                return None
        else:
            print(f"❌ FFmpeg failed with code {process.returncode}")
            print(f"Error: {stderr.decode()[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ M3U8 Download Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def download_m3u8_simple(url: str, output_path: str) -> Optional[str]:
    """Fallback simple method"""
    try:
        command = ['ffmpeg', '-i', url, '-c', 'copy', '-y', output_path]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        await process.communicate()
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        return None
        
    except Exception as e:
        print(f"Simple download error: {e}")
        return None
