import { ensureAlbumAccess, albumFromSrc } from './auth.js';
function q(sel){ return document.querySelector(sel); }
function fmt(t){ if(!isFinite(t)) return '--:--'; const m = Math.floor(t/60); const s = Math.floor(t%60); return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`; }
function getParam(k){ const u=new URL(location.href); return u.searchParams.get(k); }
function safeDecode(v){
  if(v == null) return v;
  try {
    // 如果包含百分号编码，则尝试解码；否则直接返回
    return /%[0-9A-Fa-f]{2}/.test(v) ? decodeURIComponent(v) : v;
  } catch { return v; }
}

const audio = q('#audio');
const seek = q('#seek');
const btnPlay = q('#play');
const btnRew = q('#rewind');
const btnFwd = q('#forward');
const tCur = q('#currentTime');
const tDur = q('#duration');
const titleEl = q('#trackTitle');
const backBtn = q('#backBtn');
const prevBtn = q('#prevBtn');
const nextBtn = q('#nextBtn');

// init
const src = safeDecode(getParam('src'));
const title = safeDecode(getParam('title')) || '音频';
const back = safeDecode(getParam('back')) || 'waking-up.html';
let manifest = safeDecode(getParam('manifest'));
const idParam = getParam('id');
const curId = idParam != null ? Number(idParam) : NaN;

let items = [];
let curIndex = -1;

// 进度存储（per-album per-item）
let albumSlug = null;
function progressKey(slug){ return `progress_${slug}`; }
function loadProgress(slug){
  try { return JSON.parse(localStorage.getItem(progressKey(slug)) || '{}'); } catch { return {}; }
}
function saveProgress(slug, obj){
  try { localStorage.setItem(progressKey(slug), JSON.stringify(obj)); } catch {}
}
function markDone(slug, itemId){
  if(!slug || !Number.isFinite(itemId)) return;
  const p = loadProgress(slug);
  if(p[String(itemId)] === 'done') return; // 已完成则跳过
  p[String(itemId)] = 'done';
  saveProgress(slug, p);
}
let doneMarked = false;

async function gateAndInit(){
  const decSrc = src || '';
  const slug = albumFromSrc(decSrc);
  if(slug){
    const ok = await ensureAlbumAccess(slug);
    if(!ok){
      location.href = 'index.html';
      return;
    }
    // 若未提供 manifest 参数，尝试根据 slug 推断
    if(!manifest){
      manifest = `manifest/${slug}.json`;
    }
  }
  albumSlug = slug || albumSlug;
  if(decSrc){
    audio.src = decSrc;
  }
}
gateAndInit();

titleEl.textContent = title;
backBtn.onclick = ()=>{ location.href = 'waking-up.html'; };

function updateNavButtons(){
  if(!prevBtn || !nextBtn) return;
  const atStart = curIndex <= 0;
  const atEnd = curIndex >= items.length - 1;
  prevBtn.disabled = atStart;
  nextBtn.disabled = atEnd;
  prevBtn.setAttribute('aria-disabled', String(atStart));
  nextBtn.setAttribute('aria-disabled', String(atEnd));
}

function buildPlayerUrl(item){
  const t = item.title || `第${item.id}天`;
  const u = new URL(location.origin + location.pathname);
  u.searchParams.set('title', t);
  u.searchParams.set('src', item.file);
  u.searchParams.set('back', back);
  if(!isNaN(item.id)) u.searchParams.set('id', String(item.id));
  if(manifest) u.searchParams.set('manifest', manifest);
  return u.toString();
}

function navTo(index){
  if(index < 0 || index >= items.length) return;
  const target = items[index];
  location.href = buildPlayerUrl(target);
}


async function initNav(){
  try{
    if(!manifest){ updateNavButtons(); return; }
    const res = await fetch(manifest, {cache:'no-cache'});
    const data = await res.json();
    items = (data.items || []).slice().sort((a,b)=>a.id-b.id);
    // 1) 优先用 id 精确匹配
    if(!Number.isNaN(curId)){
      curIndex = items.findIndex(it => Number(it.id) === curId);
    }
    // 2) 再用完整路径匹配
    if(curIndex < 0){
      const decSrc = src || '';
      curIndex = items.findIndex(it => (it.file || '') === decSrc);
    }
    // 3) 最后用文件名匹配（忽略目录差异）
    if(curIndex < 0){
      const decSrc = src || '';
      const bn = decSrc.split('/').pop();
      curIndex = items.findIndex(it => (it.file || '').split('/').pop() === bn);
    }
    // 4) 兜底：未能识别则回到第一项
    if(curIndex < 0 && items.length){
      console.warn('无法从参数识别当前条目，已回退到第一项');
      curIndex = 0;
    }
    updateNavButtons();
    if(prevBtn) prevBtn.onclick = ()=> navTo(curIndex - 1);
    if(nextBtn) nextBtn.onclick = ()=> navTo(curIndex + 1);
  }catch(e){
    console.error('导航初始化失败', e);
  }
}
initNav();


// events
btnPlay.addEventListener('click', ()=>{
  if(audio.paused){ audio.play(); } else { audio.pause(); }
});
audio.addEventListener('play', ()=>{ btnPlay.innerHTML = '<svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>'; });
audio.addEventListener('pause', ()=>{ btnPlay.innerHTML = '<svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>'; });
audio.addEventListener('loadedmetadata', ()=>{
  tDur.textContent = fmt(audio.duration);
});
audio.addEventListener('timeupdate', ()=>{
  tCur.textContent = fmt(audio.currentTime);
  if(isFinite(audio.duration)){
    seek.value = (audio.currentTime / audio.duration) * 100;
    // 到达 90% 视为完成（仅标记一次）
    if(!doneMarked && albumSlug && !Number.isNaN(curId)){
      const ratio = audio.currentTime / (audio.duration || 1);
      if(ratio >= 0.9){
        markDone(albumSlug, curId);
        doneMarked = true;
      }
    }
  }
});
audio.addEventListener('ended', ()=>{
  if(albumSlug && !Number.isNaN(curId)){
    markDone(albumSlug, curId);
    doneMarked = true;
  }
});
seek.addEventListener('input', ()=>{
  if(isFinite(audio.duration)){
    audio.currentTime = (seek.value/100) * audio.duration;
  }
});
btnRew.addEventListener('click', ()=>{ audio.currentTime = Math.max(0, audio.currentTime - 15); });
btnFwd.addEventListener('click', ()=>{ audio.currentTime = Math.min(audio.duration||Infinity, audio.currentTime + 30); });

// 为了在中国网络下更稳健：不自动播放，保持简单请求
// 用户手动点击即可播放，提高成功率
