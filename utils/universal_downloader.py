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
    """Universal downloader with error handling"""
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
    """Fast M3U8 download"""
    try:
        if status_msg:
            try:
                await status_msg.edit_text(
                    f"📥 **Downloading M3U8**\n\n"
                    f"`{filename[:40]}...`\n\n"
                    f"⚡ Fast mode..."
                )
            except:
                pass
        
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
            output_path
        ]
        
        start_time = time.time()
        last_update = start_time
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        # Monitor progress
        while True:
            await asyncio.sleep(3)
            
            # Check if process finished
            if process.returncode is not None:
                break
            
            try:
                await asyncio.wait_for(process.wait(), timeout=0.1)
                break
            except asyncio.TimeoutError:
                pass
            
            # Update status
            if os.path.exists(output_path) and status_msg:
                elapsed = time.time() - start_time
                if time.time() - last_update > 5:
                    size_mb = os.path.getsize(output_path) / (1024*1024)
                    
                    try:
                        await status_msg.edit_text(
                            f"📥 **Downloading M3U8**\n\n"
                            f"`{filename[:40]}...`\n\n"
                            f"📦 {size_mb:.2f} MB\n"
                            f"⏱️ {int(elapsed)}s"
                        )
                        last_update = time.time()
                    except:
                        pass
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return output_path
        
        return None
            
    except Exception as e:
        print(f"M3U8 error: {e}")
        return None


async def download_direct_fast(url: str, output_path: str, status_msg, filename: str, user_id=None) -> Optional[str]:
    """Fast direct download"""
    try:
        from plugins.download import active_tasks
        
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=20,
            ttl_dns_cache=300,
            force_close=False,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=None,
            connect=60,
            sock_read=120
        )
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*'
            }
            
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    print(f"HTTP {resp.status}")
                    return None
                
                total_size = int(resp.headers.get('content-length', 0))
                downloaded = 0
                start_time = time.time()
                
                # Ensure file can be written
                try:
                    async with aiofiles.open(output_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(Config.CHUNK_SIZE):
                            if user_id and user_id in active_tasks and active_tasks[user_id].get('cancelled'):
                                return None
                            
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress
                            if status_msg:
                                try:
                                    await progress_for_pyrogram(
                                        downloaded,
                                        total_size,
                                        "Downloading",
                                        status_msg,
                                        start_time,
                                        filename
                                    )
                                except:
                                    pass
                except Exception as write_error:
                    print(f"Write error: {write_error}")
                    return None
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path
                return None
                
    except Exception as e:
        print(f"Direct download error: {e}")
        return None
