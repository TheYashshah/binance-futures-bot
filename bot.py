import requests
from datetime import datetime, timedelta
import re
import time
import os

BOT_TOKEN = "8245776152:AAGt7OtJFZkd6GiUXOxoQvOIQzY0Lt3Jb0o"
CHAT_ID = "897811407"
LAST_IDS_FILE = "last_ids.txt"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Sent to Telegram!")
        else:
            print(f"⚠️ Telegram send error: {r.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def get_latest_announcements(limit=10):
    url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
    params = {"type": "1", "catalogId": "48", "pageNo": "1", "pageSize": str(limit)}
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data["data"]["catalogs"][0]["articles"]

def read_last_ids():
    if os.path.exists(LAST_IDS_FILE):
        with open(LAST_IDS_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()

def write_last_ids(ids_set):
    with open(LAST_IDS_FILE, "w") as f:
        f.write("\n".join(ids_set))

def process_and_send(article):
    title = article["title"]
    link = f"https://www.binance.com/en/support/announcement/{article['code']}"
    release_time = article["releaseDate"]

    utc_time = datetime.utcfromtimestamp(release_time / 1000.0)
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    publish_time_str = ist_time.strftime("%Y-%m-%d %H:%M:%S")

    listing_date_match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", title)
    if listing_date_match:
        listing_date_utc_str = listing_date_match.group(1)
        try:
            listing_datetime_utc = datetime.strptime(listing_date_utc_str + " 08:00", "%Y-%m-%d %H:%M")
            listing_datetime_ist = listing_datetime_utc + timedelta(hours=5, minutes=30)
            listing_date_str = listing_datetime_ist.strftime("%Y-%m-%d %H:%M")
        except:
            listing_date_str = "Error parsing date"
    else:
        listing_date_str = "Not found"

    msg = f"🆕 *New Binance Futures Announcement!*\n\n" \
          f"📢 {title}\n" \
          f"🕒 Published (IST): {publish_time_str}\n" \
          f"📅 Listing Date (IST est.): {listing_date_str}\n" \
          f"🔗 [View Announcement]({link})"

    send_telegram_message(msg)

print("🚀 Binance Futures Monitor started... (checks every 12 hours)")

while True:
    try:
        articles = get_latest_announcements(limit=10)
        last_ids = read_last_ids()
        new_ids_found = False

        for article in reversed(articles):  # oldest first
            if str(article["id"]) not in last_ids:
                process_and_send(article)
                last_ids.add(str(article["id"]))
                new_ids_found = True

        if new_ids_found:
            write_last_ids(last_ids)
        else:
            print("ℹ️ No new announcements.")

    except Exception as e:
        print(f"❌ Error: {e}")

    time.sleep(43200)  # 12 hours