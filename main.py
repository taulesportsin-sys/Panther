import discord
from discord.ext import commands
import os
import random
import asyncio

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Prefix handler: p, P, p , P 
def get_prefix(bot, message):
    return ['P ', 'p ', 'P', 'p']

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# --- Constants & Variables ---
OWNER_ID = 1525484718412267662
MAX_BET_LIMIT = 250000
STARTING_BALANCE = 100000
DAILY_REWARD = 15000
OWNER_BALANCE = 100000000000  # ओनर का अनलिमिटेड कैश

# Database Placeholder
users_db = {}

def get_balance(user_id):
    if user_id not in users_db:
        if user_id == OWNER_ID:
            users_db[user_id] = OWNER_BALANCE
        else:
            users_db[user_id] = STARTING_BALANCE
    return users_db[user_id]

def update_balance(user_id, amount):
    users_db[user_id] = get_balance(user_id) + amount

def parse_bet(bet_str, balance):
    if bet_str.lower() == "all":
        return min(balance, MAX_BET_LIMIT)
    try:
        amount = int(bet_str)
        return amount
    except ValueError:
        return None

# --- Events & Error Handling ---
@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online with ALL GAMES!')
    await bot.change_presence(activity=discord.Game(name="BGMI Scrims | p help"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ भाई, ये कमांड गलत है! सही कमांड्स देखने के लिए `p help` टाइप करो।")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ तुमने कमांड पूरी नहीं लिखी! सही तरीका जानने के लिए `p help` चेक करो।")

# --- Custom Help Command ---
@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🤖 Ultimate Bot Commands Menu", color=0x2b2d31, description="प्रिफिक्स: `p` या `P` (स्पेस दो या मत दो!)")
    
    embed.add_field(name="💰 Economy", 
                    value="`p cash` - अपना बैलेंस चेक करो\n"
                          "`p daily` - डेली 15,000 कैश क्लेम करो\n"
                          "`p give @user [amount]` - कैश ट्रांसफर करो", inline=False)
                    
    embed.add_field(name="🎲 Games (Max Bet: 2.5L)", 
                    value="`p mine [amount/all] [mines]` - माइन स्वीपर\n"
                          "`p cf [amount/all] [heads/tails]` - कॉइन फ्लिप\n"
                          "`p s [amount/all]` - स्लॉट्स मशीन\n"
                          "`p hl [amount/all]` - हाई-लो कार्ड गेम", inline=False)
                    
    embed.add_field(name="🏆 Scrims", 
                    value="`p qualify \"Team Name\" @Role @Player1 @Player2` - टीम को क्वालीफाई करो और रोल दो", inline=False)
                    
    await ctx.send(embed=embed)


# --- Economy Commands ---
@bot.command(name="cash", aliases=["bal", "balance"])
async def cash(ctx, member: discord.Member = None):
    member = member or ctx.author
    bal = get_balance(member.id)
    await ctx.send(f"💳 | **{member.display_name}**, you currently have **{bal:,}** cash!")

@bot.command(name="daily")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily(ctx):
    update_balance(ctx.author.id, DAILY_REWARD)
    await ctx.send(f"💸 | **{ctx.author.display_name}**, तुमने अपना डेली **15,000** कैश क्लेम कर लिया है!")

@daily.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ | थोड़ा सब्र करो! दोबारा क्लेम करने में **{error.retry_after // 3600:.0f}** घंटे बाकी हैं।")

@bot.command(name="give")
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0: return await ctx.send("❌ अमाउंट 0 से ज़्यादा होना चाहिए!")
    sender_bal = get_balance(ctx.author.id)
    if ctx.author.id != OWNER_ID and sender_bal < amount:
        return await ctx.send("❌ तुम्हारे पास इतना कैश नहीं है!")
        
    update_balance(ctx.author.id, -amount)
    update_balance(member.id, amount)
    await ctx.send(f"💳 | **{ctx.author.display_name}** sent **{amount:,}** cash to **{member.display_name}**!")


# --- GAME: Coinflip (cf) ---
@bot.command(name="coinflip", aliases=["cf"])
async def coinflip(ctx, bet: str, choice: str = "heads"):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount: return await ctx.send("❌ सही अमाउंट डालो या `all` लिखो!")
    if bet_amount > MAX_BET_LIMIT: return await ctx.send(f"❌ मैक्स लिमिट **{MAX_BET_LIMIT:,}** है!")
    if bet_amount <= 0 or bet_amount > bal: return await ctx.send("❌ इनवैलिड अमाउंट या कैश कम है!")
    if choice.lower() not in ["heads", "tails", "h", "t"]: return await ctx.send("❌ Heads या Tails चुनो!")

    choice_full = "heads" if choice.lower() in ["heads", "h"] else "tails"
    result = random.choice(["heads", "tails"])
    
    msg = await ctx.send(f"**{ctx.author.display_name}** spent 💵 **{bet_amount:,}** and chose **{choice_full}**\nThe coin spins... 🪙")
    await asyncio.sleep(2) # सस्पेंस के लिए
    
    if choice_full == result:
        update_balance(ctx.author.id, bet_amount) # Double money (profit = bet)
        await msg.edit(content=f"**{ctx.author.display_name}** spent 💵 **{bet_amount:,}** and chose **{choice_full}**\nThe coin spins... 🪙 and you **WON {bet_amount * 2:,}!** 🎉")
    else:
        update_balance(ctx.author.id, -bet_amount)
        await msg.edit(content=f"**{ctx.author.display_name}** spent 💵 **{bet_amount:,}** and chose **{choice_full}**\nThe coin spins... 🪙 and you **lost it all... :c**")


# --- GAME: Slots (s) ---
@bot.command(name="slots", aliases=["s"])
async def slots(ctx, bet: str):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount: return await ctx.send("❌ सही अमाउंट डालो या `all` लिखो!")
    if bet_amount > MAX_BET_LIMIT: return await ctx.send(f"❌ मैक्स लिमिट **{MAX_BET_LIMIT:,}** है!")
    if bet_amount <= 0 or bet_amount > bal: return await ctx.send("❌ इनवैलिड अमाउंट या कैश कम है!")

    emojis = ["🍎", "🍒", "🍇", "💎", "🔔", "💖"]
    slot1, slot2, slot3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
    
    if slot1 == slot2 == slot3:
        multiplier = 5 # 3 सेम पर 5x
        winnings = bet_amount * multiplier
        update_balance(ctx.author.id, winnings - bet_amount)
        result_text = f"and **WON {winnings:,}!!** 🎰🔥"
    elif slot1 == slot2 or slot2 == slot3 or slot1 == slot3:
        multiplier = 2 # 2 सेम पर 2x
        winnings = bet_amount * multiplier
        update_balance(ctx.author.id, winnings - bet_amount)
        result_text = f"and won **{winnings:,}!** 🎰"
    else:
        update_balance(ctx.author.id, -bet_amount)
        result_text = f"and won nothing... :c"

    embed = discord.Embed(color=0x2b2d31)
    embed.description = f"**___SLOTS___**\n[ {slot1} {slot2} {slot3} ] **{ctx.author.display_name}** bet 💵 {bet_amount:,}\n|               | {result_text}"
    await ctx.send(embed=embed)


# --- GAME: Mines ---
@bot.command(name="mine", aliases=["mines"])
async def mine(ctx, bet: str, num_mines: int = 1):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount: return await ctx.send("❌ सही अमाउंट डालो या `all` लिखो!")
    if bet_amount > MAX_BET_LIMIT: return await ctx.send(f"❌ मैक्स लिमिट **{MAX_BET_LIMIT:,}** है!")
    if bet_amount <= 0 or bet_amount > bal: return await ctx.send("❌ इनवैलिड अमाउंट या कैश कम है!")
    if num_mines < 1 or num_mines > 24: return await ctx.send("❌ माइन 1 से 24 के बीच होनी चाहिए!")

    safe_spots = 25 - num_mines
    win_chance = safe_spots / 25.0
    
    if random.random() < win_chance:
        multiplier = 1.0 + (num_mines * 0.15) 
        winnings = int(bet_amount * multiplier)
        update_balance(ctx.author.id, winnings - bet_amount)
        await ctx.send(f"💎 | **{ctx.author.display_name}** cashed out! Winnings: **{winnings:,}** ({multiplier:.2f}x)")
    else:
        update_balance(ctx.author.id, -bet_amount)
        await ctx.send(f"💣 | **{ctx.author.display_name}** hit a mine! You lost **{bet_amount:,}**... :c")


# --- GAME: HighLow (hl) Interactive View ---
class HighLowView(discord.ui.View):
    def __init__(self, ctx, bet_amount, current_card):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.bet_amount = bet_amount
        self.current_card = current_card
        self.multiplier = 1.0

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ यह तुम्हारा गेम नहीं है!", ephemeral=True)
            return False
        return True

    async def process_guess(self, interaction: discord.Interaction, guess: str):
        next_card = random.randint(1, 10)
        won = False
        
        if guess == "higher" and next_card > self.current_card: won = True
        elif guess == "lower" and next_card < self.current_card: won = True
        elif guess == "same" and next_card == self.current_card: won = True
        
        if won:
            if guess == "same": self.multiplier += 1.5
            else: self.multiplier += 0.3
            
            self.current_card = next_card
            embed = discord.Embed(title="👍 Good guess!", color=0x00ff00)
            embed.description = f"Bet: {self.bet_amount:,}\nCurrent Card: **{self.current_card}**\nCurrent Multiplier: **{self.multiplier:.2f}x**"
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            update_balance(self.ctx.author.id, -self.bet_amount)
            embed = discord.Embed(title="👎 You guessed incorrectly!!", color=0xff0000)
            embed.description = f"Bet: {self.bet_amount:,}\nThe card was **{next_card}**.\nYou guessed {guess}. You lost."
            
            # Disable buttons
            for child in self.children: child.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()

    @discord.ui.button(label="Higher", style=discord.ButtonStyle.blurple)
    async def btn_higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_guess(interaction, "higher")

    @discord.ui.button(label="Lower", style=discord.ButtonStyle.blurple)
    async def btn_lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_guess(interaction, "lower")

    @discord.ui.button(label="Same", style=discord.ButtonStyle.blurple)
    async def btn_same(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_guess(interaction, "same")

    @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.success)
    async def btn_cashout(self, interaction: discord.Interaction, button: discord.ui.Button):
        winnings = int(self.bet_amount * self.multiplier)
        update_balance(self.ctx.author.id, winnings - self.bet_amount)
        
        embed = discord.Embed(title="💸 Cashed Out!", color=0x00ff00)
        embed.description = f"You cashed out at **{self.multiplier:.2f}x** and won **{winnings:,}**!"
        
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

@bot.command(name="highlow", aliases=["hl"])
async def highlow(ctx, bet: str):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount: return await ctx.send("❌ सही अमाउंट डालो या `all` लिखो!")
    if bet_amount > MAX_BET_LIMIT: return await ctx.send(f"❌ मैक्स लिमिट **{MAX_BET_LIMIT:,}** है!")
    if bet_amount <= 0 or bet_amount > bal: return await ctx.send("❌ इनवैलिड अमाउंट या कैश कम है!")

    start_card = random.randint(1, 10)
    embed = discord.Embed(title="🃏 HighLow Game", color=0x2b2d31)
    embed.description = f"Bet: {bet_amount:,}\nCurrent Card: **{start_card}**\nWhat's the next card going to be?"
    
    view = HighLowView(ctx, bet_amount, start_card)
    await ctx.send(embed=embed, view=view)


# --- Scrims Qualifiers Command ---
@bot.command(name="qualify")
@commands.has_permissions(manage_roles=True)
async def qualify(ctx, team_name: str, role: discord.Role, *members: discord.Member):
    if not members: return await ctx.send("❌ प्लेयर को टैग (mention) करो!")
        
    mentions = " ".join([m.mention for m in members])
    for m in members:
        try: await m.add_roles(role)
        except discord.Forbidden: return await ctx.send("❌ बोट के पास रोल देने की परमिशन नहीं है!")
            
    embed = discord.Embed(title="🏆 QUALIFIERS — RESULTS", color=0x2b2d31)
    embed.add_field(name="🌟 QUALIFIED TEAM", value=f"**1. ✓ {team_name} —**\n{mentions}", inline=False)
    embed.add_field(name="", value=f"🎉 You've been given the {role.mention} role.", inline=False)
    embed.set_footer(text=f"Verified by {ctx.author.display_name}")
    
    await ctx.send(embed=embed)


# --- Run the Bot ---
token = os.environ.get("DISCORD_TOKEN")
if token: bot.run(token)
else: print("❌ ERROR: DISCORD_TOKEN environment variable is not set!")
