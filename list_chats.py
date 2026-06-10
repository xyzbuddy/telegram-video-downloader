# =====================================================================
# Telegram Chat/Channel ID Lister
# =====================================================================
# This utility script lists all the channels, groups, and chats
# you are part of, along with their unique IDs.
# You can copy the target ID from here and paste it into your '.env'.
# =====================================================================

import os
import sys
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User

# Load configuration from .env file
load_dotenv()

# ---------------------------------------------------------------------
# Configuration Reading and Validation
# ---------------------------------------------------------------------

api_id_raw = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

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

# Initialize Telegram client using the same local session
client = TelegramClient(
    "session",
    api_id,
    api_hash
)

# ---------------------------------------------------------------------
# Main Dialog Fetcher
# ---------------------------------------------------------------------

async def main():
    print("\nConnecting to Telegram and fetching chats...")
    print("=" * 70)
    print(f"{'Chat/Channel Name':<35} | {'ID':<15} | {'Type':<12}")
    print("=" * 70)

    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            name = dialog.name or "Unknown Name"
            
            # Determine the type of chat/channel
            if isinstance(entity, Channel):
                if entity.broadcast:
                    chat_type = "Channel"
                else:
                    chat_type = "MegaGroup"
            elif isinstance(entity, Chat):
                chat_type = "Group"
            elif isinstance(entity, User):
                if entity.bot:
                    chat_type = "Bot"
                else:
                    chat_type = "User"
            else:
                chat_type = "Other"

            # Clean name linebreaks for printing
            display_name = name.replace("\n", " ").strip()
            print(f"{display_name[:35]:<35} | {dialog.id:<15} | {chat_type:<12}")
            
    except Exception as e:
        print(f"\n[ERROR] Failed to fetch dialogs. Detail: {e}")
        return

    print("=" * 70)
    print("\nInstructions:")
    print("1. Find your target channel/group in the list above.")
    print("2. Copy the corresponding ID (it will look like a long negative number, e.g. -100xxxxxxxxxx).")
    print("3. Open your '.env' file, set it as: CHANNEL_ID=copied_id_here")
    print("4. Save the '.env' file and run 'python downloader.py' to start downloading.\n")

# ---------------------------------------------------------------------
# Start Script
# ---------------------------------------------------------------------

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
