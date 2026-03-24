import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import json
import datetime
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1478018060840468601  # replace

# Google setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)

client_sheet = gspread.authorize(creds)

# IMPORTANT: replace with your sheet name
sheet = client_sheet.open("Good News (Responses)").sheet1


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def load_used():
    try:
        with open("used.json", "r") as f:
            return json.load(f)
    except:
        return {"used": []}


def save_used(data):
    with open("used.json", "w") as f:
        json.dump(data, f, indent=4)

async def post_news():
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ Channel not found.")
        return

    rows = sheet.get_all_records()

    if not rows:
        print("❌ No data found.")
        return

    data = load_used()
    used = data["used"]

    # Get unused news
    unused = [row["Good News"] for row in rows if row["Good News"] not in used]

    # If everything has been used → reset
    if not unused:
        print("🔄 Resetting used list")
        data["used"] = []
        save_used(data)
        unused = [row["Good News"] for row in rows]

    # Pick one
    news = random.choice(unused)

    # Mark as used
    data["used"].append(news)
    save_used(data)

    emojis = ["🌱", "🐶", "🌍", "✨", "💛", "📰"]
    emoji = random.choice(emojis)

    embed = discord.Embed(
        title=f"{emoji} Good News of the Day",
        description=f"**Here's something positive today:**\n\n{news}",
        color=discord.Color.gold()
    )

    embed.timestamp = datetime.datetime.utcnow()

    today = datetime.datetime.now().strftime("%B %d, %Y")
    embed.set_footer(text=f"{today} • Good things are happening 💛")

    msg = await channel.send(embed=embed)

    await msg.add_reaction("💛")
    await msg.add_reaction("🌱")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(post_news, "cron", hour=9, minute=0)
    scheduler.start()

@bot.command()
async def postnow(ctx):
    await post_news()
    await ctx.send("✅ Posted today's good news!")

@bot.command()
async def test(ctx):
    await ctx.send("✅ Bot is working!")

@bot.event
async def on_message(message):
    print(f"SAW MESSAGE: {message.content}")
    await bot.process_commands(message)

bot.run(TOKEN)
