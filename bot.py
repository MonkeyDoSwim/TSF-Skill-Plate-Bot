import os
import re
from pathlib import Path
import discord
from discord.ext import commands
from discord import app_commands
from bs4 import BeautifulSoup

# ================= CONFIG =================

TOKEN = os.getenv("PLATE_DISCORD_TOKEN")
if not TOKEN:
    print("❌ ERROR: Set environment variable PLATE_DISCORD_TOKEN")
    raise SystemExit(1)

HTML_FILES = ["plates.html", "123.htm"]
IMAGE_FOLDER = "plates_files"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
plates = []


# ================= UTILITIES =================

def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def load_plates():
    plates.clear()

    html_path = None
    for name in HTML_FILES:
        if Path(name).exists():
            html_path = Path(name)
            break

    if not html_path:
        print("❌ No plates.html or 123.htm found next to bot.py")
        return

    print(f"📄 Loading: {html_path.name}")
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")

    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        name = clean(tds[0].get_text(" ", strip=True))
        desc = clean(tds[-1].get_text(" ", strip=True))
        if not name or not desc:
            continue

        img = None
        img_tag = tr.find("img")
        if img_tag and img_tag.get("src"):
            filename = img_tag["src"].split("/")[-1]
            local = Path(IMAGE_FOLDER) / filename
            if local.exists():
                img = str(local)

        plates.append({"name": name, "desc": desc, "img": img})

    print(f"✅ Loaded {len(plates)} plates with thumbnails.")


def search(query: str):
    words = query.lower().split()
    results = []
    for p in plates:
        text = (p["name"] + " " + p["desc"]).lower()
        if all(w in text for w in words):
            results.append(p)
    return results


async def send_list(ctx, results):
    if not results:
        return await ctx.send("❌ No matching plates.")

    for p in results[:5]:
        embed = discord.Embed(title=p["name"], description=p["desc"], color=discord.Color.blue())
        file = None
        if p["img"]:
            file = discord.File(p["img"], filename="thumb.png")
            embed.set_thumbnail(url="attachment://thumb.png")
        await ctx.send(embed=embed, file=file)


async def send_single(inter, plate):
    embed = discord.Embed(title=plate["name"], description=plate["desc"], color=discord.Color.dark_gold())
    file = None
    if plate["img"]:
        file = discord.File(plate["img"], filename="thumb.png")
        embed.set_thumbnail(url="attachment://thumb.png")
    await inter.response.send_message(embed=embed, file=file)


# ================= READY =================

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    load_plates()
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced globally.")
        print("⏳ They may take ~30–90 minutes to appear the first time.")
    except Exception as e:
        print("⚠️ Slash sync failed:", e)
    await bot.change_presence(activity=discord.Game(name="!sp trap red  |  /sp"))


# ================= TEXT COMMANDS =================

@bot.command()
async def reload(ctx):
    load_plates()
    await ctx.send("🔄 Reload complete.")


@bot.command()
async def sp(ctx, *, query=None):
    if not query:
        return await ctx.send("Usage: `!sp <keywords>`")
    await send_list(ctx, search(query))


def make_text_shortcut(name):
    @bot.command(name=name)
    async def _cmd(ctx, *, extra=""):
        await send_list(ctx, search(name + " " + extra))


for kw in ["trap", "bleed", "botch", "multiply", "yellow", "black"]:
    make_text_shortcut(kw)


# ================= SLASH COMMANDS =================

@bot.tree.command(name="sp", description="Search plates (supports multiple words)")
@app_commands.describe(query="Example: trap red")
@bot.tree.command(name="sp", description="Browse or search plates. Type words to filter.")
@app_commands.describe(query="Optional keywords to filter plates")
async def slash_sp(inter, query: str = None):

    if query:
        list_to_show = search(query)
        if not list_to_show:
            return await inter.response.send_message("❌ No plates found for that search.")
    else:
        list_to_show = plates

    PAGE_SIZE = 25
    pages = [list_to_show[i:i+PAGE_SIZE] for i in range(0, len(list_to_show), PAGE_SIZE)]
    page_index = 0

    async def show_page(interaction, idx):
        embed = discord.Embed(
            title=f"📄 Skill Plates — Page {idx+1}/{len(pages)}",
            description="\n".join(f"• **{p['name']}**" for p in pages[idx]),
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=make_view(idx))

    def make_view(idx):
        view = View()

        class PlateSelect(Select):
            def __init__(self):
                super().__init__(
                    placeholder="Select a plate",
                    options=[discord.SelectOption(label=p["name"][:100], value=p["name"]) for p in pages[idx]]
                )

            async def callback(self, interaction):
                plate = next((x for x in plates if x["name"] == self.values[0]), None)
                await interaction.response.defer()
                embed = discord.Embed(title=plate["name"], description=plate["desc"], color=discord.Color.dark_gold())
                if plate["img"]:
                    file = discord.File(plate["img"], filename="thumb.png")
                    embed.set_thumbnail(url="attachment://thumb.png")
                    await interaction.followup.send(embed=embed, file=file)
                else:
                    await interaction.followup.send(embed=embed)

        view.add_item(PlateSelect())

        if len(pages) > 1:
            prev = Button(label="◀️", style=discord.ButtonStyle.secondary)
            btn_next = Button(label="▶️", style=discord.ButtonStyle.secondary)

            async def prev_page(interaction):
                await show_page(interaction, (idx - 1) % len(pages))

            async def next_page(interaction):
                await show_page(interaction, (idx + 1) % len(pages))

            prev.callback = prev_page
            btn_next.callback = next_page
            view.add_item(prev)
            view.add_item(btn_next)

        return view

    embed = discord.Embed(
        title=f"📄 Skill Plates — Page 1/{len(pages)}",
        description="\n".join(f"• **{p['name']}**" for p in pages[0]),
        color=discord.Color.blurple()
    )

    await inter.response.send_message(embed=embed, view=make_view(0))

bot.run(TOKEN)