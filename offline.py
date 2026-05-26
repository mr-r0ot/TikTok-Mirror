import os
import json
import random
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox

def generate_offline():
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

    for p in all_posts:
        p["channel_score"] = 1  
        p["liked"] = False
        p["disliked"] = False
        p["visited"] = False


    channels_file = "channels.json"
    if os.path.exists(channels_file):
        with open(channels_file, "r", encoding="utf-8") as f:
            channels_data = json.load(f)
        for p in all_posts:
            ch = p["channel"]
            if ch in channels_data:
                p["channel_score"] = channels_data[ch].get("score", 1)


    random.shuffle(all_posts)


    file_path = filedialog.asksaveasfilename(
        defaultextension=".html",
        filetypes=[("HTML files", "*.html")],
        title="ذخیره خروجی آفلاین تیک‌تاک"
    )
    if not file_path:
        return

    posts_json = json.dumps(all_posts, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>آفلاین تیک‌تاک آینه‌ای - هوشمند</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: #000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            overflow: hidden;
            height: 100vh;
        }}
        .tiktok-container {{
            height: 100vh;
            overflow-y: scroll;
            scroll-snap-type: y mandatory;
            scroll-behavior: smooth;
        }}
        .video-item {{
            scroll-snap-align: start;
            height: 100vh;
            width: 100%;
            position: relative;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .video-player {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        .video-info {{
            position: absolute;
            bottom: 100px;
            left: 16px;
            right: 100px;
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
            z-index: 10;
        }}
        .channel-name {{
            font-weight: bold;
            margin-bottom: 4px;
            font-size: 16px;
        }}
        .caption {{
            font-size: 14px;
            opacity: 0.9;
            max-height: 60px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}
        .actions {{
            position: absolute;
            bottom: 100px;
            right: 16px;
            display: flex;
            flex-direction: column;
            gap: 24px;
            z-index: 10;
        }}
        .action-btn {{
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(8px);
            border: none;
            color: white;
            font-size: 32px;
            width: 52px;
            height: 52px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: transform 0.1s ease;
        }}
        .action-btn:active {{
            transform: scale(0.92);
        }}
        .action-btn.active {{
            color: #ff2a5e;
        }}
        .views {{
            font-size: 12px;
            text-align: center;
            margin-top: 6px;
            font-weight: 500;
            color: white;
            text-shadow: 0 0 2px black;
        }}
        .video-controls {{
            position: absolute;
            bottom: 30%;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 30px;
            z-index: 20;
            background: rgba(0,0,0,0.4);
            backdrop-filter: blur(12px);
            padding: 8px 24px;
            border-radius: 60px;
            opacity: 0;
            transition: opacity 0.25s;
            pointer-events: none;
        }}
        .video-item:hover .video-controls {{
            opacity: 1;
            pointer-events: auto;
        }}
        .ctrl-btn {{
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            font-size: 28px;
            width: 52px;
            height: 52px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: 0.2s;
        }}
        .ctrl-btn:hover {{
            background: rgba(255,255,255,0.4);
            transform: scale(1.05);
        }}
        .loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: #000;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 100;
            color: white;
            gap: 20px;
        }}
        .spinner {{
            width: 48px;
            height: 48px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        .status-bar {{
            position: fixed;
            bottom: 16px;
            left: 16px;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(8px);
            color: #fff;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-family: monospace;
            z-index: 20;
        }}
        .sound-prompt {{
            position: fixed;
            bottom: 120px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            backdrop-filter: blur(10px);
            color: white;
            padding: 8px 18px;
            border-radius: 40px;
            font-size: 14px;
            font-weight: bold;
            z-index: 30;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.3);
            transition: 0.2s;
        }}
        .sound-prompt:hover {{
            background: #ff2a5e;
            border-color: #ff2a5e;
        }}
        .text-placeholder {{
            background: #1a1a1a;
            padding: 20px;
            border-radius: 16px;
            max-width: 80%;
            text-align: center;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="tiktok-container" id="tiktokContainer"></div>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
        <div id="loadingMessage">در حال بارگذاری هوشمند...</div>
    </div>
    <div class="status-bar" id="statusMsg">📱 0 پست</div>
    <div class="sound-prompt" id="soundPrompt">🔊 فعال‌سازی صدا</div>

    <script>
        // داده‌های اصلی پست‌ها (از فایل JSON)
        const rawPosts = {posts_json};
        
        // ------------------- الگوریتم هوشمند مرتب‌سازی -------------------
        // تابع برای بارگذاری اطلاعات کاربر از localStorage
        function loadUserData() {{
            const defaultData = {{
                visited: [],
                liked: [],
                disliked: [],
                channelScores: {{}}   // ذخیره امتیاز کانال‌ها بر اساس لایک/دیسلایک کاربر
            }};
            const saved = localStorage.getItem('tiktok_offline_user');
            if (saved) {{
                try {{
                    return JSON.parse(saved);
                }} catch(e) {{ return defaultData; }}
            }}
            return defaultData;
        }}
        
        function saveUserData(data) {{
            localStorage.setItem('tiktok_offline_user', JSON.stringify(data));
        }}
        
        let userData = loadUserData();
        
        // ترکیب امتیاز کانال: اگر کاربر قبلاً به کانالی امتیاز داده، آن را ملاک قرار بده
        // ابتدا امتیاز اولیه از channels.json (که در rawPosts ذخیره شده)
        function getChannelScore(channel) {{
            if (userData.channelScores[channel] !== undefined) {{
                return userData.channelScores[channel];
            }}
            // fallback به امتیاز اولیه از فایل (اگر موجود بود)
            const post = allPosts.find(p => p.channel === channel);
            return post ? post.channel_score : 1;
        }}
        
        // به‌روزرسانی امتیاز کانال در userData
        function updateChannelScore(channel, delta) {{
            const current = getChannelScore(channel);
            const newScore = Math.max(0, current + delta);
            userData.channelScores[channel] = newScore;
            saveUserData(userData);
        }}
        
        // الگوریتم اصلی: اولویت با ندیده‌ها، سپس بر اساس امتیاز کانال، سپس رندوم
        function reorderPosts() {{
            // جدا کردن ندیده‌ها و دیده‌ها
            const unseen = [];
            const seen = [];
            for (let p of allPosts) {{
                if (userData.visited.includes(p.id)) {{
                    seen.push(p);
                }} else {{
                    unseen.push(p);
                }}
            }}
            // تابع امتیاز برای هر پست = امتیاز کانال آن
            const scoreFunc = (p) => getChannelScore(p.channel);
            
            // مرتب‌سازی ندیده‌ها بر اساس امتیاز نزولی (با رندوم در صورت تساوی)
            unseen.sort((a,b) => {{
                const diff = scoreFunc(b) - scoreFunc(a);
                if (diff !== 0) return diff;
                return Math.random() - 0.5;
            }});
            // مرتب‌سازی دیده‌ها نیز به همین ترتیب
            seen.sort((a,b) => {{
                const diff = scoreFunc(b) - scoreFunc(a);
                if (diff !== 0) return diff;
                return Math.random() - 0.5;
            }});
            // ترکیب: اول همه ندیده‌ها، سپس دیده‌ها
            return unseen.concat(seen);
        }}
        
        // آرایه پست‌ها که به ترتیب نمایش خواهند بود
        let allPosts = [];
        let renderedCount = 0;
        let userInteracted = false;
        let currentActiveVideo = null;
        const container = document.getElementById('tiktokContainer');
        const loadingOverlay = document.getElementById('loadingOverlay');
        const statusDiv = document.getElementById('statusMsg');
        const soundPrompt = document.getElementById('soundPrompt');
        
        // مقداردهی اولیه: کپی از rawPosts و بازآرایی
        function initPosts() {{
            allPosts = JSON.parse(JSON.stringify(rawPosts));
            // همگام‌سازی وضعیت لایک/دیسلایک از userData
            for (let p of allPosts) {{
                p.liked = userData.liked.includes(p.id);
                p.disliked = userData.disliked.includes(p.id);
                p.visited = userData.visited.includes(p.id);
            }}
            // مرتب‌سازی مجدد
            const reordered = reorderPosts();
            allPosts.length = 0;
            allPosts.push(...reordered);
            // به‌روزرسانی status bar
            const unseenCount = allPosts.filter(p => !p.visited).length;
            statusDiv.innerText = `📱 ${{allPosts.length}} پست | ${{unseenCount}} دیده نشده`;
        }}
        
        // فعال‌سازی صدا
        function enableGlobalSound() {{
            if (userInteracted) return;
            userInteracted = true;
            soundPrompt.style.display = 'none';
            if (currentActiveVideo) currentActiveVideo.muted = false;
        }}
        soundPrompt.addEventListener('click', enableGlobalSound);
        document.body.addEventListener('click', enableGlobalSound, {{ once: true }});
        
        // رندر کردن پست‌های بعدی (تا 3 تا جلوتر از پست فعال)
        function renderNextPosts() {{
            const items = document.querySelectorAll('.video-item');
            let activeIndex = -1;
            for (let i = 0; i < items.length; i++) {{
                const rect = items[i].getBoundingClientRect();
                if (rect.top >= -100 && rect.top <= window.innerHeight/2) {{
                    activeIndex = i;
                    break;
                }}
            }}
            if (activeIndex === -1 && items.length > 0) activeIndex = 0;
            
            // رندر کردن تا 3 تا جلوتر از ویدیوی فعال (حداکثر)
            const targetRenderCount = (activeIndex === -1) ? 4 : activeIndex + 4;
            while (renderedCount < allPosts.length && renderedCount <= targetRenderCount) {{
                renderPost(allPosts[renderedCount]);
                renderedCount++;
            }}
        }}
        
        // علامت زدن به عنوان دیده شده
        function markVisited(postId) {{
            if (!userData.visited.includes(postId)) {{
                userData.visited.push(postId);
                saveUserData(userData);
                // به‌روزرسانی وضعیت در allPosts
                const post = allPosts.find(p => p.id === postId);
                if (post) post.visited = true;
                const unseenCount = allPosts.filter(p => !p.visited).length;
                statusDiv.innerText = `📱 ${{allPosts.length}} پست | ${{unseenCount}} دیده نشده`;
            }}
        }}
        
        // لایک و دیسلایک
        function toggleLike(postId, isLike) {{
            const post = allPosts.find(p => p.id === postId);
            if (!post) return;
            const wasLiked = post.liked;
            const wasDisliked = post.disliked;
            let newLiked = false, newDisliked = false;
            if (isLike) {{
                newLiked = !wasLiked;
                newDisliked = false;
            }} else {{
                newDisliked = !wasDisliked;
                newLiked = false;
            }}
            // به‌روزرسانی آرایه‌های userData
            if (newLiked && !userData.liked.includes(postId)) {{
                userData.liked.push(postId);
                // حذف از دیسلایک اگر بود
                const idx = userData.disliked.indexOf(postId);
                if (idx !== -1) userData.disliked.splice(idx,1);
                // تغییر امتیاز کانال: +1
                updateChannelScore(post.channel, +1);
            }} else if (!newLiked && wasLiked) {{
                const idx = userData.liked.indexOf(postId);
                if (idx !== -1) userData.liked.splice(idx,1);
                updateChannelScore(post.channel, -1);
            }}
            if (newDisliked && !userData.disliked.includes(postId)) {{
                userData.disliked.push(postId);
                const idx = userData.liked.indexOf(postId);
                if (idx !== -1) userData.liked.splice(idx,1);
                updateChannelScore(post.channel, -1);
            }} else if (!newDisliked && wasDisliked) {{
                const idx = userData.disliked.indexOf(postId);
                if (idx !== -1) userData.disliked.splice(idx,1);
                updateChannelScore(post.channel, +1);
            }}
            saveUserData(userData);
            // به‌روزرسانی وضعیت در allPosts
            post.liked = newLiked;
            post.disliked = newDisliked;
            // به‌روزرسانی ظاهر دکمه‌ها در DOM
            const item = document.querySelector(`.video-item[data-id="${{postId}}"]`);
            if (item) {{
                const likeBtn = item.querySelector('.like-btn');
                const dislikeBtn = item.querySelector('.dislike-btn');
                if (newLiked) {{
                    likeBtn.classList.add('active');
                    dislikeBtn.classList.remove('active');
                }} else if (newDisliked) {{
                    dislikeBtn.classList.add('active');
                    likeBtn.classList.remove('active');
                }} else {{
                    likeBtn.classList.remove('active');
                    dislikeBtn.classList.remove('active');
                }}
            }}
            // پس از تغییر امتیاز، لیست پست‌ها را دوباره مرتب کن (اختیاری، برای تجربه بهتر)
            // اما برای حفظ سادگی، فقط وضعیت ذخیره می‌شود و در دفعات بعدی که صفحه بارگذاری مجدد شود، مرتب‌سازی می‌شود.
            // در اینجا برای بهبود تجربه، می‌توانیم دوباره مرتب کنیم و صفحه را به‌روز کنیم؟ اما بهتر است کاربر بعد از رفرش ببیند.
            // برای آفلاین، رفرش صفحه باعث اعمال مرتب‌سازی جدید می‌شود.
        }}
        
        // رندر یک پست
        function renderPost(post) {{
            const item = document.createElement('div');
            item.className = 'video-item';
            item.dataset.id = post.id;
            const isVideo = /\\.(mp4|webm|mov)/i.test(post.file_url) || post.file_url.includes('video') || post.file_url.includes('/download/');
            const mediaHtml = isVideo ? 
                `<video class="video-player" src="${{post.file_url}}" muted playsinline loop preload="none" referrerpolicy="no-referrer"></video>` :
                `<img class="video-player" src="${{post.file_url}}" alt="content" loading="lazy">`;
            const likeActive = post.liked ? 'active' : '';
            const dislikeActive = post.disliked ? 'active' : '';
            const viewsText = post.views ? formatNumber(post.views) : '';
            item.innerHTML = `
                ${{mediaHtml}}
                <div class="video-info">
                    <div class="channel-name">@${{post.channel}}</div>
                    <div class="caption">${{escapeHtml(post.text) || ''}}</div>
                </div>
                <div class="actions">
                    <div><button class="action-btn like-btn ${{likeActive}}" data-id="${{post.id}}">❤️</button><div class="views">${{viewsText}}</div></div>
                    <div><button class="action-btn dislike-btn ${{dislikeActive}}" data-id="${{post.id}}">👎</button></div>
                </div>
            `;
            container.appendChild(item);
            const likeBtn = item.querySelector('.like-btn');
            const dislikeBtn = item.querySelector('.dislike-btn');
            likeBtn.addEventListener('click', (e) => {{
                e.stopPropagation();
                toggleLike(post.id, true);
            }});
            dislikeBtn.addEventListener('click', (e) => {{
                e.stopPropagation();
                toggleLike(post.id, false);
            }});
            const video = item.querySelector('video');
            if (video) setupVideoPlayer(video, item);
            // علامت دیده شدن وقتی ویدیو وارد viewport شد (با observer در updateActiveAndRender انجام می‌شود)
        }}
        
        function setupVideoPlayer(video, containerDiv) {{
            video.playsInline = true;
            video.loop = true;
            video.preload = "none";
            video.setAttribute('referrerpolicy', 'no-referrer');
            video.muted = true;
            
            // پیش‌بارگذاری با اینترسکشن
            const preloadObserver = new IntersectionObserver((entries) => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        video.preload = "metadata";
                        video.load();
                        preloadObserver.disconnect();
                    }}
                }});
            }}, {{ threshold: 0.1 }});
            preloadObserver.observe(containerDiv);
            
            const attemptPlay = () => {{
                video.play().catch(e => console.log("autoplay blocked", e));
            }};
            video.addEventListener('loadeddata', attemptPlay);
            if (video.readyState >= 2) attemptPlay();
            
            let retry = 0;
            video.addEventListener('error', () => {{
                if (retry < 2) {{ retry++; setTimeout(() => {{ video.load(); attemptPlay(); }}, 1000); }}
            }});
            
            addCustomControls(video, containerDiv);
        }}
        
        function addCustomControls(video, containerDiv) {{
            if (containerDiv.querySelector('.video-controls')) return;
            const controlsDiv = document.createElement('div');
            controlsDiv.className = 'video-controls';
            const playPauseBtn = document.createElement('button');
            playPauseBtn.innerHTML = '⏸️';
            playPauseBtn.className = 'ctrl-btn';
            playPauseBtn.onclick = (e) => {{
                e.stopPropagation();
                if (video.paused) {{ video.play(); playPauseBtn.innerHTML = '⏸️'; }} 
                else {{ video.pause(); playPauseBtn.innerHTML = '▶️'; }}
            }};
            const volumeBtn = document.createElement('button');
            volumeBtn.innerHTML = '🔇';
            volumeBtn.className = 'ctrl-btn';
            volumeBtn.onclick = (e) => {{
                e.stopPropagation();
                video.muted = !video.muted;
                volumeBtn.innerHTML = video.muted ? '🔇' : '🔊';
                if (!video.muted && !userInteracted) {{
                    userInteracted = true;
                    soundPrompt.style.display = 'none';
                }}
            }};
            video.addEventListener('play', () => {{ playPauseBtn.innerHTML = '⏸️'; }});
            video.addEventListener('pause', () => {{ playPauseBtn.innerHTML = '▶️'; }});
            video.addEventListener('volumechange', () => {{ volumeBtn.innerHTML = video.muted ? '🔇' : '🔊'; }});
            controlsDiv.appendChild(playPauseBtn);
            controlsDiv.appendChild(volumeBtn);
            containerDiv.appendChild(controlsDiv);
        }}
        
        function formatNumber(num) {{
            if (num >= 1_000_000) return (num/1_000_000).toFixed(1)+'M';
            if (num >= 1000) return (num/1000).toFixed(1)+'K';
            return num.toString();
        }}
        
        function escapeHtml(str) {{
            if (!str) return '';
            return str.replace(/[&<>]/g, m => ({{ '&':'&amp;', '<':'&lt;', '>':'&gt;' }})[m]);
        }}
        
        // تشخیص ویدیوی فعال و علامت دیده شدن و رندر بعدی
        function updateActiveAndRender() {{
            const items = document.querySelectorAll('.video-item');
            let bestItem = null, bestRatio = 0, bestIndex = -1;
            for (let i = 0; i < items.length; i++) {{
                const rect = items[i].getBoundingClientRect();
                const visibleHeight = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
                const ratio = visibleHeight / rect.height;
                if (ratio > bestRatio) {{
                    bestRatio = ratio;
                    bestItem = items[i];
                    bestIndex = i;
                }}
            }}
            if (bestItem && bestRatio > 0.5) {{
                const newVideo = bestItem.querySelector('video');
                const postId = bestItem.dataset.id;
                // علامت دیده شدن (اگر هنوز نخورده)
                const post = allPosts.find(p => p.id === postId);
                if (post && !post.visited) {{
                    markVisited(postId);
                }}
                if (newVideo && newVideo !== currentActiveVideo) {{
                    if (currentActiveVideo) currentActiveVideo.muted = true;
                    currentActiveVideo = newVideo;
                    if (userInteracted) currentActiveVideo.muted = false;
                    else currentActiveVideo.muted = true;
                    currentActiveVideo.play().catch(e => console.log(e));
                }}
                // رندر کردن 3 ویدیوی بعدی
                const needRenderUpTo = bestIndex + 4;
                while (renderedCount < allPosts.length && renderedCount <= needRenderUpTo) {{
                    renderPost(allPosts[renderedCount]);
                    renderedCount++;
                }}
            }}
        }}
        
        let scrollTimeout;
        function onScrollHandler() {{
            if (scrollTimeout) clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {{
                updateActiveAndRender();
            }}, 100);
        }}
        
        container.addEventListener('scroll', onScrollHandler);
        window.addEventListener('resize', updateActiveAndRender);
        
        // مقداردهی اولیه
        initPosts();
        // رندر اولیه ۴ پست ابتدایی
        setTimeout(() => {{
            while (renderedCount < allPosts.length && renderedCount < 4) {{
                renderPost(allPosts[renderedCount]);
                renderedCount++;
            }}
            updateActiveAndRender();
            loadingOverlay.style.display = 'none';
        }}, 100);
    </script>
</body>
</html>"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

    messagebox.showinfo("موفق", f"خروجی آفلاین هوشمند با {len(all_posts)} پست در\n{file_path}\nذخیره شد.")
    webbrowser.open(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    generate_offline()