import os
from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from yt_dlp import YoutubeDL

app = Client(
    "vc_music_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)
vc = PyTgCalls(app)

def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'song.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "song.mp3"

@app.on_message(filters.command("start"))
async def start(_, m):
    bn = (await app.get_me()).username
    await m.reply_text(
        f"👋 Hello {m.from_user.mention}!\n"
        "Add me to a group and use `/play <song>`.\n"
        f"Try inline: `@{bn}`"
    )

@app.on_message(filters.new_chat_members)
async def welcome(_, m):
    for u in m.new_chat_members:
        await m.reply_text(
            f"🎉 Welcome {u.mention}!\n"
            "Use `/play <song name>` to play music in VC."
        )

@app.on_message(filters.command("play") & filters.group)
async def play(_, m):
    if len(m.command) < 2:
        return await m.reply_text("❗ Please include a song name or URL.")
    query = " ".join(m.command[1:])
    status = await m.reply_text(f"🔍 Searching for `{query}`...")
    with YoutubeDL({'quiet': True, 'skip_download': True, 'format': 'bestaudio'}) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        except Exception as e:
            return await status.edit(f"❌ Error: {e}")
    await status.edit(f"🎧 Playing: **{info['title']}**")
    download_audio(info['webpage_url'])
    await vc.join_group_call(m.chat.id, AudioPiped("song.mp3"))
    os.remove("song.mp3")

@app.on_inline_query()
async def inline(iq):
    bn = (await app.get_me()).username
    results = [
        InlineQueryResultArticle(
            title="➕ Add to Group",
            description="Invite me to your group",
            input_message_content=InputTextMessageContent("Use the button below to add the bot."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bn}?startgroup=true")]
            ])
        ),
        InlineQueryResultArticle(
            title="📜 How to Use",
            description="/play command guide",
            input_message_content=InputTextMessageContent("Use `/play <song name>` to play music in VC.")
        ),
        InlineQueryResultArticle(
            title="💠 Clone This Bot",
            description="Get your own copy",
            input_message_content=InputTextMessageContent("Fork and deploy your own from GitHub!")
        ),
    ]
    await iq.answer(results, cache_time=1)

vc.start()
app.run()
