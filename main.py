import os
import nextcord
from nextcord.ext import commands
import requests
from bs4 import BeautifulSoup
import re
import time
import subprocess

# İki kısmı olan tokenları birleştirerek tam tokeni oluştur
PART_1 = "MTI2NzU0NjQ4MTQ2NDg0MDI2Ng"
PART_2 = "GmoMpj._87ir4HG_2H6rmf0Sbjy6tXa51BBqLh2LEusag"
DISCORD_BOT_TOKEN = f"{PART_1}.{PART_2}"

intents = nextcord.Intents.default()
intents.message_content = True  # Mesaj içeriği niyetini etkinleştir

bot = commands.Bot(command_prefix='/', intents=intents)

WEBHOOK_URL_173 = "https://discord.com/api/webhooks/1268702067376001034/Z47dW23MEq364xRAr5Zjv8lTnb7BHizO7OF2lp48i-l5Gfs0F-PlMWFg97TQjOCG50Fk"
WEBHOOK_URL_174 = "https://discord.com/api/webhooks/1268702478367461490/U0Q88RXhWazvWZKoHaq5qun1dBcQVkQ7DfeBLNSUuHjyG2jq9wmeWjNqVGXUNBwRuZYx"
TOP15TIME_WEBHOOK_URL = "https://discord.com/api/webhooks/1268838133408202843/mSp42jGBQLcLp9BQee45YYIcY1aZcv7xLfNq48H9yPOeP8Jb08tDtQTsuQK9qJ5BPhQ6"
AKTIF_WEBHOOK_URL = "https://discord.com/api/webhooks/1268878901216677920/sqJoMJIaIDaUK8sVUzJiaSSUesGTaJqlMZKlxtUNwbH8IHPmTdFLvA7133Um4-Pswq09"

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

def fetch_top15time_data(url, ip_suffix):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Hata varsa bir istisna fırlatır

        # HTML içeriğini ayrıştırın
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'table1'})
        rows = table.find_all('tr')

        # Embed formatında veri hazırlayın
        embed_content = '|NO|   |    👤NICK🔗     |     ⌛DAKIKA🕰️   | \n'
        embed_content += '---------------------------------------------\n'

        for row in rows[1:]:  # İlk satır başlık satırıdır
            cols = row.find_all('td')
            sıra = cols[0].text
            nick = cols[1].text
            dakika = cols[2].text
            embed_content += f"{sıra} | {nick} | {dakika} dakika\n"

        # Webhook'a gönderim
            payload = {
                'embeds': [
                    {
                        'title': f'Serverda Oynama Süreleri - {ip_suffix}',
                        'description': f"```{embed_content}```",
                        'color': 0x00ff00,  # Yeşil renk kodu, isteğe bağlı
                        'footer': {
                            "text": "VERILER 10 DAKIKA GECIKMELI [ULAN SERHAT KAVAK!!!] -slave"
                        }
                    }
                ]
            }
        
        discord_response = requests.post(TOP15TIME_WEBHOOK_URL, json=payload)
        discord_response.raise_for_status()  # Hata varsa bir istisna fırlatır

        print("Veriler başarıyla gönderildi.")

    except requests.exceptions.RequestException as e:
        print(f"Bir hata oluştu: {e}")

def fetch_active_players(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Hata varsa bir istisna fırlatır
        return response.text.strip()
    except requests.RequestException as e:
        print(f"Bir hata oluştu: {e}")
        return "Bilgi alınamadı"

def send_active_players_to_discord(active_players_text, webhook_url):
    embed = {
        "title": f"👥AKTIF OYUNCULAR👥 : {active_players_text}",
        "color": 0x0000FF,  # Mavi renk kodu (hexadecimal formatta)
        "image": {
            "url": "https://imgur.com/wv2kLot.gif"  # Resim URL'si
        },
        "footer": {
            "text": "-slave"  # Footer metni
        }
    }

    payload = {
        "embeds": [embed]
    }

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Webhook gönderim hatası: {e}")
    else:
        print("Aktif oyuncu sayısı başarıyla gönderildi.")

# /sorgula komutu
@bot.slash_command(name="sorgula", description="Serverleri Sorgula [173-174]")
async def sorgula(ctx, ip: str):
    if ip not in ["173", "174"]:
        await ctx.send("Dur Lan! 173 veya 174 yaz.")
        return

    await ctx.send(f"{ip} dekileri sorguluyorum...")
    url = f"https://www.oyunyoneticisi.com/server/cs16ipler_{ip}.txt"
    html_content = fetch_and_parse_html(url)
    server_data = parse_html(html_content)

    if ip == "173":
        send_to_discord(server_data, WEBHOOK_URL_173)
        channel_url = "https://discord.com/channels/1268679931446034594/1268699712177967135"
    elif ip == "174":
        send_to_discord(server_data, WEBHOOK_URL_174)  # Ek webhook
        channel_url = "https://discord.com/channels/1268679931446034594/1268699729349578783"

    await ctx.send(f"Sunucu bilgileri gönderildi bak lan şuraya > {channel_url}.")

# /top15time komutu
@bot.slash_command(name="top15time", description="Top15 zaman bilgilerini getir. [173.254,174-254]")
async def top15time(ctx, ip: str):
    if not re.match(r'^(173|174)\.\d+$', ip):
        await ctx.send("Dur Lan! 173.255-174.255 aralığında yaz. Ornek : 173.100")
        return

    await ctx.send(f"{ip} adresindeki serverin top15 zaman bilgilerini getiriyorum...")

    ip_parts = ip.split('.')
    base_url = "https://cs16playedtime.oyunyoneticisi.com/rank/suremotd.php?ip="
    data_url = f"{base_url}95.173.{ip_parts[0]}.{ip_parts[1]}" if ip_parts[0] == "173" else f"{base_url}95.173.{ip_parts[0]}.{ip_parts[1]}"

    fetch_top15time_data(data_url, ip_parts[1])
    channel_url = "https://discord.com/channels/1268679931446034594/1268699841400143986"
    await ctx.send(f"Sunucu bilgileri gönderildi bak lan şuraya > {channel_url}.")

# /aktif komutu
@bot.slash_command(name="aktif", description="Aktif oyuncu sayısını getir.")
async def aktif(ctx):
    channel_url = "https://discord.com/channels/1268679931446034594/1268873568960380969"
    players_url = 'https://www.oyunyoneticisi.com/server/ana_players.txt'
    active_players_text = fetch_active_players(players_url)
    send_active_players_to_discord(active_players_text, AKTIF_WEBHOOK_URL)
    await ctx.send(f"Aktif kullanici sayisi gönderildi bak lan şuraya > {channel_url}.")

bot.run(DISCORD_BOT_TOKEN)
