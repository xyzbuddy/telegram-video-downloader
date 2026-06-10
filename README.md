# Telegram Private Video Downloader 📥

An automated, high-speed Python script to download videos from specific Telegram channels or chats directly to your local machine, using the official Telethon library.

This repository is designed to be easily cloneable, customizable, and safe (preventing sensitive credentials from leaking to public repositories).

---

## Features

- **High-Speed Decryption**: Automatically uses `cryptg` (a C-extension) to decrypt files. This yields speeds that are up to 5x-10x faster than default pure-Python decryption.
- **Concurrently Download (Parallel)**: Downloads up to 3 videos simultaneously using an asynchronous Semaphore. This maximizes bandwidth utilization without triggering Telegram's API rate limiting (`FloodWaitError`).
- **Live Progress Percentage**: Shows real-time progress update percentages (`10%`, `20%`, ..., `100%`) for each running download.
- **Automatic Video Filtering**: Automatically identifies and downloads video messages from the specified target chat/channel.
- **Sequential Scan with Limit Safety**: Scans chronological channel history (from oldest to newest) and budgets files beforehand to respect your maximum size limit (default 20 GB).
- **Configuration Security**: Keeps secrets like Telegram credentials and sessions separate from the code using environment variables (`.env`).
- **Resilient**: Robust logging and error handling for failed downloads.

---

## Prerequisites

Before running the script, make sure you have:
1. **Python 3.7 or higher** installed on your system.
2. A **Telegram account** to authenticate the client.
3. Your Telegram **API ID** and **API Hash**. If you don't have them:
   - Go to [my.telegram.org](https://my.telegram.org) and log in with your phone number.
   - Go to **API development tools**.
   - Create a new application (fill out the form; name/short name can be anything).
   - Copy the `api_id` and `api_hash` values.

---

## Quick Start Setup

### Step 1: Clone the Repository & Install Dependencies
First, clone the repository to your local machine and install the required library packages (which include the speed-up libraries):
```bash
git clone https://github.com/xyzbuddy/telegram-video-downloader.git
cd telegram-video-downloader
pip install -r requirements.txt
```

### Step 2: Set up Initial API Credentials
Copy the template configuration file to a new file named `.env`:
```bash
# On Linux/macOS
cp .env.example .env

# On Windows (Command Prompt)
copy .env.example .env

# On Windows (PowerShell)
Copy-Item .env.example .env
```

Open the `.env` file in a text editor and fill in your Telegram API details (leave `CHANNEL_ID` blank or as is for now):
```ini
API_ID=your_api_id_here
API_HASH=your_api_hash_here
```

### Step 3: Find Channel ID & First-Time Login
Now, run the chat lister script. This will connect to Telegram and guide you through the first-time authentication:
```bash
python list_chats.py
```

*During this step, the terminal will ask for your login details:*
- **Phone Number**: Enter your phone number with your **country code** prefix included (e.g., `+88017XXXXXXXX` or `+123456789`). The country code prefix is mandatory.
- **Login Code**: Enter the numeric login code sent to your Telegram app.
- **2-Factor Authentication (2FA) Password**: If you have 2FA enabled on your Telegram account, the terminal will ask for your password. **Note**: As you type your password, the characters will **not be visible in the terminal** (no letters, dots, or asterisks will show) for security. Type it blindly and press Enter.

Once logged in, a secure session file named `session.session` will be saved in your project folder, and the script will list all the channels and groups you belong to. Copy the ID of the channel you want to download from (usually starts with `-100`).

### Step 4: Configure the Channel ID
Open `.env` in a text editor again, and set your `CHANNEL_ID` to the copied value:
```ini
CHANNEL_ID=-100xxxxxxxxxx
```
Save and close the `.env` file.

### Step 5: Start Downloading
You are now ready to download the videos! Since you logged in during Step 3, you won't need to log in again. Simply run:
```bash
python downloader.py
```

---

## Customizing Limits

You can customize the maximum download size and directory inside the `.env` file:

- **`MAX_TOTAL_SIZE`**: The maximum limit (in bytes) of files to download in a single execution.
  - *Example (5 GB Limit)*: `MAX_TOTAL_SIZE=5368709120` (i.e. `5 * 1024 * 1024 * 1024`)
- **`DOWNLOADS_DIR`**: The directory name where files are saved (defaults to `downloads`).

---

## Security Best Practices

⚠️ **Crucial Security Reminder**:
- **Never** share or upload your `.env` file or `session.session` files. These files contain login tokens and credentials that grant full API access to your Telegram account.
- This repository is configured with a `.gitignore` file that automatically excludes these files from git commits. Keep it that way.

---

## Troubleshooting

- **Connection / Authentication Error**: Check if your `API_ID` and `API_HASH` are correct, or verify if your network has blocked Telegram services.
- **Channel Access Denied**: Ensure that the Telegram account you are logging in with has joined or has read permission on the target channel/chat.
- **SQLite Error**: If you encounter an error involving `session.session` database lock, close any other terminal running the downloader or delete the `session.session` file and log in again.
