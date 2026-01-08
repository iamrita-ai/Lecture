import aiohttp
import aiofiles
import asyncio
import os
import m3u8
from typing import Optional
import subprocess

async def download_m3u8_chunks(url: str, output_path: str, status_msg=None, filename="video") -> Optional[str]:
    """
    Download M3U8 video with proper chunking - Creates playable MP4
    """
    try:
        # Create downloads directory
        os.makedirs("downloads", exist_ok=True)
        
        if status_msg:
            await status_msg.edit_text(
                f"📥 **Downloading M3U8 Video**\n\n"
                f"`{filename}`\n\n"
                f"⏳ Fetching stream information..."
            )
        
        # Parse M3U8 playlist
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                playlist_content = await resp.text()
        
        playlist = m3u8.loads(playlist_content)
        
        # Get base URL
        base_url = url.rsplit('/', 1)[0] + '/'
        
        if status_msg:
            await status_msg.edit_text(
                f"📥 **Downloading M3U8 Video**\n\n"
                f"`{filename}`\n\n"
                f"📊 Found {len(playlist.segments)} segments\n"
                f"⏳ Downloading chunks..."
            )
        
        # Download all segments
        temp_dir = f"downloads/temp_{int(asyncio.get_event_loop().time())}"
        os.makedirs(temp_dir, exist_ok=True)
        
        segment_files = []
        
        async with aiohttp.ClientSession() as session:
            for idx, segment in enumerate(playlist.segments):
                segment_url = segment.uri if segment.uri.startswith('http') else base_url + segment.uri
                segment_path = f"{temp_dir}/segment_{idx:05d}.ts"
                
                try:
                    async with session.get(segment_url) as resp:
                        if resp.status == 200:
                            async with aiofiles.open(segment_path, 'wb') as f:
                                await f.write(await resp.read())
                            segment_files.append(segment_path)
                            
                            # Update progress every 10 segments
                            if status_msg and idx % 10 == 0:
                                progress = (idx / len(playlist.segments)) * 100
                                await status_msg.edit_text(
                                    f"📥 **Downloading M3U8 Video**\n\n"
                                    f"`{filename}`\n\n"
                                    f"📊 Progress: {progress:.1f}%\n"
                                    f"📦 Segments: {idx}/{len(playlist.segments)}"
                                )
                except Exception as e:
                    print(f"Segment {idx} download error: {e}")
        
        if status_msg:
            await status_msg.edit_text(
                f"🔄 **Converting to MP4**\n\n"
                f"`{filename}`\n\n"
                f"⏳ Merging {len(segment_files)} segments..."
            )
        
        # Merge segments using ffmpeg
        concat_file = f"{temp_dir}/concat.txt"
        async with aiofiles.open(concat_file, 'w') as f:
            for seg_file in segment_files:
                await f.write(f"file '{os.path.basename(seg_file)}'\n")
        
        # Convert to MP4
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
        
        if os.path.exists(output_path):
            return output_path
        return None
        
    except Exception as e:
        print(f"M3U8 Download Error: {e}")
        return None


async def download_m3u8_simple(url: str, output_path: str) -> Optional[str]:
    """Simple M3U8 download using ffmpeg directly"""
    try:
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
        
        if os.path.exists(output_path):
            return output_path
        return None
        
    except Exception as e:
        print(f"Simple M3U8 Download Error: {e}")
        return None
