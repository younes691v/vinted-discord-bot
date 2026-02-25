import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import json
import asyncio
import random
import os
from dotenv import load_dotenv

# ===== FLASK POUR RENDER =====
from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ===== CHARGER TOKEN =====
load_dotenv()
TOKEN = os.getenv("TOKEN")

CHANNEL_ID = 1472286338647724105  # METS TON VRAI CHANNEL ID

# ===== TES 12 LIENS =====
SEARCH_URLS = [
    "https://www.vinted.uk/catalog?search_text=nike%20phenom%20pants%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20trail%20pants%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20trail%20jacket%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20running%20pants%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20running%20jacket%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20division%20pants%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20division%20jacket%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20berlin%20pants%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20berlin%20sweater%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20always%20jacket%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20tokyo%20sweater%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050",
    "https://www.vinted.uk/catalog?search_text=nike%20tokyo%20pants%20&currency=GBP&order=newest_first&brand_ids[]=53&catalog[]=2050"
]

# ===== FILTRES =====
MAX_PRICE = 40
KEYWORDS_BLOCK = ["kids", "fake", "replica"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

# ===== SAVE SEEN ITEMS =====
def load_seen():
    try:
        with open("seen.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_seen(data):
    with open("seen.json", "w") as f:
        json.dump(data, f)

# ===== SCRAPER =====
def scrape():
    items = []

    for url in SEARCH_URLS:
        try:
            r = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(r.text, "html.parser")

            products = soup.find_all("a", {"data-testid": "item-card"})

            for p in products[:8]:
                link = "https://www.vinted.uk" + p["href"]
                title = p.get_text(strip=True)
                item_id = p["href"].split("-")[-1]

                price_tag = p.find("span")
                price = 0

                if price_tag:
                    price_text = price_tag.text.replace("£", "").strip()
                    try:
                        price = float(price_text)
                    except:
                        continue

                # ===== FILTRE PRIX =====
                if price > MAX_PRICE:
                    continue

                # ===== FILTRE MOTS BLOQUÉS =====
                if any(word in title.lower() for word in KEYWORDS_BLOCK):
                    continue

                items.append({
                    "id": item_id,
                    "title": title,
                    "url": link,
                    "price": price
                })

        except:
            continue

    return items

# ===== LOOP =====
@tasks.loop(seconds=45)
async def check_vinted():
    await bot.wait_until_ready()

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel introuvable")
        return

    seen = load_seen()
    items = scrape()

    for item in items:
        if item["id"] not in seen:

            embed = discord.Embed(
                title=item["title"],
                url=item["url"],
                description="🚨 Nouvelle annonce Nike UK",
                color=0x111111
            )

            embed.add_field(name="💰 Prix", value=f"{item['price']} GBP", inline=True)
            embed.add_field(name="🌍 Market", value="UK", inline=True)

            embed.set_footer(text="Nike Monitor • Vinted UK")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Voir l'annonce", url=item["url"]))

            await channel.send(embed=embed, view=view)

            seen.append(item["id"])
            save_seen(seen)

            await asyncio.sleep(2)

    await asyncio.sleep(random.randint(5, 12))

# ===== READY =====
@bot.event
async def on_ready():
    print(f"Connecté : {bot.user}")
    check_vinted.start()

# ===== IMPORTANT POUR RENDER =====
keep_alive()
bot.run(TOKEN)
