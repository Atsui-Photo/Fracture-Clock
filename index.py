import discord
from discord import app_commands
import time
import asyncio
from datetime import datetime
import os

# ===== KEEP ALIVE (RENDER FIX) =====
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ===== TOKEN =====
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ===== SETTINGS =====
SCALE = 365 / 12
START_REAL = datetime.fromisoformat("2026-03-19T02:00:00-04:00").timestamp()
START_YEAR = 2065

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

# ===== HELPERS =====
def is_leap_year(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def get_month_day(day_of_year, year):
    month_lengths = [
        31,
        29 if is_leap_year(year) else 28,
        31,30,31,30,31,31,30,31,30,31
    ]

    month = 0
    while day_of_year >= month_lengths[month]:
        day_of_year -= month_lengths[month]
        month += 1

    return month, day_of_year + 1

def make_bar(percent):
    total = 10
    filled = round((percent / 100) * total)
    return "█" * filled + "░" * (total - filled)

def format_time(seconds):
    seconds = max(0, int(seconds))
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{d}d {h}h {m}m {s}s"

# ===== MAIN LOGIC =====
def get_game_data():
    now = time.time()
    real_elapsed = now - START_REAL
    game_elapsed = real_elapsed * SCALE

    seconds_per_day = 86400

    year = START_YEAR
    remaining = game_elapsed

    while True:
        days_in_year = 366 if is_leap_year(year) else 365
        seconds_in_year = days_in_year * seconds_per_day

        if remaining >= seconds_in_year:
            remaining -= seconds_in_year
            year += 1
        else:
            break

    days_in_year = 366 if is_leap_year(year) else 365
    seconds_in_year = days_in_year * seconds_per_day

    day_of_year = int(remaining // seconds_per_day)
    month, day = get_month_day(day_of_year, year)

    seconds_today = int(remaining % seconds_per_day)
    hours = seconds_today // 3600
    minutes = (seconds_today % 3600) // 60
    seconds = seconds_today % 60

    total_days = game_elapsed / seconds_per_day
    days_per_turn = 365 / 4
    seconds_per_turn = days_per_turn * seconds_per_day
    turn = int(total_days // days_per_turn) + 1

    # Progress
    year_progress = (remaining / seconds_in_year) * 100
    turn_progress = ((game_elapsed % seconds_per_turn) / seconds_per_turn) * 100

    # Countdown
    seconds_to_year = (seconds_in_year - remaining) / SCALE
    seconds_to_turn = (seconds_per_turn - (game_elapsed % seconds_per_turn)) / SCALE

    return {
        "year": year,
        "turn": turn,
        "date": f"{MONTHS[month]} {day}",
        "time": f"{hours:02}:{minutes:02}:{seconds:02}",
        "year_bar": make_bar(year_progress),
        "turn_bar": make_bar(turn_progress),
        "year_countdown": format_time(seconds_to_year),
        "turn_countdown": format_time(seconds_to_turn)
    }

# ===== EMBED BUILDER =====
def build_embed(data):
    return discord.Embed(
        title="🌍 Game Time",
        description=(
            f"**Year {data['year']} | Turn {data['turn']}**\n"
            f"{data['date']}\n"
            f"`{data['time']}`\n\n"

            f"**Year Progress ({data['year_percent']})**\n"
            f"{data['year_bar']}\n"
            f"⏳ Next Year in: {data['year_countdown']}\n\n"

            f"**Turn Progress ({data['turn_percent']})**\n"
            f"{data['turn_bar']}\n"
            f"⏳ Next Turn in: {data['turn_countdown']}"
        )
    )

# ===== SLASH COMMAND =====
@tree.command(name="time", description="Live game time (updates every 2 seconds)")
async def time_command(interaction: discord.Interaction):
    await interaction.response.defer()

    msg = await interaction.followup.send(embed=build_embed(get_game_data()))

    while True:
        await asyncio.sleep(2)

        try:
            await msg.edit(embed=build_embed(get_game_data()))
        except:
            break

# ===== READY =====
@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

# ===== START =====
keep_alive()
client.run(TOKEN)
