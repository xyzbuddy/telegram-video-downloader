# =====================================================================
# Telegram Private Video Downloader
# =====================================================================
# This script logs into Telegram using your API ID & Hash and
# downloads video files from a designated channel or chat.
# It automatically reads configurations from a local '.env' file.
# =====================================================================

import os
import sys
from dotenv import load_dotenv
from telethon import TelegramClient

# Load configuration from .env file
load_dotenv()

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

# Channel ID can be a numeric ID (like -100xxxxxxxxxx) or a public username (like 'telegram_username')
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

# A session file named 'session.session' will be created locally to store login token
client = TelegramClient(
    "session",
    api_id,
    api_hash
)

# ---------------------------------------------------------------------
# Downloader Main Function
# ---------------------------------------------------------------------

async def main():
    downloaded_size = 0
    download_count = 0

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
        # Resolve target entity/channel
        entity = await client.get_entity(channel_id)
        channel_title = getattr(entity, 'title', channel_id)
        print(f"Successfully connected! Target: '{channel_title}'")
    except Exception as e:
        print(f"\n[ERROR] Failed to connect or locate target channel/chat.")
        print(f"Detail: {e}")
        print("Please check your CHANNEL_ID, internet connection, or if your user session has access to it.")
        return

    print("\nScanning messages (oldest to newest)...")
    print("-" * 50)

    # Read Messages
    async for message in client.iter_messages(
        entity,
        reverse=True
    ):
        # Skip Non-Videos
        if not message.video:
            continue

        file_size = getattr(message.file, "size", 0)

        # Stop if downloading the next file exceeds the size limit
        if downloaded_size + file_size > MAX_TOTAL_SIZE:
            print("\n" + "=" * 50)
            print(f"LIMIT REACHED: Download stopped at {downloaded_size / (1024**3):.2f} GB to prevent exceeding the limit.")
            break

        # Display details
        video_name = getattr(message.file, "name", f"video_{message.id}.mp4") or f"video_{message.id}.mp4"
        size_mb = file_size / (1024 * 1024)

        print(f"\n[{download_count + 1}] Downloading Video (ID: {message.id})")
        print(f"  Name: {video_name}")
        print(f"  Size: {size_mb:.2f} MB")

        # Download Video file
        try:
            output_path = os.path.join(downloads_dir, "")
            await message.download_media(file=output_path)
            downloaded_size += file_size
            download_count += 1
            print(f"  Status: Downloaded successfully!")
        except Exception as e:
            print(f"  Status: Failed to download. Error: {e}")

    print("\n" + "=" * 50)
    print("Download Summary:")
    print(f"  Total Videos Downloaded : {download_count}")
    print(f"  Total Size Downloaded   : {downloaded_size / (1024**3):.2f} GB")
    print("=" * 50 + "\n")

# ---------------------------------------------------------------------
# Start Script
# ---------------------------------------------------------------------

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
