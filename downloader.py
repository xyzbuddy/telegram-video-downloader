# =====================================================================
# Telegram Private Video Downloader
# =====================================================================
# This script logs into Telegram using your API ID & Hash and
# downloads video files from a designated channel or chat.
# It automatically reads configurations from a local '.env' file.
# =====================================================================

import os
import sys
import re
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

# Load configuration from .env file
load_dotenv(override=True)

# ---------------------------------------------------------------------
# Configuration Reading and Validation
# ---------------------------------------------------------------------

api_id_raw = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
channel_id_raw = os.getenv("CHANNEL_ID")
downloads_dir = os.getenv("DOWNLOADS_DIR", "downloads")
max_total_size_raw = os.getenv("MAX_TOTAL_SIZE", str(20 * 1024 * 1024 * 1024))

# Validating API Credentials
if not api_id_raw or not api_hash or api_hash == "your_api_hash_here":
    print("\n[ERROR] API_ID or API_HASH is missing or has placeholder values.")
    print("Please copy '.env.example' to '.env', fill in your Telegram API credentials, and try again.")
    print("Get your API credentials from: https://my.telegram.org")
    sys.exit(1)

try:
    api_id = int(api_id_raw)
except ValueError:
    print(f"\n[ERROR] API_ID must be an integer. Got: '{api_id_raw}'")
    sys.exit(1)

# Validating Channel ID
if not channel_id_raw:
    print("\n[ERROR] CHANNEL_ID is not configured in your .env file.")
    sys.exit(1)

try:
    if channel_id_raw.startswith("-") or channel_id_raw.isdigit():
        channel_id = int(channel_id_raw)
    else:
        channel_id = channel_id_raw
except ValueError:
    channel_id = channel_id_raw

# Validating Max Size Limit
try:
    MAX_TOTAL_SIZE = int(max_total_size_raw)
except ValueError:
    print(f"\n[WARNING] Invalid MAX_TOTAL_SIZE value. Using default of 20 GB.")
    MAX_TOTAL_SIZE = 20 * 1024 * 1024 * 1024

# ---------------------------------------------------------------------
# Telegram Client Initialization
# ---------------------------------------------------------------------

client = TelegramClient(
    "session",
    api_id,
    api_hash
)

# Limit concurrent downloads to 3 files to avoid FloodWaitError (Telegram rate-limits)
DOWNLOAD_SEMAPHORE = asyncio.Semaphore(3)

# ---------------------------------------------------------------------
# Download Progress Helper
# ---------------------------------------------------------------------

def create_progress_callback(video_id, video_name, size_mb):
    """
    Creates a callback function to track and display download percentage.
    """
    last_percent = -5  # Force print at 0%

    def progress_callback(received, total):
        nonlocal last_percent
        if not total:
            return
        
        percent = int((received / total) * 100)
        
        # Only print updates every 10% change to keep console clean during concurrency
        if percent - last_percent >= 10 or percent == 100:
            last_percent = percent
            print(f"  -> [Video ID {video_id}] {video_name} ({size_mb:.1f} MB) - {percent}% downloaded")
            
    return progress_callback

# ---------------------------------------------------------------------
# Single File Download Worker
# ---------------------------------------------------------------------

def clean_filename(name):
    """
    Remove invalid characters from filename and clean extra whitespaces.
    """
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    cleaned = re.sub(r'\s+', " ", cleaned).strip()
    return cleaned

