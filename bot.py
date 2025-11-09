import os
import re
from pathlib import Path
import discord
from discord.ext import commands
from discord import app_commands
from bs4 import BeautifulSoup
from discord.ui import View, Select, Button

# ================= CONFIG =================

TOKEN = os.getenv("PLATE_DISCORD_TOKEN")
if not TOKEN:
    print("❌ ERROR: Set environment variable PLATE_DISCORD_TOKEN")
    raise SystemExit(1)

GUILD_ID = int(os.getenv("PLATE_GUILD_ID", "0"))

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
    query_words = query.lower().split()
    scored = []

    for p in plates:
        text = (p["name"] + " " + p["desc"]).lower()
        score = 0

        for w in query_words:
            if w in text:
                score += 2
        for w in query_words:
            if any(w in word for word in text.split()):
                score += 1

        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for score, p in scored]


async def send_single(inter, plate):
    embed = discord.Embed(title=plate["name"], description=plate["desc"], color=discord.Color.dark_gold())
    file = None
    if plate["img"]:
        file = discord.File(plate["img"], filename="thumb.png")
        embed.set_thumbnail(url="attachment://thumb.png")
    await inter.response.send_message(embed=embed, file=file)


async def send_related(inter, results):
    related = results[1:4]
    if not related:
        return

    await inter.followup.send("🔍 **Similar Plates:**")

    for p in related:
        embed = discord.Embed(title=p["name"], description=p["desc"], color=discord.Color.dark_blue())
        file = None
        if p["img"]:
            file = discord.File(p["img"], filename="thumb.png")
            embed.set_thumbnail(url="attachment://thumb.png")
        await inter.followup.send(embed=embed, file=file)


# ================= READY =================

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    load_plates()

    try:
        await bot.tree.sync()
        print("✅ Global slash commands synced.")
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"⚡ Guild slash commands synced for {GUILD_ID}.")
    except Exception as e:
        print("⚠️ Slash sync failed:", e)

    await bot.change_presence(activity=discord.Game(name="!sp | /sp | /suggest"))


# ================= TEXT COMMANDS =================

@bot.command()
async def reload(ctx):
    load_plates()
    await ctx.send("🔄 Reload complete.")


@bot.command()
async def sp(ctx, *, query=None):
    if not query:
        return await ctx.send("Usage: `!sp <keywords>`")
    results = search(query)
    if not results:
        return await ctx.send("❌ No matching plates.")
    for p in results[:5]:
        embed = discord.Embed(title=p["name"], description=p["desc"], color=discord.Color.blue())
        file = None
        if p["img"]:
            file = discord.File(p["img"], filename="thumb.png")
            embed.set_thumbnail(url="attachment://thumb.png")
        await ctx.send(embed=embed, file=file)


# ================= UPDATED /sp WITH OPTIONAL FILTER =================

@bot.tree.command(name="sp", description="Browse or search plates. Type words to filter.")
@app_commands.describe(query="Optional keywords, example: 'blue trap' or 'moment bliss'")
async def slash_sp(inter, query: str = None):

    # If user typed search words, filter via scoring
    if query:
        results = search(query)
        if not results:
            return await inter.response.send_message("❌ No plates found for that search.", ephemeral=True)
        list_to_show = results
    else:
        list_to_show = plates

    PAGE_SIZE = 25
    pages = [list_to_show[i:i+PAGE_SIZE] for i in range(0, len(list_to_show), PAGE_SIZE)]
    page_index = 0

    def make_view(page):
        view = View()

        class PlateSelect(Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label=p["name"][:100], value=p["name"])
                    for p in page
                ]
                super().__init__(placeholder="Choose a plate", options=options)

            async def callback(self, interaction):
                plate = next((x for x in plates if x["name"] == self.values[0]), None)
                if not plate:
                    return await interaction.response.send_message("❌ Plate not found.", ephemeral=True)

                embed = discord.Embed(title=plate["name"], description=plate["desc"], color=discord.Color.dark_gold())
                file = None
                if plate["img"]:
                    file = discord.File(plate["img"], filename="thumb.png")
                    embed.set_thumbnail(url="attachment://thumb.png")

                await interaction.response.send_message(embed=embed, file=file)

        view.add_item(PlateSelect())

        async def prev(interaction):
            nonlocal page_index
            page_index = (page_index - 1) % len(pages)
            await interaction.response.edit_message(content=f"📄 Page {page_index+1}/{len(pages)}", view=make_view(pages[page_index]))

        async def next(interaction):
            nonlocal page_index
            page_index = (page_index + 1) % len(pages)
            await interaction.response.edit_message(content=f"📄 Page {page_index+1}/{len(pages)}", view=make_view(pages[page_index]))

        if len(pages) > 1:
            btn_prev = Button(label="◀️", style=discord.ButtonStyle.secondary)
            btn_next = Button(label="▶️", style=discord.ButtonStyle.secondary)
            btn_prev.callback = prev
            btn_next.callback = next
            view.add_item(btn_prev)
            view.add_item(btn_next)

        return view

    await inter.response.send_message(
        f"📄 Page {page_index+1}/{len(pages)} (Showing {len(list_to_show)} results)",
        view=make_view(pages[page_index]),
        ephemeral=True
    )


# ================= SUGGEST COMMAND (DROPDOWN) =================

GEM_COLORS = [
    ("🟥 Red", "Red"),
    ("🟨 Yellow", "Yellow"),
    ("🟦 Blue", "Blue"),
    ("🟪 Purple", "Purple"),
    ("🟩 Green", "Green"),
    ("⬛ Black", "Black"),
]

PLATE_TYPES = [
    ("🪤 Trap", "Trap"),
    ("💀 Botch", "Botch"),
    ("🩸 Bleed", "Bleed"),
    ("✖️ Multiply", "Multiply"),
    ("🛡️ Armor", "Armor"),
    ("💚 Heal", "Heal"),
    ("💥 Blast", "Blast"),
    ("⚡ Gain MP", "Gain MP"),
    ("🔄 Generate", "Generate"),
]


@bot.tree.command(name="suggest", description="Suggest plates by choosing gem color & effect type.")
async def suggest(inter):
    class ColorSelect(Select):
        def __init__(self):
            options = [discord.SelectOption(label=label, value=value) for label, value in GEM_COLORS]
            super().__init__(placeholder="Select Gem Color", options=options)

        async def callback(self, interaction):
            selected_color = self.values[0]

            class TypeSelect(Select):
                def __init__(self):
                    options = [discord.SelectOption(label=label, value=value) for label, value in PLATE_TYPES]
                    super().__init__(placeholder="Select Plate Type", options=options)

                async def callback(self, interaction2):
                    selected_type = self.values[0]
                    query = f"{selected_color} {selected_type}"
                    results = search(query)

                    if not results:
                        return await interaction2.response.send_message(
                            f"❌ No plates match `{selected_color} {selected_type}`.", ephemeral=True
                        )

                    await send_single(interaction2, results[0])
                    await send_related(interaction2, results)

            view2 = View()
            view2.add_item(TypeSelect())
            await interaction.response.send_message(
                f"🎨 **Color Selected:** {selected_color}\nNow choose the plate type:",
                view=view2, ephemeral=True
            )

    view = View()
    view.add_item(ColorSelect())
    await inter.response.send_message("🔍 **Let's find you a plate!**\nChoose gem color:", view=view, ephemeral=True)


bot.run(TOKEN)
