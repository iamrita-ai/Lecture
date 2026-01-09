async def download_file(url, filename, status_msg, action="Downloading", user_id=None):
    """Download file with M3U8 support"""
    try:
        clean_name = clean_filename(filename)
        
        # Check if M3U8
        is_m3u8 = '.m3u8' in url.lower()
        
        if not any(clean_name.endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.pdf', '.mov']):
            if '.pdf' in url.lower():
                clean_name += '.pdf'
            else:
                clean_name += '.mp4'
        
        file_path = f"downloads/{clean_name}"
        
        os.makedirs("downloads", exist_ok=True)
        
        if is_m3u8:
            print(f"Downloading M3U8: {url}")
            # Use M3U8 downloader
            from utils.m3u8_downloader import download_m3u8_video, download_m3u8_simple
            
            result = await download_m3u8_video(url, file_path, status_msg, filename)
            
            if not result:
                # Try simple method
                print("Trying simple M3U8 method...")
                result = await download_m3u8_simple(url, file_path)
            
            return result
        else:
            # Regular download
            print(f"Downloading regular file: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3600)) as resp:
                    if resp.status == 200:
                        total_size = int(resp.headers.get('content-length', 0))
                        downloaded = 0
                        start_time = time.time()
                        
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in resp.content.iter_chunked(Config.CHUNK_SIZE):
                                if user_id and user_id in active_tasks and active_tasks[user_id]['cancelled']:
                                    return None
                                
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                await progress_for_pyrogram(
                                    downloaded, 
                                    total_size, 
                                    action, 
                                    status_msg, 
                                    start_time, 
                                    filename
                                )
                        
                        return file_path
                    else:
                        print(f"Download failed: Status {resp.status}")
                        return None
                    
    except Exception as e:
        print(f"Download error for {filename}: {e}")
        import traceback
        traceback.print_exc()
        return None
