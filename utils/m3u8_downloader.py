import aiohttp
import aiofiles
import asyncio
import os
import re
from typing import Optional

async def download_m3u8_video(url: str, output_path: str, status_msg=None, filename="video") -> Optional[str]:
    """
    Download M3U8 video with proper quality selection and chunk handling
    """
    try:
        os.makedirs("downloads", exist_ok=True)
        
        if status_msg:
            await status_msg.edit_text(
                f"📥 **Downloading M3U8**\n\n"
                f"`{filename}`\n\n"
                f"⏳ Fetching playlist..."
            )
        
        async with aiohttp.ClientSession() as session:
            # Step 1: Get master playlist
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"Failed to get master playlist: {resp.status}")
                    return None
                
                master_content = await resp.text()
                print(f"Master Playlist:\n{master_content[:500]}")
            
            # Step 2: Parse playlist
            base_url = url.rsplit('/', 1)[0] + '/'
            
            # Check if it's a master playlist or direct media playlist
            if '#EXT-X-STREAM-INF' in master_content:
                # Master playlist - select quality
                print("Master playlist detected, selecting quality...")
                
                # Parse quality options
                lines = master_content.split('\n')
                playlists = []
                
                for i, line in enumerate(lines):
                    if line.startswith('#EXT-X-STREAM-INF'):
                        # Get resolution/bandwidth
                        resolution = None
                        if 'RESOLUTION=' in line:
                            resolution = line.split('RESOLUTION=')[1].split(',')[0]
                        
                        # Get URL from next line
                        if i + 1 < len(lines):
                            playlist_url = lines[i + 1].strip()
                            if not playlist_url.startswith('http'):
                                playlist_url = base_url + playlist_url
                            
                            playlists.append({
                                'url': playlist_url,
                                'resolution': resolution
                            })
                
                # Select best quality (last one usually)
                if playlists:
                    selected = playlists[-1]
                    print(f"Selected quality: {selected['resolution']} - {selected['url']}")
                    
                    # Get actual media playlist
                    async with session.get(selected['url']) as resp:
                        if resp.status != 200:
                            return None
                        media_content = await resp.text()
                        media_base_url = selected['url'].rsplit('/', 1)[0] + '/'
                else:
                    print("No playlists found in master")
                    return None
            else:
                # Direct media playlist
                print("Direct media playlist")
                media_content = master_content
                media_base_url = base_url
            
            # Step 3: Parse media playlist and get segments
            print(f"Media Playlist:\n{media_content[:500]}")
            
            segments = []
            lines = media_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # This is a segment URL
                    if not line.startswith('http'):
                        segment_url = media_base_url + line
                    else:
                        segment_url = line
                    segments.append(segment_url)
            
            if not segments:
                print("No segments found")
                return None
            
            print(f"Found {len(segments)} segments")
            
            if status_msg:
                await status_msg.edit_text(
                    f"📥 **Downloading M3U8**\n\n"
                    f"`{filename}`\n\n"
                    f"📦 Segments: {len(segments)}\n"
                    f"⏳ Downloading..."
                )
            
            # Step 4: Download segments
            temp_dir = f"downloads/temp_{int(asyncio.get_event_loop().time())}"
            os.makedirs(temp_dir, exist_ok=True)
            
            segment_files = []
            
            for idx, seg_url in enumerate(segments):
                try:
                    seg_path = f"{temp_dir}/seg_{idx:05d}.ts"
                    
                    async with session.get(seg_url) as resp:
                        if resp.status == 200:
                            async with aiofiles.open(seg_path, 'wb') as f:
                                await f.write(await resp.read())
                            segment_files.append(seg_path)
                            
                            # Update progress every 10 segments
                            if status_msg and idx % 10 == 0:
                                progress = (idx / len(segments)) * 100
                                await status_msg.edit_text(
                                    f"📥 **Downloading M3U8**\n\n"
                                    f"`{filename}`\n\n"
                                    f"📊 Progress: {progress:.1f}%\n"
                                    f"📦 Segments: {idx}/{len(segments)}"
                                )
                except Exception as e:
                    print(f"Segment {idx} failed: {e}")
            
            if not segment_files:
                print("No segments downloaded")
                return None
            
            # Step 5: Merge segments using ffmpeg
            if status_msg:
                await status_msg.edit_text(
                    f"🔄 **Converting to MP4**\n\n"
                    f"`{filename}`\n\n"
                    f"⏳ Merging {len(segment_files)} segments..."
                )
            
            # Create concat file
            concat_file = f"{temp_dir}/concat.txt"
            async with aiofiles.open(concat_file, 'w') as f:
                for seg_file in segment_files:
                    await f.write(f"file '{os.path.basename(seg_file)}'\n")
            
            # Use ffmpeg to concat
            import subprocess
            
            command = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                '-y',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=temp_dir,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            await process.communicate()
            
            # Cleanup temp files
            for seg_file in segment_files:
                try:
                    os.remove(seg_file)
                except:
                    pass
            
            try:
                os.remove(concat_file)
                os.rmdir(temp_dir)
            except:
                pass
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Download successful: {output_path}")
                return output_path
            else:
                print("Output file is empty or doesn't exist")
                return None
                
    except Exception as e:
        print(f"M3U8 Download Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def download_m3u8_simple(url: str, output_path: str) -> Optional[str]:
    """Simple fallback using ffmpeg directly"""
    try:
        import subprocess
        
        command = [
            'ffmpeg',
            '-i', url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            '-y',
            output_path
        ]
        
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
        print(f"Simple M3U8 Error: {e}")
        return None
