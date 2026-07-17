import discord
from discord.ext import commands
import aiohttp
import os  # एनवायरनमेंट वेरिएबल रीड करने के लिए

# बॉट का सेटअप
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# इमेज को लिंक से डाउनलोड करने का फंक्शन
async def get_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            return None

@bot.event
async def on_ready():
    print(f'✅ बॉट लॉग इन हो चुका है: {bot.user.name}')

# 1. सर्ver का नाम चेंज करने की कमांड
@bot.command()
@commands.has_permissions(manage_guild=True)
async def setname(ctx, *, new_name: str):
    await ctx.guild.edit(name=new_name)
    await ctx.send(f"✅ सर्वर का नाम बदलकर **{new_name}** कर दिया गया है!")

# 2. सर्वर का लोगो (Icon) चेंज करने की कमांड
@bot.command()
@commands.has_permissions(manage_guild=True)
async def seticon(ctx, url: str):
    image_data = await get_image(url)
    if image_data:
        await ctx.guild.edit(icon=image_data)
        await ctx.send("✅ सर्वर का लोगो (Icon) सफलतापूर्वक अपडेट हो गया है!")
    else:
        await ctx.send("❌ इमेज डाउनलोड करने में दिक्कत आई, कृपया सही लिंक दें।")

# 3. सर्वर का बैनर चेंज करने की कमांड
@bot.command()
@commands.has_permissions(manage_guild=True)
async def setbanner(ctx, url: str):
    image_data = await get_image(url)
    if image_data:
        await ctx.guild.edit(banner=image_data)
        await ctx.send("✅ सर्वर का बैकग्राउंड बैनर अपडेट हो गया है!")
    else:
        await ctx.send("❌ इमेज डाउनलोड करने में दिक्कत आई, कृपया सही लिंक दें।")

# 4. रोल का आइकन चेंज करने की कमांड
@bot.command()
@commands.has_permissions(manage_roles=True)
async def setroleicon(ctx, role: discord.Role, url: str):
    image_data = await get_image(url)
    if image_data:
        await role.edit(icon=image_data)
        await ctx.send(f"✅ **{role.name}** रोल का आइकन सेट हो गया है!")
    else:
        await ctx.send("❌ इमेज डाउनलोड करने में दिक्कत आई, कृपया सही लिंक दें।")

# रेलवे के Variables से DISCORD_TOKEN उठाना
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ एरर: DISCORD_TOKEN एनवायरनमेंट वेरिएबल नहीं मिला! कृपया रेलवे सेटिंग्स चेक करें।")
