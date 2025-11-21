import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Discord bot with intents
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Bot startup event
@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info('Bot is ready for moderation')

# Welcome message on member join
@bot.event
async def on_member_join(member):
    guild = member.guild
    logger.info(f'{member} has joined {guild.name}')

# Message moderation
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    logger.info(f'{message.author}: {message.content}')
    await bot.process_commands(message)

# Moderation commands
@bot.command(name='warn')
async def warn_user(ctx, member: discord.Member, *, reason='No reason provided'):
    await ctx.send(f'{member} has been warned. Reason: {reason}')
    logger.warning(f'{member} warned by {ctx.author}. Reason: {reason}')

@bot.command(name='kick')
async def kick_user(ctx, member: discord.Member, *, reason='No reason provided'):
    try:
        await member.kick(reason=reason)
        await ctx.send(f'{member} has been kicked. Reason: {reason}')
        logger.info(f'{member} kicked by {ctx.author}. Reason: {reason}')
    except discord.Forbidden:
        await ctx.send('I do not have permission to kick this user.')

@bot.command(name='ban')
async def ban_user(ctx, member: discord.Member, *, reason='No reason provided'):
    try:
        await member.ban(reason=reason)
        await ctx.send(f'{member} has been banned. Reason: {reason}')
        logger.info(f'{member} banned by {ctx.author}. Reason: {reason}')
    except discord.Forbidden:
        await ctx.send('I do not have permission to ban this user.')

@bot.command(name='mute')
async def mute_user(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
    if not muted_role:
        muted_role = await ctx.guild.create_role(name='Muted')
    await member.add_roles(muted_role)
    await ctx.send(f'{member} has been muted.')
    logger.info(f'{member} muted by {ctx.author}')

@bot.command(name='unmute')
async def unmute_user(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f'{member} has been unmuted.')
        logger.info(f'{member} unmuted by {ctx.author}')
    else:
        await ctx.send(f'{member} is not muted.')

@bot.command(name='ping')
async def ping(ctx):
    latency = bot.latency * 1000
    await ctx.send(f'Pong! Latency: {latency:.2f}ms')

@bot.command(name='status')
async def status(ctx):
    await ctx.send('Bot is online and operational!')

if __name__ == '__main__':
    logger.info('Starting Discord bot...')
    bot.run(BOT_TOKEN)
