import discord
from discord.ext import commands, tasks
import datetime
import os

# ==========================================
# ⚙️ BOT SETUP & INTENTS
# ==========================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

# Variables to store channel IDs and Attendance in memory
announce_channel_id = None
active_channel_id = None
attendance_log = {} # Format: {user_id: True}

# Blacklist Words for Auto-Mod
BLACKLIST_WORDS = ["scammer", "स्कैमर", "gaali1", "gaali2"] 

# Indian Standard Time (IST) Setup
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def create_embed(title, description, color=discord.Color.dark_theme()):
    return discord.Embed(title=title, description=description, color=color)

@bot.event
async def on_ready():
    print(f'✅ Bot is ready! Logged in as {bot.user}')
    daily_tasks.start() 

# ==========================================
# 🛡️ AUTO-MODERATION & AUTO-ATTENDANCE
# ==========================================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. AUTO-ATTENDANCE: Auto-detect if they post in the active channel
    global active_channel_id
    if active_channel_id and message.channel.id == active_channel_id:
        has_staff = any(role.name in ["Panther Owner", "Panther Charmer"] for role in message.author.roles)
        if has_staff:
            attendance_log[message.author.id] = True
            await message.add_reaction("✅") 

    # 2. AUTO-MODERATION: Check for bad words
    has_admin = any(role.name == "Panther Owner" for role in message.author.roles)
    if not has_admin:
        msg_content = message.content.lower()
        if any(word in msg_content for word in BLACKLIST_WORDS):
            await message.delete()
            duration = datetime.timedelta(days=7) # 7 Days Timeout
            try:
                await message.author.timeout(duration, reason="Using abusive words or scammer tag")
                embed = create_embed("⚠️ Auto-Mod Action", f"**{message.author.mention}** has been timed out for 7 days for using prohibited words.")
                await message.channel.send(embed=embed)
            except discord.Forbidden:
                pass

    await bot.process_commands(message)

# ==========================================
# ⚙️ SETUP COMMANDS (Run these once!)
# ==========================================
@bot.command()
@commands.has_permissions(administrator=True)
async def setannounce(ctx, channel: discord.TextChannel):
    global announce_channel_id
    announce_channel_id = channel.id
    await ctx.send(f"✅ Announcements channel set to {channel.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setactive(ctx, channel: discord.TextChannel):
    global active_channel_id
    active_channel_id = channel.id
    await ctx.send(f"✅ Active/VC logs channel set to {channel.mention}. Bot will now auto-detect attendance here.")

@bot.command()
@commands.has_permissions(administrator=True)
async def createroles(ctx):
    roles_to_create = ["Panther Owner", "Panther Charmer"]
    created = []
    for role_name in roles_to_create:
        existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not existing_role:
            await ctx.guild.create_role(name=role_name, color=discord.Color.default(), reason="Panther Bot Setup")
            created.append(role_name)
    if created:
        embed = create_embed("✅ Roles Created", f"Successfully created: **{', '.join(created)}**")
    else:
        embed = create_embed("⚠️ Info", "Roles already exist.")
    await ctx.send(embed=embed)

# ==========================================
# 👑 OWNER COMMANDS
# ==========================================
@bot.command()
@commands.has_role("Panther Owner")
async def addstaff(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    embed = create_embed("🎉 New Staff Added!", f"**{member.mention}** has been given the **{role.mention}** role.")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role("Panther Owner")
async def promote(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    embed = create_embed("🎊 Staff Promoted!", f"Congratulations **{member.mention}**! You have been promoted to **{role.mention}**.")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role("Panther Owner")
async def demote(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    embed = create_embed("📉 Staff Demoted", f"**{member.mention}** has been removed from **{role.mention}**.")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role("Panther Owner")
async def serverinfo(ctx):
    guild = ctx.guild
    desc = f"**Total Members:** {guild.member_count}\n**Boosts:** {guild.premium_subscription_count}"
    embed = create_embed(f"📊 {guild.name} - Server Info", desc)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role("Panther Owner")
async def say(ctx, channel: discord.TextChannel, *, message: str):
    embed = create_embed("📢 Announcement", message)
    await channel.send(embed=embed)
    await ctx.send("✅ Message sent!", delete_after=3)

# ==========================================
# 🆘 CUSTOM HELP MENU
# ==========================================
@bot.command(name="help")
async def custom_help(ctx):
    embed = discord.Embed(title="🛠️ Panther Bot - Help Menu", description="Available commands:", color=discord.Color.dark_theme())
    embed.add_field(name="👑 Owner Commands", value="**$addstaff @user @role**\n**$promote @user @role**\n**$demote @user @role**\n**$serverinfo**\n**$say #channel [msg]**", inline=False)
    embed.add_field(name="⚙️ Setup Commands", value="**$createroles** - Create default roles\n**$setannounce #channel** - Set greetings channel\n**$setactive #channel** - Set attendance auto-detect channel", inline=False)
    await ctx.send(embed=embed)

# ==========================================
# 🚀 AUTOMATED GREETINGS & DEADLINE TASKS
# ==========================================
sent_morning = False
sent_afternoon = False
sent_night = False
checked_deadline = False

@tasks.loop(minutes=1)
async def daily_tasks():
    global sent_morning, sent_afternoon, sent_night, checked_deadline, attendance_log, announce_channel_id
    
    now = datetime.datetime.now(IST) 
    
    if announce_channel_id is None:
        return 

    channel = bot.get_channel(announce_channel_id)
    if not channel:
        return

    # Reset all trackers at midnight
    if now.hour == 0 and now.minute == 0:
        sent_morning = sent_afternoon = sent_night = checked_deadline = False
        attendance_log.clear() 

    # 8:30 AM - Good Morning
    if now.hour == 8 and now.minute == 30 and not sent_morning:
        embed = create_embed("🌅 Good Morning!", "Good morning bhai log! Fatafat apna active time daal do aur jo kaam theek lage apne hisaab se shuru kar do.")
        # Change ROLE_ID_HERE to the actual Role ID if tag doesn't work, or mention role normally
        await channel.send(content="<@&ROLE_ID_HERE>", embed=embed) 
        sent_morning = True

    # 12:00 PM - Deadline Check
    if now.hour == 12 and now.minute == 0 and not checked_deadline:
        guild = channel.guild
        staff_role = discord.utils.get(guild.roles, name="Panther Charmer")
        if staff_role:
            defaulters = []
            for member in staff_role.members:
                if member.id not in attendance_log:
                    defaulters.append(member.mention)
            
            if defaulters:
                embed = create_embed("⚠️ Deadline Alert!", f"The following staff haven't logged their active time yet:\n{', '.join(defaulters)}\n\n**Drop it now or face consequences!**", color=discord.Color.red())
                await channel.send(embed=embed)
            else:
                embed = create_embed("✅ Deadline Passed", "All staff have logged their active times! Great job.")
                await channel.send(embed=embed)
                
        checked_deadline = True

    # 2:00 PM - Good Afternoon
    if now.hour == 14 and now.minute == 0 and not sent_afternoon:
        embed = create_embed("☀️ Good Afternoon!", "Hope your day is going well, Panther Staff!")
        await channel.send(embed=embed)
        sent_afternoon = True

    # 10:00 PM - Good Night
    if now.hour == 22 and now.minute == 0 and not sent_night:
        embed = create_embed("🌙 Good Night!", "Wrap up your work and get some rest. See you tomorrow!")
        await channel.send(embed=embed)
        sent_night = True

# ==========================================
# ❌ ERROR HANDLING
# ==========================================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingPermissions):
        pass 

bot.run(os.getenv('DISCORD_TOKEN'))
