import discord
from discord.ext import commands
import logging
import os
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('bot_logs.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

user_warnings = {}
mod_logs = []

def log_action(action_type, user, moderator, reason, details=None):
    log_entry = {'timestamp': datetime.now().isoformat(), 'action': action_type, 'user': str(user), 'moderator': str(moderator) if moderator else 'System', 'reason': reason, 'details': details}
    mod_logs.append(log_entry)
    logger.info(f"MOD: {action_type} on {user} - {reason}")
    with open('moderation_logs.json', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

@bot.event
async def on_ready():
    logger.info(f'Bot logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name='!help'))

@bot.event
async def on_member_join(member):
    logger.info(f'Member joined: {member}')
    log_action('member_join', member, None, 'Member joined')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if isinstance(message.channel, discord.DMChannel):
        logger.info(f'DM from {message.author}: {message.content}')
        response = await process_dm_with_ai(message.author, message.content)
        try:
            await message.author.send(response)
        except Exception as e:
            logger.error(f'Failed to send DM: {e}')
    await bot.process_commands(message)

async def process_dm_with_ai(user, content):
    msg = content.lower()
    if 'help' in msg:
        return "Use !warn, !mute, !kick, !ban, !unmute, !logs in servers. I help moderate Discord communities!"
    elif 'who' in msg or 'what' in msg:
        return "I'm a Discord moderation bot with AI-powered decision making and comprehensive logging!"
    elif 'hi' in msg or 'hello' in msg:
        return f"Hello {user.mention}! How can I help?"
    else:
        return "Thanks for reaching out! I'm here to help moderate. Ask me about moderation commands!"

@bot.command()
async def warn(ctx, member: discord.Member, *, reason='No reason'):
    if member == ctx.author:
        await ctx.send("Can't warn yourself!")
        return
    if member.id not in user_warnings:
        user_warnings[member.id] = []
    user_warnings[member.id].append({'reason': reason, 'timestamp': datetime.now().isoformat()})
    count = len(user_warnings[member.id])
    log_action('warn', member, ctx.author, reason, {'count': count})
    embed = discord.Embed(title="User Warned", description=f"{member.mention} warned", color=discord.Color.orange())
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Total Warnings", value=str(count))
    await ctx.send(embed=embed)

@bot.command()
async def mute(ctx, member: discord.Member, *, reason='No reason'):
    muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
    if not muted_role:
        muted_role = await ctx.guild.create_role(name='Muted')
    await member.add_roles(muted_role)
    log_action('mute', member, ctx.author, reason)
    embed = discord.Embed(title="User Muted", description=f"{member.mention} muted", color=discord.Color.red())
    embed.add_field(name="Reason", value=reason)
    await ctx.send(embed=embed)

@bot.command()
async def unmute(ctx, member: discord.Member, *, reason='No reason'):
    muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
    if muted_role and muted_role in member.roles:
        await member.remove_roles(muted_role)
    log_action('unmute', member, ctx.author, reason)
    embed = discord.Embed(title="User Unmuted", description=f"{member.mention} unmuted", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command()
async def kick(ctx, member: discord.Member, *, reason='No reason'):
    log_action('kick', member, ctx.author, reason)
    await member.kick(reason=reason)
    embed = discord.Embed(title="User Kicked", description=f"{member} kicked", color=discord.Color.red())
    embed.add_field(name="Reason", value=reason)
    await ctx.send(embed=embed)

@bot.command()
async def ban(ctx, member: discord.Member, *, reason='No reason'):
    log_action('ban', member, ctx.author, reason)
    await member.ban(reason=reason)
    embed = discord.Embed(title="User Banned", description=f"{member} banned", color=discord.Color.dark_red())
    embed.add_field(name="Reason", value=reason)
    await ctx.send(embed=embed)

@bot.command()
async def logs(ctx, user: discord.Member = None):
    user_logs = [log for log in mod_logs if user and str(log.get('user')) == str(user)] if user else mod_logs[-10:]
    embed = discord.Embed(title="Moderation Logs", description=f"{len(user_logs)} entries", color=discord.Color.blue())
    for log_entry in user_logs[-5:]:
        embed.add_field(name=f"{log_entry['action'].upper()}", value=f"User: {log_entry['user']}\nReason: {log_entry['reason']}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    latency = f"{round(bot.latency * 1000)}ms"
    embed = discord.Embed(title="Pong!", description=f"Latency: {latency}", color=discord.Color.green())
    logger.info(f"Ping: {latency}")
    await ctx.send(embed=embed)

@bot.command()
async def status(ctx):
    embed = discord.Embed(title="Bot Status", description="Online and operational", color=discord.Color.green())
    embed.add_field(name="Guilds", value=len(bot.guilds))
    embed.add_field(name="Logs", value=len(mod_logs))
    await ctx.send(embed=embed)

if __name__ == '__main__':
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    logger.info('Starting bot...')
    bot.run(BOT_TOKEN)
