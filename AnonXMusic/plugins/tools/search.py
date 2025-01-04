from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import time
import threading
from .logging import LOGGER 
from AnonXMusic import app  # Importing the existing app


# Path to cookies file
cookies_file = "assets/cookies.txt"

# Function to search songs (You need to implement actual search logic)
def search_songs(query, offset=0, limit=10):
    # This should be replaced with actual search logic
    # Mocking search results with song names and durations
    return [(f"{query} Song {i+1 + offset}", f"{(i+1 + offset) * 60} seconds") for i in range(limit)]

# Function to download song from YouTube in M4A format
def download_song(song_name, cookies_file):
    fpath = f"{song_name}.m4a"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": fpath,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "prefer_ffmpeg": True,
        "postprocessors": [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                "preferredquality": "192",
                'audio_bitrate': '192k',
                'audio_channels': 2,
                'audio_sample_rate': '44100'
            }
        ],
        "cookiefile": cookies_file,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch:{song_name}"])
    except Exception as e:
        logging.error(f"Error downloading {song_name}: {e}")
        return None
    return fpath

# Function to delete file after 20 minutes
def delete_file_after_delay(file_path, delay=1200):
    time.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)

# Command handler for /find, /song, and /fsong
@app.on_message(filters.command(["find", "song", "fsong"], prefixes=["/", "!"]))
async def find(client, message):
    chat_id = message.chat.id
    try:
        query = message.text.split(maxsplit=1)[1]
    except IndexError:
        await client.send_message(chat_id, "Please provide a song name to search.")
        return

    songs = search_songs(query)

    buttons = [[InlineKeyboardButton(f"{duration} - {name}", callback_data=name)] for name, duration in songs]
    buttons.append([InlineKeyboardButton("Next Page", callback_data=f"next_{query}_10")])

    reply_markup = InlineKeyboardMarkup(buttons)

    await client.send_message(chat_id, "Select a song:", reply_markup=reply_markup)

# Callback query handler for inline buttons
@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data

    if data.startswith("next_"):
        parts = data.split("_")
        query = parts[1]
        offset = int(parts[2])

        songs = search_songs(query, offset=offset)
        buttons = [[InlineKeyboardButton(f"{duration} - {name}", callback_data=name)] for name, duration in songs]
        buttons.append([InlineKeyboardButton("Next Page", callback_data=f"next_{query}_{offset + 10}")])

        reply_markup = InlineKeyboardMarkup(buttons)

        await callback_query.message.edit_reply_markup(reply_markup=reply_markup)
    else:
        song_name = data
        logging.info(f"Downloading song: {song_name}")
        file_path = download_song(song_name, cookies_file)

        if file_path:
            logging.info(f"Sending file: {file_path}")
            await client.send_document(chat_id, document=file_path)
            threading.Thread(target=delete_file_after_delay, args=(file_path,)).start()
        else:
            logging.error(f"Failed to download {song_name}")
            await client.send_message(chat_id, f"Failed to download {song_name}. Please try again.")
