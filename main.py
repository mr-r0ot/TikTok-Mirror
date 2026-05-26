"""
Coded by Nicola
https://github.com/mr-r0ot/TikTok-Mirror/
"""

import os
import sys
import subprocess
import socket
import threading
import time
import webbrowser
import json
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# ========== توابع سیستمی ==========
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def start_flask():
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    return subprocess.Popen([sys.executable, "app.py"], creationflags=flags)

def start_scraper():
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    return subprocess.Popen([sys.executable, "scraper.py"], creationflags=flags)

def kill_processes_by_name(*names):
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                for name in names:
                    if name in cmdline:
                        proc.terminate()
                        time.sleep(0.5)
                        if proc.is_running():
                            proc.kill()
                        break
            except:
                pass
    except ImportError:
        pass  # اگر psutil نصب نیست، فقط نادیده بگیر

def export_all_posts():
    posts_file = "posts.json"
    if not os.path.exists(posts_file):
        messagebox.showerror("خطا", "فایل posts.json یافت نشد.")
        return

    with open(posts_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_posts = [p for p in data.values() if p.get("file_url")]
    if not all_posts:
        messagebox.showerror("خطا", "هیچ پست دارای عکس یا ویدیویی یافت نشد.")
        return

    import random
    random.shuffle(all_posts)  # ترتیب رندوم

    posts_per_page = 50
    pages = [all_posts[i:i+posts_per_page] for i in range(0, len(all_posts), posts_per_page)]

    # انتخاب پوشه ذخیره
    folder = filedialog.askdirectory(title="انتخاب پوشه برای ذخیره صفحات HTML")
    if not folder:
        return

    # تابع تولید یک صفحه
    def save_page(page_posts, page_num, total_pages):
        posts_json = json.dumps(page_posts, ensure_ascii=False)
        html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>تیک‌تاک آفلاین - صفحه {page_num}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #000; font-family: system-ui; overflow-y: scroll; height: 100vh; scroll-snap-type: y mandatory; }}
        .video-card {{ height: 100vh; width: 100%; position: relative; background: #000; display: flex; align-items: center; justify-content: center; scroll-snap-align: start; }}
        .video-player {{ width: 100%; height: 100%; object-fit: contain; }}
        .info {{ position: absolute; bottom: 100px; left: 16px; color: white; text-shadow: 0 1px 2px black; z-index: 10; }}
        .channel {{ font-weight: bold; font-size: 16px; }}
        .caption {{ font-size: 14px; opacity: 0.9; }}
        .views {{ font-size: 12px; margin-top: 4px; }}
        .controls {{ position: fixed; bottom: 120px; right: 20px; display: flex; gap: 15px; z-index: 30; }}
        .btn {{ background: rgba(0,0,0,0.7); border: none; color: white; padding: 8px 18px; border-radius: 40px; font-size: 14px; cursor: pointer; }}
        .paginator {{ position: fixed; bottom: 20px; left: 20px; background: rgba(0,0,0,0.5); color: white; padding: 6px 15px; border-radius: 30px; font-size: 13px; z-index: 30; }}
        .paginator a {{ color: #ff2a5e; text-decoration: none; margin: 0 5px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div class="controls">
        <button class="btn" id="unmuteBtn">🔊 فعال‌سازی صدا</button>
    </div>
    <div class="paginator">
        صفحه {page_num} از {total_pages}
        {"<a href='page_{}.html'>⏮ قبلی</a>".format(page_num-1) if page_num > 1 else ""}
        {"<a href='page_{}.html'>بعدی ▶</a>".format(page_num+1) if page_num < total_pages else ""}
    </div>
    <script>
        const posts = {posts_json};
        let soundEnabled = false;
        let currentVideo = null;
        const container = document.getElementById('container');
        const unmuteBtn = document.getElementById('unmuteBtn');
        
        unmuteBtn.onclick = () => {{
            soundEnabled = true;
            unmuteBtn.style.display = 'none';
            if (currentVideo) currentVideo.muted = false;
        }};
        
        function formatNumber(n) {{
            if (n >= 1e6) return (n/1e6).toFixed(1)+'M';
            if (n >= 1000) return (n/1000).toFixed(1)+'K';
            return n;
        }}
        
        for (let post of posts) {{
            const card = document.createElement('div');
            card.className = 'video-card';
            const isVideo = /\\.(mp4|webm|mov)/i.test(post.file_url) || post.file_url.includes('video') || post.file_url.includes('/download/');
            const media = isVideo ?
                `<video class="video-player" src="${{post.file_url}}" muted autoplay loop playsinline preload="metadata"></video>` :
                `<img class="video-player" src="${{post.file_url}}" loading="lazy">`;
            const viewsText = post.views ? formatNumber(post.views) : '';
            card.innerHTML = `
                ${{media}}
                <div class="info">
                    <div class="channel">@${{post.channel}}</div>
                    <div class="caption">${{post.text || ''}}</div>
                    <div class="views">${{viewsText}}</div>
                </div>
            `;
            container.appendChild(card);
            const video = card.querySelector('video');
            if (video) {{
                video.muted = true;
                video.play().catch(e=>{{}});
                // مدیریت صدا فقط برای ویدیوی فعال
                const obs = new IntersectionObserver((entries) => {{
                    entries.forEach(entry => {{
                        if (entry.isIntersecting) {{
                            if (currentVideo && currentVideo !== video) currentVideo.muted = true;
                            currentVideo = video;
                            if (soundEnabled) currentVideo.muted = false;
                            else currentVideo.muted = true;
                        }}
                    }});
                }}, {{ threshold: 0.6 }});
                obs.observe(card);
            }}
        }}
    </script>
</body>
</html>"""
        filename = os.path.join(folder, f"page_{page_num}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

    total = len(pages)
    for i, page_posts in enumerate(pages, start=1):
        save_page(page_posts, i, total)

    index_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>خروجی تیک‌تاک آفلاین</title></head>
<body style="background:#000; color:white; text-align:center; padding-top:50px;">
<h1>📱 خروجی تیک‌تاک آفلاین</h1>
<p>تعداد کل پست‌ها: {len(all_posts)}</p>
<p>تعداد صفحات: {total}</p>
<a href="page_1.html" style="color:#ff2a5e; font-size:24px;">شروع از صفحه 1</a>
</body>
</html>"""
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    messagebox.showinfo("موفق", f"خروجی در پوشه {folder} ذخیره شد.\nفایل index.html را باز کنید.")
    os.startfile(folder) if sys.platform == 'win32' else webbrowser.open(folder)

# ========== کلاس اصلی برنامه ==========
class ModernLauncher:
    def __init__(self, root):
        self.root = root
        root.title("TikTok Mirror Engine")
        root.geometry("600x520")
        root.configure(bg="#0f0f1a")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.exit_app)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#0f0f1a", foreground="#cccccc", font=("Segoe UI", 10))
        style.configure("TButton", background="#1e2a3e", foreground="white", borderwidth=0, focusthickness=0, font=("Segoe UI", 10, "bold"))
        style.map("TButton", background=[("active", "#e94560")])

        self.create_header()
        main_frame = tk.Frame(root, bg="#0f0f1a")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)

        local_ip = get_local_ip()
        self.create_info_box(main_frame, "📍 دسترسی محلی", "http://127.0.0.1:5000")
        self.create_info_box(main_frame, "🌐 دسترسی شبکه", f"http://{local_ip}:5000" if local_ip != "127.0.0.1" else "همان آدرس بالا")

        status_frame = tk.Frame(main_frame, bg="#1a1a2e", height=60)
        status_frame.pack(fill="x", pady=15)
        status_frame.pack_propagate(False)
        self.status_label = tk.Label(status_frame, text="⏳ در حال راه‌اندازی سرویس‌ها...", font=("Segoe UI", 10, "bold"), fg="#ffaa44", bg="#1a1a2e")
        self.status_label.pack(expand=True)

        btn_frame = tk.Frame(main_frame, bg="#0f0f1a")
        btn_frame.pack(fill="x", pady=10)

        tk.Button(btn_frame, text="🌍 باز کردن مرورگر", command=self.open_browser, bg="#e94560", fg="white", font=("Segoe UI", 11, "bold"), bd=0, padx=20, pady=8, cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_frame, text="📦 خروجی HTML آفلاین (صفحه‌بندی شده)", command=export_all_posts, bg="#2d2d44", fg="white", font=("Segoe UI", 11), bd=0, padx=20, pady=8, cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ خروج", command=self.exit_app, bg="#2d2d44", fg="white", font=("Segoe UI", 11), bd=0, padx=20, pady=8, cursor="hand2").pack(side="right", padx=5)

        self.flask_proc = None
        self.scraper_proc = None
        self.start_services()

    def create_header(self):
        header = tk.Frame(self.root, bg="#1a1a2e", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🎬 TikTok Mirror Engine", font=("Segoe UI", 20, "bold"), fg="#e94560", bg="#1a1a2e").pack(pady=20)

    def create_info_box(self, parent, title, url):
        frame = tk.Frame(parent, bg="#1a1a2e", relief="flat", bd=1, highlightthickness=1, highlightcolor="#2d2d44")
        frame.pack(fill="x", pady=6)
        tk.Label(frame, text=title, font=("Segoe UI", 10, "bold"), fg="#cccccc", bg="#1a1a2e").pack(anchor="w", padx=10, pady=(5,0))
        entry = tk.Entry(frame, font=("Consolas", 11), fg="#00ffaa", bg="#0a0a1a", bd=0, relief="flat")
        entry.insert(0, url)
        entry.config(state="readonly")
        entry.pack(fill="x", padx=10, pady=(0,5))

    def start_services(self):
        def run():
            kill_processes_by_name("app.py", "scraper.py")
            self.flask_proc = start_flask()
            time.sleep(1)
            self.scraper_proc = start_scraper()
            self.root.after(0, lambda: self.status_label.config(text="✅ Flask و اسکرپر در حال اجرا هستند", fg="#a0ffa0"))
        threading.Thread(target=run, daemon=True).start()

    def open_browser(self):
        webbrowser.open("http://127.0.0.1:5000")

    def exit_app(self):
        kill_processes_by_name("app.py", "scraper.py")
        if self.flask_proc and self.flask_proc.poll() is None:
            self.flask_proc.terminate()
        if self.scraper_proc and self.scraper_proc.poll() is None:
            self.scraper_proc.terminate()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    os.makedirs("data/user_data", exist_ok=True)
    if not os.path.exists("mirrors.txt"):
        with open("mirrors.txt", "w") as f:
            f.write("# لینک کانال‌های خود را اینجا قرار دهید (هر خط یک لینک)\n")
    root = tk.Tk()
    app = ModernLauncher(root)
    root.mainloop()