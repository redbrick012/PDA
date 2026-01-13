import os
import json
import discord
from discord.ext import commands, tasks
import gspread
from google.oauth2.service_account import Credentials

# =====================
# ENV
# =====================
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
SHEET_NAME = os.environ.get("SHEET_NAME", "PDA_View")

# =====================
# GOOGLE SHEETS
# =====================
scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds_json = json.loads(os.environ["GOOGLE_CREDS_JSON"])
creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
gc = gspread.authorize(creds)

sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# =====================
# DISCORD
# =====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

message_id = None  # stored in memory (fine for now)

# =====================
# HELPERS
# =====================
def read_block(start_row, end_row, col):
    values = sheet.col_values(col)[start_row - 1:end_row]
    return [v for v in values if v.strip()]

def build_embed(title):
    embed = discord.Embed(
        title=title,
        color=0x2f3136
    )

    # Define your field ranges
    field_ranges = [
        (5, 7),
        (9, 11),
        (13, 15),
        (17, 19),
        (21, 23)
    ]

    # Diamond colors for priority (most important first)
    icons = ["🔴", "🟠", "🟡", "🟢", "🔵"]

    # Add each range as a field with an icon as the name
    for icon, (start, end) in zip(icons, field_ranges):
        lines = read_block(start, end, 3)  # Column C
        embed.add_field(
            name=icon,
            value="\n".join(lines) if lines else "—",
            inline=False  # False if you want each on a new line
        )

    return embed

# =====================
# TASK
# =====================
@tasks.loop(minutes=5)
async def update_pda():
    global message_id
    channel = bot.get_channel(CHANNEL_ID)

    # === ADJUST ROW/COLUMN NUMBERS IF SHEET MOVES ===
    pda_embed = build_embed("📦 Priority Items")

    if message_id:
        try:
            msg = await channel.fetch_message(message_id)  # ✅ must be inside async
            await msg.edit(embeds=[pda_embed])
            return
        except discord.NotFound:
            message_id = None

    msg = await channel.send(embeds=[pda_embed])
    message_id = msg.id

# =====================
# EVENTS
# =====================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    update_pda.start()

bot.run(DISCORD_TOKEN)

