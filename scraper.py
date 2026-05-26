import os
import re
import json
import time
import requests
from datetime import datetime

MIRRORS_FILE = "mirrors.txt"
POSTS_FILE = "posts.json"
CHANNELS_FILE = "channels.json"
API_BASE = "https://splus.ir/srvcs-app/v1/json/7743461522282941752/03a576adcc076d93276516ec7355f28b/channel/archive"
REQUEST_DELAY = 1
MAX_LIMIT = 30
REQUEST_TIMEOUT = 10  # seconds

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Referer": "https://splus.ir/"
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def load_json(file, default=None):
    if not os.path.exists(file):
        return default if default is not None else {}
    try:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return default if default is not None else {}
            return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return default if default is not None else {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_and_save_posts(new_posts_dict):
    current = load_json(POSTS_FILE, {})
    changed = False
    for pid, post in new_posts_dict.items():
        if pid not in current:
            current[pid] = post
            changed = True
    if changed:
        save_json(POSTS_FILE, current)
        log(f"Saved {len(new_posts_dict)} new posts")

def clean_text(raw_text):
    if not raw_text:
        return ""
    text = re.sub(r'https?://\S+', '', raw_text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def fetch_messages_with_retry(channel_id, last_message_id=None, limit=MAX_LIMIT):
    body = {"channel_id": str(channel_id), "limit": limit}
    if last_message_id is not None:
        body["message_id"] = str(last_message_id)
    
    while True:
        try:
            log(f"POST {API_BASE} | channel={channel_id} last_id={last_message_id}")
            response = requests.post(API_BASE, headers=HEADERS, json=body, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            messages = data.get("messages", [])
            log(f"Received {len(messages)} messages")
            return messages
        except requests.exceptions.Timeout:
            print("\n" + "="*60)
            print("⚠️  REQUEST TIMEOUT / تایم اوت درخواست")
            print(f"No response in {REQUEST_TIMEOUT} seconds.")
            print("لطفاً اتصال اینترنت را بررسی کنید.")
            print("="*60)
        except requests.exceptions.ConnectionError:
            print("\n" + "="*60)
            print("⚠️  CONNECTION ERROR / خطای اتصال")
            print("Cannot reach the server.")
            print("سرور در دسترس نیست.")
            print("="*60)
        except Exception as e:
            print("\n" + "="*60)
            print(f"⚠️  UNKNOWN ERROR / خطای ناشناخته: {e}")
            print("="*60)
        
        ans = input("\nRetry? (y=yes / n=skip / ENTER=yes): ").strip().lower()
        if ans in ['y', 'yes', '']:
            print("Retrying... / تلاش مجدد...")
            time.sleep(2)
            continue
        else:
            print("Skipping this request... / رد شدن از این درخواست...")
            return None

def get_existing_message_ids_for_channel(channel_name):
    all_posts = load_json(POSTS_FILE, {})
    ids = set()
    for pid, post in all_posts.items():
        if post.get("channel") == channel_name:
            try:
                ids.add(int(post["message_id"]))
            except:
                pass
    return ids

def get_smallest_existing_id(channel_name):
    ids = get_existing_message_ids_for_channel(channel_name)
    return min(ids) if ids else None

def get_largest_existing_id(channel_name):
    ids = get_existing_message_ids_for_channel(channel_name)
    return max(ids) if ids else None

def convert_to_post(msg, channel_name):
    file_info = msg.get("file", {})
    file_url = file_info.get("url", "")
    if not file_url:
        return None
    msg_id = msg.get("message_id")
    if not msg_id:
        return None
    post_id = f"{channel_name}_{msg_id}"
    clean_text_content = clean_text(msg.get("text", ""))
    views_raw = msg.get("visitCount", "0")
    try:
        views = int(views_raw.replace(",", ""))
    except:
        views = 0
    time_ago = msg.get("when", "")
    return {
        "id": post_id,
        "channel": channel_name,
        "message_id": str(msg_id),
        "file_url": file_url,
        "text": clean_text_content,
        "views": views,
        "time_ago": time_ago,
        "visited": False,
        "liked": False,
        "disliked": False,
        "created_at": datetime.now().isoformat()
    }

def get_all_messages_for_channel(channel_name, channel_id, full_archive=False):
    log(f"Processing channel '{channel_name}' (id: {channel_id}) - full_archive={full_archive}")
    
    existing_ids = get_existing_message_ids_for_channel(channel_name)
    largest_existing = get_largest_existing_id(channel_name)
    smallest_existing = get_smallest_existing_id(channel_name)
    
    # دریافت جدیدترین پیام‌ها
    log("Fetching most recent messages...")
    messages = fetch_messages_with_retry(channel_id, last_message_id=None, limit=MAX_LIMIT)
    if messages is None:
        log("Failed to get initial messages. Skipping channel.")
        return 0, None
    if not messages:
        log("No messages found.")
        return 0, None
    
    newest_id = 0
    oldest_id = None
    for msg in messages:
        mid = msg.get("message_id")
        if mid:
            if mid > newest_id:
                newest_id = mid
            if oldest_id is None or mid < oldest_id:
                oldest_id = mid
    
    # ذخیره پیام‌های جدید (بزرگتر از largest_existing)
    new_posts = {}
    for msg in messages:
        mid = msg.get("message_id")
        if mid and (largest_existing is None or mid > largest_existing):
            post = convert_to_post(msg, channel_name)
            if post:
                new_posts[post["id"]] = post
    if new_posts:
        add_and_save_posts(new_posts)
        log(f"First batch: saved {len(new_posts)} new posts (newest_id={newest_id})")
    
    total_new = len(new_posts)
    
    if full_archive:
        current_oldest = oldest_id
        target_oldest = smallest_existing if smallest_existing is not None else 0
        consecutive_empty = 0
        
        while True:
            if current_oldest <= target_oldest:
                log(f"Reached existing oldest message_id {target_oldest}. Stopping.")
                break
            next_id = current_oldest - 1
            if next_id < 1:
                break
            log(f"Fetching older messages (last_id={next_id})...")
            messages = fetch_messages_with_retry(channel_id, last_message_id=next_id, limit=MAX_LIMIT)
            if messages is None:
                log("No messages received (None). Stopping.")
                break
            if not messages:
                log("Empty messages list. Stopping.")
                break
            
            new_oldest = None
            new_posts = {}
            for msg in messages:
                mid = msg.get("message_id")
                if mid:
                    if new_oldest is None or mid < new_oldest:
                        new_oldest = mid
                    if mid not in existing_ids:
                        post = convert_to_post(msg, channel_name)
                        if post:
                            new_posts[post["id"]] = post
            if new_posts:
                add_and_save_posts(new_posts)
                total_new += len(new_posts)
                log(f"Older batch: saved {len(new_posts)} new posts, now oldest_id={new_oldest}")
                # به‌روزرسانی existing_ids
                for pid in new_posts:
                    existing_ids.add(int(new_posts[pid]["message_id"]))
                consecutive_empty = 0
            else:
                consecutive_empty += 1
                log(f"No new media posts in this batch. Consecutive empty: {consecutive_empty}")
                if consecutive_empty >= 3:
                    log("Stopping because no new media posts found in last 3 batches.")
                    break
            
            if new_oldest is None or new_oldest >= current_oldest:
                log("No progress in oldest_id. Stopping.")
                break
            current_oldest = new_oldest
            time.sleep(REQUEST_DELAY)
    
    if largest_existing is not None and newest_id <= largest_existing:
        last_saved_id = largest_existing
    else:
        last_saved_id = newest_id
    
    log(f"Finished {channel_name}. New posts added: {total_new}. Last message_id: {last_saved_id}")
    return total_new, last_saved_id

def update_channel_new_posts(channel_name, channel_id, last_saved_id):
    log(f"Checking new posts for '{channel_name}' (last saved id: {last_saved_id})")
    messages = fetch_messages_with_retry(channel_id, last_message_id=None, limit=MAX_LIMIT)
    if messages is None:
        return 0, last_saved_id
    if not messages:
        return 0, last_saved_id
    new_posts = {}
    newest_id = last_saved_id
    for msg in messages:
        mid = msg.get("message_id")
        if mid and mid > last_saved_id:
            post = convert_to_post(msg, channel_name)
            if post:
                new_posts[post["id"]] = post
                if mid > newest_id:
                    newest_id = mid
    if new_posts:
        add_and_save_posts(new_posts)
        log(f"Found and saved {len(new_posts)} new posts")
        return len(new_posts), newest_id
    else:
        log("No new posts found")
        return 0, last_saved_id

def scrape_all_channels(full_archive=False):
    if not os.path.exists(MIRRORS_FILE):
        log("mirrors.txt not found!")
        return
    with open(MIRRORS_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    channels = []
    for line in lines:
        if ";" in line:
            parts = line.split(";", 1)
            channels.append((parts[0].strip(), parts[1].strip()))
        else:
            log(f"Invalid line in mirrors.txt (expected 'name;id'): {line}")
    if not channels:
        log("No valid channels found")
        return
    
    channels_info = load_json(CHANNELS_FILE, {})
    total_new = 0
    
    for ch_name, ch_id in channels:
        log(f"\n{'='*50}")
        if full_archive:
            log(f"FULL ARCHIVE for {ch_name}")
            added, new_last_id = get_all_messages_for_channel(ch_name, ch_id, full_archive=True)
            if new_last_id is not None:
                channels_info[ch_name] = {
                    "channel_id": ch_id,
                    "last_message_id": new_last_id,
                    "last_update": datetime.now().isoformat()
                }
                save_json(CHANNELS_FILE, channels_info)
            total_new += added
        else:
            log(f"UPDATE for {ch_name}")
            last_id = channels_info.get(ch_name, {}).get("last_message_id", 0)
            added, new_last_id = update_channel_new_posts(ch_name, ch_id, last_id)
            if new_last_id > last_id:
                channels_info[ch_name] = {
                    "channel_id": ch_id,
                    "last_message_id": new_last_id,
                    "last_update": datetime.now().isoformat()
                }
                save_json(CHANNELS_FILE, channels_info)
            total_new += added
        time.sleep(REQUEST_DELAY)
    
    log(f"\n{'='*50}")
    log(f"Scrape completed. Total new posts added: {total_new}")

if __name__ == "__main__":
    import sys
    full = "--full" in sys.argv
    if full:
        log("Starting FULL ARCHIVE mode - will fetch all messages (avoiding duplicates)")
    else:
        log("Starting UPDATE mode - fetching only new posts")
    scrape_all_channels(full_archive=full)