async def download_worker(message, index, total_count):
    """
    Asynchronous task worker to download a single file with concurrency control.
    """
    file_size = getattr(message.file, "size", 0)
    size_mb = file_size / (1024 * 1024)

    # 1. Try to get title from message text/caption
    video_name = ""
    if message.text:
        first_line = message.text.split("\n")[0].strip()
        if first_line:
            video_name = clean_filename(first_line)[:50]

    # 2. Fall back to message.file.name
    if not video_name and getattr(message.file, "name", None):
        video_name = clean_filename(message.file.name)

    # 3. Fall back to date/time format (e.g. video_YYYYMMDD_HHMMSS.mp4)
    if not video_name:
        msg_date = message.date
        date_str = msg_date.strftime("%Y%m%d_%H%M%S")
        video_name = f"video_{date_str}"

    # Ensure correct extension (.mp4 or other original extension)
    ext = getattr(message.file, "ext", ".mp4")
    if not ext.startswith("."):
        ext = f".{ext}"
    if not video_name.lower().endswith(ext.lower()):
        video_name = f"{video_name}{ext}"

    async with DOWNLOAD_SEMAPHORE:
        print(f"\n[Queue {index}/{total_count}] Starting: {video_name} (ID: {message.id})")
        
        progress_cb = create_progress_callback(message.id, video_name, size_mb)
        
        try:
            output_path = os.path.join(downloads_dir, video_name)
            await message.download_media(
                file=output_path,
                progress_callback=progress_cb
            )
            print(f"✓ [Finished] Video ID: {message.id} ({video_name})")
            return True
        except Exception as e:
            print(f"✗ [Failed] Video ID: {message.id} ({video_name}). Error: {e}")
            return False

# ---------------------------------------------------------------------
# Downloader Main Function
# ---------------------------------------------------------------------

async def main():
    # Ensure downloads directory exists
    os.makedirs(downloads_dir, exist_ok=True)

    print("\n" + "=" * 50)
    print("Telegram Private Video Downloader")
    print("=" * 50)
    print(f"Target Channel/Chat : {channel_id}")
    print(f"Output Directory    : {downloads_dir}/")
    print(f"Max Download Limit  : {MAX_TOTAL_SIZE / (1024**3):.2f} GB")
    print("Connecting to Telegram...")
    
    try:
        entity = await client.get_entity(channel_id)
        channel_title = getattr(entity, 'title', channel_id)
        print(f"Successfully connected! Target: '{channel_title}'")
    except Exception as e:
        print(f"\n[ERROR] Failed to connect or locate target channel/chat.")
        print(f"Detail: {e}")
        print("Please check your CHANNEL_ID, internet connection, or if your user session has access to it.")
        return

    print("\nScanning messages and applying size budget...")
    print("-" * 50)

    download_queue = []
    total_scanned_size = 0
    limit_reached = False

    # Read Messages and calculate sizes first
    async for message in client.iter_messages(
        entity,
        reverse=True
    ):
        if not message.video:
            continue

        file_size = getattr(message.file, "size", 0)

        # Stop queueing if it goes over size budget
        if total_scanned_size + file_size > MAX_TOTAL_SIZE:
            limit_reached = True
            break

        download_queue.append(message)
        total_scanned_size += file_size

    total_files = len(download_queue)
    print(f"Found {total_files} videos to download.")
    print(f"Total size budget: {total_scanned_size / (1024**3):.2f} GB")
    
    if limit_reached:
        print("Note: Stop limit reached during scan. Some newer files were excluded to stay under limits.")

    if not download_queue:
        print("No videos found to download.")
        return

    print("\nStarting Parallel Downloads (Max 3 concurrent)...")
    print("-" * 50)

    # Spawn all download workers in parallel
    tasks = [
        download_worker(message, idx + 1, total_files)
        for idx, message in enumerate(download_queue)
    ]
    
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for r in results if r)

    print("\n" + "=" * 50)
    print("Download Summary:")
    print(f"  Total Videos Checked    : {total_files}")
    print(f"  Successfully Downloaded : {success_count}")
    print(f"  Failed Downloads        : {total_files - success_count}")
    print(f"  Total Size Budgeted     : {total_scanned_size / (1024**3):.2f} GB")
    print("=" * 50 + "\n")

# ---------------------------------------------------------------------
# Start Script
# ---------------------------------------------------------------------

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
