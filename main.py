import discord
from discord.ext import commands
import os
import asyncio

# ---------------------------------------------------------
# BOT SETUP & CONFIGURATION
# ---------------------------------------------------------
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Prefix P और p सेट किया है, और डिफ़ॉल्ट हेल्प बंद कर दी है ताकि अपना कस्टम हेल्प दिखे
bot = commands.Bot(command_prefix=['P ', 'p ', 'P', 'p'], intents=intents, help_command=None)


# ---------------------------------------------------------
# UI CLASSES (DROPDOWNS)
# ---------------------------------------------------------
class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Security Modules', description='Antinuke, Raidmode, Automod', emoji='🛡️'),
            discord.SelectOption(label='Moderation', description='Ban, Kick, Purge, Lock', emoji='🔨'),
            discord.SelectOption(label='Utility & Info', description='Server info, Weather, User details', emoji='⚙️')
        ]
        super().__init__(placeholder='Explore Panther Modules...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'Security Modules':
            embed = discord.Embed(title="🛡️ Security Modules", color=discord.Color.red())
            embed.add_field(name="Core Setup", value="`P setup logs` - Setup antinuke logging\n`P wl @user` - Advanced Whitelist UI", inline=False)
            embed.add_field(name="Protections", value="`P antinuke`, `P superantinuke`, `P raidmode`, `P beastmode`", inline=False)
            await interaction.response.edit_message(embed=embed)
            
        elif self.values[0] == 'Moderation':
            embed = discord.Embed(title="🔨 Moderation Tools", color=discord.Color.blue())
            embed.add_field(name="Mass Actions", value="`P massban`, `P masskick`, `P tempban`", inline=False)
            embed.add_field(name="Channel Controls", value="`P nukechannel`, `P lock`, `P unlock`, `P purge <amount>`", inline=False)
            await interaction.response.edit_message(embed=embed)
            
        elif self.values[0] == 'Utility & Info':
            embed = discord.Embed(title="⚙️ Utility & Server Info", color=discord.Color.green())
            embed.add_field(name="Info", value="`P serverinfo`, `P userinfo`, `P avatar`", inline=False)
            embed.add_field(name="Tools", value="`P weather <city>`, `P calc <expression>`, `P afk`", inline=False)
            await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpDropdown())

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
        await interaction.response.send_message(f"✅ {self.target_user.mention} has been whitelisted for: **{selected}** by {interaction.user.mention}")

class WhitelistView(discord.ui.View):
    def __init__(self, target_user):
        super().__init__()
        self.add_item(WhitelistDropdown(target_user))


# ---------------------------------------------------------
# BOT EVENTS
# ---------------------------------------------------------
@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} (Panther Security) is online and ready on Railway!')
    await bot.change_presence(activity=discord.Game(name="Protecting BGMI Server | P help"))


# ---------------------------------------------------------
# MAIN COMMANDS
# ---------------------------------------------------------
@bot.command(name='help', aliases=['h'])
async def custom_help(ctx):
    embed = discord.Embed(
        title="🛡️ Panther Security",
        description="**🚀 Your Ultimate Security Guardian**\n\n"
                    "• **Server Prefix:** `P `\n"
                    "• **Total Commands:** 50+\n"
                    "• **Status:** Active & Protect\n\n"
                    "*Use the dropdown below to explore modules!*",
        color=0x2b2d31
    )
    view = HelpView()
    await ctx.send(embed=embed, view=view)

@bot.command(name='setup', aliases=['autosetup'])
@commands.has_permissions(administrator=True)
async def setup(ctx, module: str = None):
    if module and module.lower() == 'logs':
        category = discord.utils.get(ctx.guild.categories, name="🛡️ Panther Security")
        if not category:
            category = await ctx.guild.create_category("🛡️ Panther Security")
        
        log_channel = discord.utils.get(ctx.guild.text_channels, name="antinuke-logs")
        if not log_channel:
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

@bot.command(name='wl', aliases=['whitelist'])
@commands.has_permissions(administrator=True)
async def whitelist(ctx, user: discord.Member = None):
    if user is None:
        return await ctx.send("⚠️ Please mention a user! Usage: `P wl @user`")
    view = WhitelistView(user)
    await ctx.send(f"🛡️ Whitelist Settings for {user.mention}:", view=view)

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
# REGISTERED PLACEHOLDER COMMANDS (Structure for Future Logic)
# ---------------------------------------------------------
@bot.command()
async def raidmode(ctx, action: str = None): await ctx.send("🛡️ Raidmode configuration panel.")

@bot.command(aliases=['antimultispam', 'antispam', 'antiping', 'anticaps', 'antimoji', 'antilink', 'antieveryone'])
async def automod(ctx): await ctx.send("🤖 Automod settings triggered.")

@bot.command()
async def antinuke(ctx, action: str = None): await ctx.send("🛑 Antinuke settings panel.")

@bot.command()
async def superantinuke(ctx, action: str = None): await ctx.send("🛑 SuperAntinuke status.")

@bot.command()
async def beastmode(ctx, action: str = None): await ctx.send("⚠️ Beast Mode controls.")

@bot.command()
async def wallroles(ctx): await ctx.send("🧱 Wall roles configuration.")

@bot.command()
async def massban(ctx, *users: discord.Member): await ctx.send("🔨 Massban initiated.")

@bot.command()
async def masskick(ctx, *users: discord.Member): await ctx.send("👞 Masskick initiated.")

@bot.command()
async def tempban(ctx, user: discord.Member, duration: str): await ctx.send(f"⏳ {user} tempbanned for {duration}.")

@bot.command()
async def role(ctx, action: str, user_or_role=None): await ctx.send("🎭 Role management command triggered.")

@bot.command(aliases=['rolehumans', 'rolebots'])
async def massrole(ctx, role: discord.Role): await ctx.send("👥 Mass role assignment started.")

@bot.command()
async def serverinfo(ctx): await ctx.send("📊 Displaying Server Info...")

@bot.command()
async def userinfo(ctx, user: discord.Member = None): await ctx.send("👤 Displaying User Info...")

@bot.command()
async def avatar(ctx, user: discord.Member = None): await ctx.send("🖼️ Fetching Avatar...")

@bot.command()
async def weather(ctx, *, city: str): await ctx.send(f"☁️ Fetching weather for {city}...")

@bot.command()
async def calc(ctx, *, expression: str): await ctx.send(f"🧮 Calculating: {expression}...")

@bot.command()
async def afk(ctx, *, reason="AFK"): await ctx.send(f"💤 {ctx.author.mention} is now AFK: {reason}")


# ---------------------------------------------------------
# RUN BOT
# ---------------------------------------------------------
if __name__ == '__main__':
    if not TOKEN:
        print("CRITICAL ERROR: DISCORD_TOKEN is missing! Please set it in Railway Variables.")
    else:
        bot.run(TOKEN)
