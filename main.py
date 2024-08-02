import os
import nextcord
from nextcord.ext import commands
import requests
from bs4 import BeautifulSoup
import re
import time

intents = nextcord.Intents.default()
intents.message_content = True  # Mesaj içeriği niyetini etkinleştir

bot = commands.Bot(command_prefix='/', intents=intents)

WEBHOOK_URL_173 = "https://discord.com/api/webhooks/1268702067376001034/Z47dW23MEq364xRAr5Zjv8lTnb7BHizO7OF2lp48i-l5Gfs0F-PlMWFg97TQjOCG50Fk"
WEBHOOK_URL_174 = "https://discord.com/api/webhooks/1268702478367461490/U0Q88RXhWazvWZKoHaq5qun1dBcQVkQ7DfeBLNSUuHjyG2jq9wmeWjNqVGXUNBwRuZYx"  # Ek webhook URL'si
DISCORD_BOT_TOKEN = "MTI2NzU0NjQ4MTQ2NDg0MDI2Ng.GGLBsg.FHUZeCQuoZ_lEckbTNmU4Jl_aB_GaZLtKXq21w"

# Function to fetch and parse HTML
def fetch_and_parse_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    server_data = []
    for row in soup.find_all('tr')[2:]:
        cols = row.find_all('td')
        if len(cols) >= 4:
            ip_full = cols[0].text.strip()
            server_name = cols[1].text.strip()
            map_name = cols[2].text.strip()
            players = cols[3].text.strip()

            ip_match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ip_full)
            ip = ip_match.group(1) if ip_match else 'Unknown'

            dns = re.sub(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '', ip_full).strip()
            if dns.startswith('/'):
                dns = dns[1:]

            server_data.append({
                'IP': ip,
                'DNS': dns,
                'Server Adı': server_name,
                'Harita': map_name,
                'Oyuncu': players
            })
    return server_data

# Function to send data to Discord webhook
def send_to_discord(data, webhook_url):
    def chunk_data(data, chunk_size):
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    chunks = list(chunk_data(data, 10))
    for chunk in chunks:
        fields = []
        for item in chunk:
            fields.append({
                "name": "Sunucu Bilgisi",
                "value": f"Sunucu: {item['Server Adı']}\nHarita: {item['Harita']}\nOyuncu: {item['Oyuncu']}\nIPler: {item['IP']} / {item['DNS']}",
                "inline": False
            })

        embed = {
            "description": "Sunucu Listesi",
            "color": 15258703,
            "fields": fields
        }

        payload = {
            "embeds": [embed]
        }

        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send webhook: {e}")
        else:
            print("Webhook sent successfully.")

        # Rate limiting için bekleme süresi
        time.sleep(2)  # 2 saniye bekle

# /sorgula komutu
@bot.slash_command(name="sorgula", description="Serverleri Sorgula [173-174]")
async def sorgula(ctx, ip: str):
    # IP'yi kontrol et
    if ip not in ["173", "174"]:
        await ctx.send("Dur Lan! 173 veya 174 yaz.")
        return

    await ctx.send(f"{ip} dekileri...")
    url = f"https://www.oyunyoneticisi.com/server/cs16ipler_{ip}.txt"
    html_content = fetch_and_parse_html(url)
    server_data = parse_html(html_content)

    # IP'ye göre doğru webhook'u belirle
    if ip == "173":
        send_to_discord(server_data, WEBHOOK_URL_173)
        channel_url = "https://discord.com/channels/1268679931446034594/1268699712177967135"
    elif ip == "174":
        send_to_discord(server_data, WEBHOOK_URL_174)  # Ek webhook
        channel_url = "https://discord.com/channels/1268679931446034594/1268699729349578783"

    await ctx.send(f"Sunucu bilgileri gönderildi {channel_url}.")

# /top15time komutu
@bot.slash_command(name="top15time", description="Top 15 zaman bilgilerini getir.")
async def top15time(ctx, ip: str):
    await ctx.send(f"{ip} adresi için top 15 zaman bilgilerini getiriyorum...")
    # Bu komut için özel script'i buraya ekleyin
    await ctx.send("Top 15 zaman bilgileri gönderildi.")

# Botun tokeni ile botu çalıştır
bot.run(DISCORD_BOT_TOKEN)
