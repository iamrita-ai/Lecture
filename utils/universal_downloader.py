import aiohttp
import aiofiles
import asyncio
import os
import subprocess
import re
from typing import Optional
from utils.progress import progress_for_pyrogram
from utils.helpers import clean_filename
from config import Config
import time

async def download_any_file(url: str, filename: str, status_msg, user_id=None) -> Optional[str]:
    """
    Universal downloader - Supports ANY file format
    - M3U8/HLS videos
    - Direct videos (MP4, MKV, etc.)
    - Audio files
    - Documents (PDF, APK, ZIP, RAR, etc.)
    """
    try:
        clean_name = clean_filename(filename)
        
        # Detect file type from URL
        is_m3u8 = '.m3u8' in url.lower() or '/hls' in url.lower()
        is_ts_chunk = '.ts' in url.lower() and ('master' in url.lower() or 'hls' in url.lower())
        
        # If TS chunk, construct master.m3u8
        if is_ts_chunk and not is_m3u8:
            print(f"TS chunk detected, constructing master.m3u8")
            # Extract base URL
            # Example: https://domain.com/path/360p/master-123.ts -> https://domain.com/path/360p/master.m3u8
            base_url = re.sub(r'/master-[\d.]+\.ts.*', '/master.m3u8', url)
            if base_url != url:
                url = base_url
                is_m3u8 = True
                print(f"Constructed M3U8 URL: {url}")
        
        # Add extension if missing
        if '.' not in clean_name or len(clean_name.split('.')[-1]) > 5:
            if is_m3u8 or is_ts_chunk:
                clean_name += '.mp4'
            elif any(ext in url.lower() for ext in ['.mp4', '.mkv', '.avi', '.mov']):
                clean_name += '.mp4'
            elif any(ext in url.lower() for ext in ['.mp3', '.wav', '.ogg']):
                clean_name += '.mp3'
            elif '.pdf' in url.lower():
                clean_name += '.pdf'
            elif '.apk' in url.lower():
                clean_name += '.apk'
            elif '.zip' in url.lower():
                clean_name += '.zip'
            elif '.rar' in url.lower():
                clean_name += '.rar'
            else:
                clean_name += '.mp4'
        
        file_path = f"downloads/{clean_name}"
        os.makedirs("downloads", exist_ok=True)
        
        # Download based on type
        if is_m3u8:
            print(f"Downloading M3U8: {url}")
            return await download_m3u8(url, file_path, status_msg, filename)
        else:
            print(f"Downloading direct file: {url}")
            return await download_direct(url, file_path, status_msg, filename, user_id)
            
    except Exception as e:
        print(f"Universal download error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def download_m3u8(url: str, output_path: str, status_msg, filename: str) -> Optional[str]:
    """Download M3U8/HLS streams using ffmpeg"""
    try:
        if status_msg:
            await status_msg.edit_text(
                f"📥 **Downloading M3U8**\n\n"
                f"`{filename}`\n\n"
                f"⏳ Processing stream..."
            )
        
        print(f"FFmpeg downloading: {url}")
        
        command = [
            'ffmpeg',
            '-i', url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            '-y',
            '-loglevel', 'warning',
            '-stats',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                size_mb = os.path.getsize(output_path) / (1024*1024)
                print(f"✅ M3U8 downloaded: {size_mb:.2f} MB")
                return output_path
            else:
                print("❌ Output file too small or empty")
                return None
        else:
            error_msg = stderr.decode()[:500]
            print(f"❌ FFmpeg error: {error_msg}")
            return None
            
    except Exception as e:
        print(f"M3U8 download error: {e}")
        return None


async def download_direct(url: str, output_path: str, status_msg, filename: str, user_id=None) -> Optional[str]:
    """Download direct file (any format)"""
    try:
        from plugins.download import active_tasks
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3600)) as resp:
                if resp.status != 200:
                    print(f"HTTP {resp.status} for {url}")
                    return None
                
                total_size = int(resp.headers.get('content-length', 0))
                downloaded = 0
                start_time = time.time()
                
                async with aiofiles.open(output_path, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(Config.CHUNK_SIZE):
                        if user_id and user_id in active_tasks and active_tasks[user_id]['cancelled']:
                            return None
                        
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        await progress_for_pyrogram(
                            downloaded,
                            total_size,
                            "Downloading",
                            status_msg,
                            start_time,
                            filename
                        )
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    size_mb = os.path.getsize(output_path) / (1024*1024)
                    print(f"✅ Downloaded: {size_mb:.2f} MB")
                    return output_path
                return None
                
    except Exception as e:
        print(f"Direct download error: {e}")
        return None
