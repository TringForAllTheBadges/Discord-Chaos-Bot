import discord
from discord.ext import commands
import asyncio
import json
from utils import *
import random

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

with open('config.json') as f:
    config = json.load(f)

TOKEN = config['token']
nuke_in_progress = False

def get_command_list():
    command_list = [f"!{command.name}: {command.help}" for command in bot.commands]
    return "\n".join(command_list)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print("\nAvailable commands:")
    print(get_command_list())

@bot.command(help="Spam a message multiple times. Example: !spam 5 Hello World")
async def spam(ctx, count: int = None, *, message: str = None):
    if count is None or message is None:
        await ctx.send("Usage: !spam [count] [message]\nExample: !spam 5 Hello World")
        return
    await spam_messages(ctx.channel, count, message)

@bot.command(help="Purge a specified number of messages. Example: !purge 10")
async def purge(ctx, limit: int = None):
    if limit is None:
        await ctx.send("Usage: !purge [limit]\nExample: !purge 10")
        return
    try:
        deleted = await ctx.channel.purge(limit=limit)
        await ctx.send(f'Deleted {len(deleted)} message(s)', delete_after=5)
    except discord.Forbidden:
        await ctx.send("I don't have the required permissions to delete messages in this channel.")
    except Exception as e:
        await ctx.send(f"An error occurred while trying to purge messages: {str(e)}")

@bot.command(help="Raid the server by spamming all text channels. Example: !raid")
async def raid(ctx):
    try:
        await raid_server(ctx.guild)
    except discord.Forbidden:
        await ctx.send("I don't have the required permissions to perform a raid.")
    except Exception as e:
        await ctx.send(f"An error occurred while trying to raid: {str(e)}")

@bot.command(help="Nuke the server (delete channels, roles, and ban members). Example: !nuke")
async def nuke(ctx):
    global nuke_in_progress
    if nuke_in_progress:
        await ctx.send("A nuke is already in progress.")
        return
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return
    
    confirmation = await ctx.send("Are you sure you want to nuke the server? This action is irreversible. React with 👍 to confirm.")
    await confirmation.add_reaction("👍")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == "👍"

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("Nuke cancelled due to timeout.")
        return

    await ctx.send("Initiating server nuke...")
    nuke_in_progress = True
    results = await nuke_server(ctx.guild, ctx.author.id, bot.user.id)
    nuke_in_progress = False
    await ctx.author.send("Nuke results:\n" + "\n".join(results))

@bot.command(help="Stop an ongoing nuke process. Example: !stop_nuke")
async def stop_nuke(ctx):
    global nuke_in_progress
    if not nuke_in_progress:
        await ctx.send("No nuke is currently in progress.")
        return
    nuke_in_progress = False
    await ctx.send("Nuke process has been stopped.")

@bot.command(help="Send a mass DM to all server members. Example: !mass_dm Hello everyone!")
async def mass_dm(ctx, *, message):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return
    result = await mass_dm_members(ctx.guild, message)
    await ctx.send(result)

@bot.command(help="Create multiple channels with a given name. Example: !create_channels 5 raid_channel")
async def create_channels(ctx, count: int, *, name: str):
    if not ctx.author.guild_permissions.manage_channels:
        await ctx.send("You don't have permission to use this command.")
        return
    if count <= 0 or count > 50:
        await ctx.send("Please provide a valid number of channels (1-50).")
        return
    result = await create_multiple_channels(ctx.guild, count, name)
    await ctx.send(result)

@bot.command(help="Delete all channels in the server. Example: !delete_channels")
async def delete_channels(ctx):
    if not ctx.author.guild_permissions.manage_channels:
        await ctx.send("You don't have permission to use this command.")
        return
    result = await delete_all_channels(ctx.guild)
    await ctx.send(result)

@bot.command(help="Kick all members from the server. Example: !mass_kick")
async def mass_kick(ctx):
    if not ctx.author.guild_permissions.kick_members:
        await ctx.send("You don't have permission to use this command.")
        return
    result = await kick_all_members(ctx.guild, ctx.author.id, bot.user.id)
    await ctx.send(result)

@bot.command(help="Ban all members from the server. Example: !mass_ban")
async def mass_ban(ctx):
    if not ctx.author.guild_permissions.ban_members:
        await ctx.send("You don't have permission to use this command.")
        return
    result = await ban_all_members(ctx.guild, ctx.author.id, bot.user.id)
    await ctx.send(result)

@bot.command(help="Display server information. Example: !server_info")
async def server_info(ctx):
    await send_server_info(ctx)

