import os
import json
import random
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

POSTS_FILE = "posts.json"
CHANNELS_FILE = "channels.json"
USER_DATA_DIR = "data/user_data"
DEFAULT_SCORE = 1
POSTS_PER_PAGE = 20

def get_client_ip():
    return request.remote_addr

def user_file(ip):
    return os.path.join(USER_DATA_DIR, f"{ip}.json")

def load_user_data(ip):
    path = user_file(ip)
    if not os.path.exists(path):
        return {"visited": [], "liked": [], "disliked": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_data(ip, data):
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    with open(user_file(ip), "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_channel_score(channel):
    channels = load_json(CHANNELS_FILE)
    return channels.get(channel, {}).get("score", DEFAULT_SCORE)

def update_channel_score(channel, delta):
    channels = load_json(CHANNELS_FILE)
    if channel not in channels:
        channels[channel] = {"last_message_id": "", "score": DEFAULT_SCORE}
    channels[channel]["score"] = max(0, channels[channel].get("score", DEFAULT_SCORE) + delta)
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=2)

def get_recommended_posts(ip, limit=POSTS_PER_PAGE):
    all_posts = load_json(POSTS_FILE)
    if not all_posts:
        return []
    # فقط پست‌های دارای فایل
    media_posts = [p for p in all_posts.values() if p.get("file_url")]
    if not media_posts:
        return []
    user = load_user_data(ip)
    visited_set = set(user.get("visited", []))
    
    unseen = [p for p in media_posts if p["id"] not in visited_set]
    seen = [p for p in media_posts if p["id"] in visited_set]
    
    # الگوریتم وزنی + رندوم برای ندیده‌ها
    def weighted_random(posts, count):
        if not posts:
            return []
        # امتیاز هر پست = امتیاز کانال
        weights = [get_channel_score(p["channel"]) for p in posts]
        total = sum(weights)
        if total == 0:
            return random.sample(posts, min(count, len(posts)))
        selected = []
        temp_posts = posts[:]
        temp_weights = weights[:]
        for _ in range(min(count, len(temp_posts))):
            r = random.uniform(0, sum(temp_weights))
            acc = 0
            for i, w in enumerate(temp_weights):
                acc += w
                if r <= acc:
                    selected.append(temp_posts.pop(i))
                    temp_weights.pop(i)
                    break
        return selected
    
    # اولویت کامل با ندیده‌ها (تا limit)
    result = weighted_random(unseen, limit)
    # اگه کم آورد، از دیده‌ها پر کن (با همان روش وزنی)
    if len(result) < limit:
        needed = limit - len(result)
        result.extend(weighted_random(seen, needed))
    
    return result

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def api_status():
    total = len([p for p in load_json(POSTS_FILE).values() if p.get("file_url")])
    return jsonify({"total_posts": total})

@app.route("/api/posts")
def api_posts():
    ip = get_client_ip()
    posts = get_recommended_posts(ip)
    user = load_user_data(ip)
    liked_set = set(user.get("liked", []))
    disliked_set = set(user.get("disliked", []))
    for p in posts:
        p["liked"] = p["id"] in liked_set
        p["disliked"] = p["id"] in disliked_set
    return jsonify(posts)

@app.route("/api/view/<post_id>", methods=["POST"])
def mark_viewed(post_id):
    ip = get_client_ip()
    user = load_user_data(ip)
    if post_id not in user["visited"]:
        user["visited"].append(post_id)
        save_user_data(ip, user)
    return jsonify({"ok": True})

@app.route("/api/like/<post_id>", methods=["POST"])
def like_post(post_id):
    ip = get_client_ip()
    user = load_user_data(ip)
    data = request.get_json()
    liked = data.get("liked", False)
    disliked = data.get("disliked", False)
    # منطق لایک/دیسلایک (همان قبل)
    all_posts = load_json(POSTS_FILE)
    post = all_posts.get(post_id)
    if not post:
        return jsonify({"ok": False})
    channel = post["channel"]
    if liked and post_id not in user["liked"]:
        user["liked"].append(post_id)
        if post_id in user["disliked"]:
            user["disliked"].remove(post_id)
        update_channel_score(channel, +1)
    elif not liked and post_id in user["liked"]:
        user["liked"].remove(post_id)
        update_channel_score(channel, -1)
    if disliked and post_id not in user["disliked"]:
        user["disliked"].append(post_id)
        if post_id in user["liked"]:
            user["liked"].remove(post_id)
        update_channel_score(channel, -1)
    elif not disliked and post_id in user["disliked"]:
        user["disliked"].remove(post_id)
        update_channel_score(channel, +1)
    save_user_data(ip, user)
    return jsonify({"ok": True})

@app.route("/api/dislike/<post_id>", methods=["POST"])
def dislike_post(post_id):
    return like_post(post_id)

if __name__ == "__main__":
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=False)