from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from io import BytesIO
from youtube_search import YoutubeSearch
from AnonXMusic import app
import time
import requests

cookies_file = "assets/cookies.txt"

# Function to convert time to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))

# Command handler for /find, /song, and /fsong
@app.on_message(filters.command(["find", "song", "fsong"], prefixes=["/", "!"]))
async def find(client, message):
    chat_id = message.chat.id
    try:
        query = " ".join(message.command[1:])
        if not query:
            await client.send_message(chat_id, "Please provide a song name to search.")
            return
    except IndexError:
        await client.send_message(chat_id, "Please provide a song name to search.")
        return

    try:
        results = YoutubeSearch(query, max_results=5).to_dict()
        if not results:
            raise Exception("No results found")

        buttons = []
        for result in results:
            title = result['title'][:40]
            duration = result['duration']
            buttons.append([InlineKeyboardButton(f"• {duration} {title}", callback_data=result['url_suffix'])])

        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(chat_id, "Select a song:", reply_markup=reply_markup)
    except Exception as e:
        await client.send_message(chat_id, "**😴 Song not found on YouTube.**\n\n» Please check the spelling and try again!")
        print(str(e))

# Callback query handler for inline buttons
@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    url_suffix = data

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "cookiefile": cookies_file,  # Use cookies.txt for authentication
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
                "preferredquality": "3200000"
            }
        ],
    }

    try:
        link = f"https://youtube.com{url_suffix}"
        await callback_query.message.edit_text("» Downloading...\n\nPlease wait...")

        # Download and convert video to audio in memory
        audio_data = BytesIO()

        def hook(d):
            if d['status'] == 'finished':
                with open(d['filename'], 'rb') as f:
                    audio_data.write(f.read())
                audio_data.seek(0)

        ydl_opts['progress_hooks'] = [hook]
        ydl_opts['outtmpl'] = '%(id)s.%(ext)s'  # Temporary filename

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            title = info_dict.get('title', 'Unknown title')
            duration = info_dict.get('duration', 0)
            views = info_dict.get('view_count', 0)
            thumbnail_url = info_dict.get('thumbnail', None)
        if thumbnail_url:
            thumbnail_data = requests.get(thumbnail_url).content
            thumbnail = BytesIO(thumbnail_data)
        else:
            thumbnail = None

        caption = f"<blockquote><b>Title:</b> {title}\n<b>Duration:</b> {time.strftime('%H:%M:%S', time.gmtime(duration))}\n<b>Views:</b> {views}\n<b>Requested by:</b> {callback_query.from_user.mention}</blockquote>"

        await client.send_audio(
            chat_id,
            audio=audio_data,
            caption=caption,
            performer="ʜɪɴ͟ᴀᴛᴀ ꭙ ͟ᴍᴜsɪ͟ᴄ🌸",
            title=title,
            duration=duration,
            file_name=f"{title}.m4a",
            thumb=thumbnail
        )

        audio_data.close()  # Close the BytesIO object when done

    except Exception as e:
        await client.send_message(chat_id, f"» Downloading error: {e}")
        print(e)