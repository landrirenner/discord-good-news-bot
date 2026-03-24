import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
import csv
import io
import random
import json
import os
import datetime

# ========================
# CONFIG
# ========================

TOKEN = os.getenv("TOKEN")  # Railway uses this
CHANNEL_ID = 1478018060840468601  # REPLACE THIS

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTjUlb3ctSFl7MByRf4_8XTVqRaLdcrwfgUrG5UibJrwaSVBe3rjy41yFxxb3UxAs-cuHsoMUJn1-eI/pub?output=csv"  # from Google Sheets

# ========================
# BOT SETUP
# ========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ========================
# LOAD / SAVE USED NEWS
# ========================

def load_used():
    try:
        with open("used.json", "r") as f:
            return json.load(f)
    except:
        return {"used": []}


def save_used(data):
    with open("used.json", "w") as f:
        json.dump(data, f, indent=4)


# ========================
# GET DATA FROM GOOGLE SHEET
# ========================

def get_news_from_sheet():
    response = requests.get(CSV_URL)
    content = response.content.decode("utf-8")

    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    return rows


# ========================
# POST FUNCTION
# ========================

async def post_news():
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ Channel not found.")
        return

    rows = get_news_from_sheet()

    if not rows:
        print("❌ No data found.")
        return

    # 🔍 automatically detect the correct column (skip Timestamp)
    column_names = list(rows[0].keys())
    print("COLUMNS:", column_names)

    # usually the second column is your form response
    column_name = column_names[1]

    data = load_used()
    used = data["used"]

    # filter valid unused entries
    unused = [
        row[column_name]
        for row in rows
        if row[column_name] and row[column_name] not in used
    ]

    # reset if all used
    if not unused:
        print("🔄 Resetting used list")
        data["used"] = []
        save_used(data)
        unused = [
            row[column_name]
            for row in rows
            if row[column_name]
        ]

    news = random.choice(unused)

    if not rows:
        print("❌ No data found.")
        return

    data = load_used()
    used = data["used"]

    # filter unused
    unused = [row["Good News"] for row in rows if row["Good News"] not in used]

    # reset if all used
    if not unused:
        print("🔄 Resetting used list")
        data["used"] = []
        save_used(data)
        unused = [row["Good News"] for row in rows]

    news = random.choice(unused)

    # mark as used
    data["used"].append(news)
    save_used(data)

    # pretty embed ✨
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


# ========================
# EVENTS
# ========================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    scheduler = AsyncIOScheduler()

    # CHANGE TIME HERE (24hr format)
    scheduler.add_job(post_news, "cron", hour=13, minute=0)

    scheduler.start()


@bot.event
async def on_message(message):
    print(f"SAW MESSAGE: {message.content}")
    await bot.process_commands(message)


# ========================
# COMMANDS
# ========================

@bot.command()
async def test(ctx):
    await ctx.send("✅ Bot is working!")


@bot.command()
async def postnow(ctx):
    try:
        await post_news()
        await ctx.send("✅ Posted today's good news!")
    except Exception as e:
        print("ERROR:", e)
        await ctx.send(f"❌ Error: {e}")

# ========================
# RUN BOT
# ========================

bot.run(TOKEN)
