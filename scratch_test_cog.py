import asyncio
import discord
from discord.ext import commands

async def main():
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)
    try:
        await bot.load_extension("cogs.yardim_bekleme")
        print("yardim_bekleme loaded successfully!")
    except Exception as e:
        print(f"Error loading yardim_bekleme: {e}")

asyncio.run(main())
