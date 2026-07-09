import discord
from discord.ext import commands
import os
import asyncio

# Railway के एनवायरनमेंट वेरिएबल से सीधा टोकन लेगा
TOKEN = os.getenv('DISCORD_TOKEN')

# Intents सेटअप
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# बॉट सेटअप (Prefix P और p)
bot = commands.Bot(command_prefix=['P ', 'p ', 'P', 'p'], intents=intents, help_command=None)

# ---------------------------------------------------------
# 1. ON READY EVENT
# ---------------------------------------------------------
@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} (Panther Security) is online and ready on Railway!')
    await bot.change_presence(activity=discord.Game(name="Protecting BGMI Server | P help"))

# ---------------------------------------------------------
# 2. AUTO SETUP (P setup)
# ---------------------------------------------------------
@bot.command(name='setup', aliases=['autosetup'])
@commands.has_permissions(administrator=True)
async def setup(ctx, module: str = None):
    if module and module.lower() == 'logs':
        # कैटेगरी बनाना
        category = discord.utils.get(ctx.guild.categories, name="🛡️ Panther Security")
        if not category:
            category = await ctx.guild.create_category("🛡️ Panther Security")
        
        # लॉग चैनल बनाना
        log_channel = discord.utils.get(ctx.guild.text_channels, name="antinuke-logs")
        if not log_channel:
            # प्राइवेट चैनल बनाना (सिर्फ एडमिन्स और बॉट के लिए)
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            log_channel = await ctx.guild.create_text_channel('antinuke-logs', category=category, overwrites=overwrites)
            await ctx.send(f"✅ Setup Complete! Category and {log_channel.mention} created successfully.")
            await log_channel.send("🚨 **Panther Security Antinuke Logs Initialized!**\nAll unauthorized actions will be logged here.")
        else:
            await ctx.send(f"⚠️ Setup is already done. Logs channel exists: {log_channel.mention}")
    else:
        await ctx.send("Usage: `P setup logs`")

# ---------------------------------------------------------
# 3. WHITELIST SYSTEM WITH DROPDOWN UI (P wl @user)
# ---------------------------------------------------------
class WhitelistDropdown(discord.ui.Select):
    def __init__(self, target_user):
        self.target_user = target_user
        options = [
            discord.SelectOption(label='Ban/Kick', description='Allow user to ban or kick members', emoji='🔨'),
            discord.SelectOption(label='Channel Management', description='Allow create/delete/update channels', emoji='📁'),
            discord.SelectOption(label='Role Management', description='Allow create/delete/update roles', emoji='🎭'),
            discord.SelectOption(label='Server Management', description='Allow editing server settings', emoji='⚙️'),
            discord.SelectOption(label='Full Whitelist', description='Bypass all antinuke protections', emoji='🌟')
        ]
        super().__init__(placeholder='Select permissions to whitelist...', min_values=1, max_values=5, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = ", ".join(self.values)
        # (यहाँ डेटाबेस में सेव करने का लॉजिक आएगा, अभी के लिए रिप्लाई कर रहा है)
        await interaction.response.send_message(f"✅ {self.target_user.mention} has been whitelisted for: **{selected}** by {interaction.user.mention}")

class WhitelistView(discord.ui.View):
    def __init__(self, target_user):
        super().__init__()
        self.add_item(WhitelistDropdown(target_user))

@bot.command(name='wl', aliases=['whitelist'])
@commands.has_permissions(administrator=True)
async def whitelist(ctx, user: discord.Member = None):
    if user is None:
        return await ctx.send("⚠️ Please mention a user! Usage: `P wl @user`")
    view = WhitelistView(user)
    await ctx.send(f"🛡️ Whitelist Settings for {user.mention}:", view=view)

# ---------------------------------------------------------
# 4. SERVER & CHANNEL CONTROL
# ---------------------------------------------------------
@bot.command(name='nukechannel', aliases=['nuke'])
@commands.has_permissions(manage_channels=True)
async def nukechannel(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    position = channel.position
    new_channel = await channel.clone(reason="Panther Security: Channel Nuked")
    await new_channel.edit(position=position)
    await channel.delete()
    await new_channel.send("https://tenor.com/view/explosion-mushroom-cloud-atomic-bomb-bomb-boom-gif-4464831")
    await new_channel.send("☢️ **Channel has been successfully nuked!**")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(f"🔒 {channel.mention} has been locked.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(f"🔓 {channel.mention} has been unlocked.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Purged {amount} messages.")
    await asyncio.sleep(3)
    await msg.delete()

# ---------------------------------------------------------
# 5. ALL OTHER COMMANDS REGISTERED (Structure Ready for Logic)
# ---------------------------------------------------------
# System Control & Raidmode
@bot.command()
async def raidmode(ctx, action: str = None): await ctx.send("Raidmode configuration panel.")

@bot.command(aliases=['antimultispam', 'antispam', 'antiping', 'anticaps', 'antimoji', 'antilink', 'antieveryone'])
async def automod(ctx): await ctx.send("Automod settings adjusted.")

# Antinuke Core
@bot.command()
async def antinuke(ctx, action: str = None): await ctx.send("Antinuke settings panel.")

@bot.command()
async def superantinuke(ctx, action: str = None): await ctx.send("SuperAntinuke status.")

@bot.command()
async def beastmode(ctx, action: str = None): await ctx.send("⚠️ Beast Mode controls.")

# Wall Roles
@bot.command()
async def wallroles(ctx): await ctx.send("Wall roles configuration.")

# Mass Actions
@bot.command()
async def massban(ctx, *users: discord.Member): await ctx.send("Massban initiated.")

@bot.command()
async def masskick(ctx, *users: discord.Member): await ctx.send("Masskick initiated.")

@bot.command()
async def tempban(ctx, user: discord.Member, duration: str): await ctx.send(f"{user} tempbanned for {duration}.")

# Role Management
@bot.command()
async def role(ctx, action: str, user_or_role=None): await ctx.send("Role management command triggered.")

@bot.command(aliases=['rolehumans', 'rolebots'])
async def massrole(ctx, role: discord.Role): await ctx.send("Mass role assignment started.")

# Utility Tools
@bot.command()
async def serverinfo(ctx): await ctx.send("Displaying Server Info...")

@bot.command()
async def userinfo(ctx, user: discord.Member = None): await ctx.send("Displaying User Info...")

@bot.command()
async def avatar(ctx, user: discord.Member = None): await ctx.send("Fetching Avatar...")

@bot.command()
async def weather(ctx, *, city: str): await ctx.send(f"Fetching weather for {city}...")

@bot.command()
async def calc(ctx, *, expression: str): await ctx.send(f"Calculating: {expression}...")

@bot.command()
async def afk(ctx, *, reason="AFK"): await ctx.send(f"{ctx.author.mention} is now AFK: {reason}")

# ---------------------------------------------------------
# BOT RUN LOGIC
# ---------------------------------------------------------
if __name__ == '__main__':
    if not TOKEN:
        print("CRITICAL ERROR: DISCORD_TOKEN is missing! Please set it in Railway Variables.")
    else:
        bot.run(TOKEN)