@bot.command(help="Change the server name. Example: !rename_server New Server Name")
async def rename_server(ctx, *, new_name):
    if not ctx.author.guild_permissions.manage_guild:
        await ctx.send("You don't have permission to use this command.")
        return
    try:
        await ctx.guild.edit(name=new_name)
        await ctx.send(f"Server name changed to: {new_name}")
    except discord.Forbidden:
        await ctx.send("I don't have permission to change the server name.")

@bot.command(help="Give everyone a specific role. Example: !mass_role @RoleName")
async def mass_role(ctx, role: discord.Role):
    if not ctx.author.guild_permissions.manage_roles:
        await ctx.send("You don't have permission to use this command.")
        return
    success = 0
    for member in ctx.guild.members:
        try:
            await member.add_roles(role)
            success += 1
        except:
            pass
    await ctx.send(f"Added the role to {success} members.")

@bot.command(help="Create a server backup (roles and channels). Example: !backup")
async def backup(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return
    backup_data = await create_backup(ctx.guild)
    await ctx.author.send("Server backup:", file=discord.File(fp=backup_data, filename="server_backup.json"))
    await ctx.send("Backup created and sent to your DMs.")

@bot.command(help="Restore a server from a backup. Example: !restore")
async def restore(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return
    if not ctx.message.attachments:
        await ctx.send("Please attach the backup file when using this command.")
        return
    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith('.json'):
        await ctx.send("Please provide a valid JSON backup file.")
        return
    backup_data = await attachment.read()
    await restore_backup(ctx.guild, backup_data)
    await ctx.send("Server restored from backup.")

@bot.command(help="Generate invite links for all channels. Example: !invite_all")
async def invite_all(ctx):
    if not ctx.author.guild_permissions.create_instant_invite:
        await ctx.send("You don't have permission to use this command.")
        return
    invites = await generate_all_invites(ctx.guild)
    invite_message = "\n".join([f"{channel}: {invite}" for channel, invite in invites.items()])
    await ctx.author.send(f"Invite links for all channels:\n{invite_message}")
    await ctx.send("Invite links have been sent to your DMs.")

# Game commands
@bot.command(help="Play a game of Rock Paper Scissors. Example: !rps rock")
async def rps(ctx, choice: str):
    choices = ["rock", "paper", "scissors"]
    if choice.lower() not in choices:
        await ctx.send("Invalid choice. Please choose rock, paper, or scissors.")
        return
    bot_choice = random.choice(choices)
    result = determine_rps_winner(choice.lower(), bot_choice)
    await ctx.send(f"You chose {choice}, I chose {bot_choice}. {result}")

@bot.command(help="Guess a number between 1 and 10. Example: !guess 7")
async def guess(ctx, number: int):
    if number < 1 or number > 10:
        await ctx.send("Please guess a number between 1 and 10.")
        return
    correct_number = random.randint(1, 10)
    if number == correct_number:
        await ctx.send("Congratulations! You guessed correctly!")
    else:
        await ctx.send(f"Sorry, the correct number was {correct_number}. Try again!")

@bot.command(help="Roll a dice. Example: !roll 2d6")
async def roll(ctx, dice: str):
    try:
        num_dice, num_sides = map(int, dice.split('d'))
        if num_dice <= 0 or num_sides <= 0:
            raise ValueError
    except ValueError:
        await ctx.send("Invalid format. Use 'NdM' where N is the number of dice and M is the number of sides.")
        return
    
    results = [random.randint(1, num_sides) for _ in range(num_dice)]
    total = sum(results)
    await ctx.send(f"Rolling {dice}:\nResults: {results}\nTotal: {total}")

@bot.command(help="Play a game of Hangman. Example: !hangman")
async def hangman(ctx):
    word, hidden_word, attempts = start_hangman()
    await ctx.send(f"Let's play Hangman! Your word has {len(word)} letters.\n{' '.join(hidden_word)}\nYou have {attempts} attempts left.")
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1
    
    while attempts > 0 and '_' in hidden_word:
        try:
            guess = await bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("Time's up! The game has ended.")
            return
        
        hidden_word, attempts = guess_hangman(word, hidden_word, guess.content.lower(), attempts)
        await ctx.send(f"{' '.join(hidden_word)}\nYou have {attempts} attempts left.")
    
    if '_' not in hidden_word:
        await ctx.send(f"Congratulations! You guessed the word: {word}")
    else:
        await ctx.send(f"Game over! The word was: {word}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use !help for a list of commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. Check command usage.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

bot.run(TOKEN)
