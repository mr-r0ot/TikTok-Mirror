let posts = [];
let isLoading = false;
let hasInitialLoad = false;
let observer = null;
const container = document.getElementById('tiktokContainer');
const loadingOverlay = document.getElementById('loadingOverlay');
const statusDiv = document.getElementById('statusMsg');

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        statusDiv.innerText = `${data.message} | Posts: ${data.total_posts} (پست)`;
        if (data.total_posts > 0 && !hasInitialLoad) fetchPosts();
    } catch(e) { console.error(e); }
}

async function fetchPosts() {
    if (isLoading) return;
    isLoading = true;
    try {
        const res = await fetch('/api/posts');
        const newPosts = await res.json();
        if (newPosts.length === 0) {
            if (posts.length === 0) document.getElementById('loadingMessage').innerText = 'No posts yet, waiting... (هیچ پستی نیست)';
            isLoading = false;
            return;
        }
        if (!hasInitialLoad) {
            loadingOverlay.style.display = 'none';
            hasInitialLoad = true;
        }
        let added = 0;
        for (let p of newPosts) {
            if (!posts.find(ex => ex.id === p.id)) {
                posts.push(p);
                renderPost(p);
                added++;
            }
        }
        if (added > 0) setupObservers();
    } catch(err) { console.error(err); }
    isLoading = false;
}

function renderPost(post) {
    const item = document.createElement('div');
    item.className = 'video-item';
    item.dataset.id = post.id;
    let mediaHtml = '';
    if (post.file_url) {
        const isVideo = post.file_url.match(/\.(mp4|webm|mov)/i) || post.file_url.includes('video');
        if (isVideo) {
            mediaHtml = `<video class="video-player" src="${post.file_url}" muted autoplay loop playsinline preload="auto"></video>`;
        } else {
            mediaHtml = `<img class="video-player" src="${post.file_url}" alt="content">`;
        }
    } else {
        mediaHtml = `<div class="text-placeholder">${escapeHtml(post.text) || '📝 Text post (پست متنی)'}</div>`;
    }
    const likeActive = post.liked ? 'active' : '';
    const dislikeActive = post.disliked ? 'active' : '';
    const viewsText = post.views ? `${formatNumber(post.views)} views (بازدید)` : '';
    item.innerHTML = `
        ${mediaHtml}
        <div class="video-info">
            <div class="channel-name">@${post.channel}</div>
            <div class="caption">${escapeHtml(post.text) || ''}</div>
        </div>
        <div class="actions">
            <div>
                <button class="action-btn like-btn ${likeActive}" data-id="${post.id}">❤️</button>
                <div class="views">${viewsText}</div>
            </div>
            <div>
                <button class="action-btn dislike-btn ${dislikeActive}" data-id="${post.id}">👎</button>
            </div>
        </div>
    `;
    container.appendChild(item);
    const likeBtn = item.querySelector('.like-btn');
    const dislikeBtn = item.querySelector('.dislike-btn');
    likeBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleLike(post.id, true); });
    dislikeBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleLike(post.id, false); });
    const video = item.querySelector('video');
    if (video) setupVideoPlayer(video);
}

function setupVideoPlayer(video) {
    video.muted = true;
    video.playsInline = true;
    video.loop = true;
    video.preload = "auto";
    const play = () => video.play().catch(e => console.log("autoplay error", e));
    video.addEventListener('loadeddata', play);
    video.addEventListener('error', () => setTimeout(() => video.load(), 1500));
    if (video.readyState >= 2) play();
}

function formatNumber(num) {
    if (num >= 1000) return (num/1000).toFixed(1) + 'k';
    return num.toString();
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

async function toggleLike(postId, isLike) {
    const post = posts.find(p => p.id === postId);
    if (!post) return;
    const newLike = isLike ? !post.liked : false;
    const newDislike = !isLike ? !post.disliked : false;
    const item = document.querySelector(`.video-item[data-id="${postId}"]`);
    if (item) {
        const likeBtn = item.querySelector('.like-btn');
        const dislikeBtn = item.querySelector('.dislike-btn');
        if (newLike) {
            likeBtn.classList.add('active');
            dislikeBtn.classList.remove('active');
        } else if (newDislike) {
            dislikeBtn.classList.add('active');
            likeBtn.classList.remove('active');
        } else {
            likeBtn.classList.remove('active');
            dislikeBtn.classList.remove('active');
        }
    }
    try {
        const url = isLike ? `/api/like/${postId}` : `/api/dislike/${postId}`;
        await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ liked: newLike, disliked: newDislike })
        });
        post.liked = newLike;
        post.disliked = newDislike;
    } catch(e) { console.error(e); }
}

function setupObservers() {
    if (observer) observer.disconnect();
    observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const video = entry.target.querySelector('video');
            const postId = entry.target.dataset.id;
            if (entry.isIntersecting) {
                if (video) video.play().catch(e => console.log(e));
                fetch(`/api/view/${postId}`, { method: 'POST' });
            } else {
                if (video) video.pause();
            }
        });
    }, { threshold: 0.5 });
    document.querySelectorAll('.video-item').forEach(item => observer.observe(item));
}

container.addEventListener('scroll', () => {
    if (container.scrollTop + container.clientHeight >= container.scrollHeight - 500) fetchPosts();
});

fetchStatus();
setInterval(fetchStatus, 5000);