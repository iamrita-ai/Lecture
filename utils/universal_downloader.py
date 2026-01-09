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
    """Universal downloader - Optimized for speed"""
    try:
        clean_name = clean_filename(filename)
        
        is_m3u8 = '.m3u8' in url.lower() or '/hls' in url.lower()
        is_ts_chunk = '.ts' in url.lower() and ('master' in url.lower() or 'hls' in url.lower())
        
        if is_ts_chunk and not is_m3u8:
            base_url = re.sub(r'/master-[\d.]+\.ts.*', '/master.m3u8', url)
            if base_url != url:
                url = base_url
                is_m3u8 = True
        
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
            else:
                clean_name += '.mp4'
        
        file_path = f"downloads/{clean_name}"
        os.makedirs("downloads", exist_ok=True)
        
        if is_m3u8:
            return await download_m3u8_fast(url, file_path, status_msg, filename)
        else:
            return await download_direct_fast(url, file_path, status_msg, filename, user_id)
            
    except Exception as e:
        print(f"Download error: {e}")
        return None


async def download_m3u8_fast(url: str, output_path: str, status_msg, filename: str) -> Optional[str]:
    """Fast M3U8 download with ffmpeg"""
    try:
        if status_msg:
            await status_msg.edit_text(
                f"📥 **Downloading M3U8**\n\n"
                f"`{filename}`\n\n"
                f"⚡ Fast mode enabled..."
            )
        
        command = [
            'ffmpeg',
            '-headers', 'User-Agent: Mozilla/5.0',
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            '-i', url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            '-y',
            '-loglevel', 'error',
            '-stats',
            output_path
        ]
        
        start_time = time.time()
        last_update = start_time
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        # Monitor file size for progress
        while process.returncode is None:
            await asyncio.sleep(2)
            
            if os.path.exists(output_path):
                size = os.path.getsize(output_path)
                elapsed = time.time() - start_time
                
                if time.time() - last_update > 3:
                    size_mb = size / (1024*1024)
                    speed = size / elapsed if elapsed > 0 else 0
                    speed_mb = speed / (1024*1024)
                    
                    try:
                        await status_msg.edit_text(
                            f"📥 **Downloading M3U8**\n\n"
                            f"`{filename[:40]}...`\n\n"
                            f"📦 Downloaded: {size_mb:.2f} MB\n"
                            f"⚡ Speed: {speed_mb:.2f} MB/s\n"
                            f"⏱️ Elapsed: {int(elapsed)}s"
                        )
                        last_update = time.time()
                    except:
                        pass
            
            try:
                await asyncio.wait_for(process.wait(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
        
        if process.returncode == 0:
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return output_path
        
        return None
            
    except Exception as e:
        print(f"M3U8 error: {e}")
        return None


async def download_direct_fast(url: str, output_path: str, status_msg, filename: str, user_id=None) -> Optional[str]:
    """Fast direct download with optimized settings"""
    try:
        from plugins.download import active_tasks
        
        # Optimized connector settings
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300
        )
        
        timeout = aiohttp.ClientTimeout(
            total=Config.DOWNLOAD_TIMEOUT,
            connect=60,
            sock_read=60
        )
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    print(f"HTTP {resp.status}")
                    return None
                
                total_size = int(resp.headers.get('content-length', 0))
                downloaded = 0
                start_time = time.time()
                
                async with aiofiles.open(output_path, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(Config.CHUNK_SIZE):
                        if user_id and user_id in active_tasks and active_tasks[user_id].get('cancelled'):
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
                    return output_path
                return None
                
    except Exception as e:
        print(f"Direct download error: {e}")
        return None
