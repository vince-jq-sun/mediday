import { ensureAlbumAccess, albumFromSrc } from './auth.js';
function q(sel){ return document.querySelector(sel); }
function fmt(t){ if(!isFinite(t)) return '--:--'; const m = Math.floor(t/60); const s = Math.floor(t%60); return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`; }
function getParam(k){ const u=new URL(location.href); return u.searchParams.get(k); }

const audio = q('#audio');
const seek = q('#seek');
const btnPlay = q('#play');
const btnRew = q('#rewind');
const btnFwd = q('#forward');
const tCur = q('#currentTime');
const tDur = q('#duration');
const titleEl = q('#trackTitle');
const backBtn = q('#backBtn');
const download = q('#download');

// init
const src = getParam('src');
const title = getParam('title') || '音频';
const back = getParam('back') || 'waking-up.html';

async function gateAndInit(){
  const decSrc = src ? decodeURIComponent(src) : '';
  const slug = albumFromSrc(decSrc);
  if(slug){
    const ok = await ensureAlbumAccess(slug);
    if(!ok){
      location.href = 'index.html';
      return;
    }
  }
  if(decSrc){
    audio.src = decSrc;
    download.href = decSrc;
  }
}
gateAndInit();

titleEl.textContent = decodeURIComponent(title);
backBtn.onclick = ()=>{ try{ history.length>1?history.back():location.href = decodeURIComponent(back); }catch{ location.href = 'index.html'; } };

// events
btnPlay.addEventListener('click', ()=>{
  if(audio.paused){ audio.play(); } else { audio.pause(); }
});
audio.addEventListener('play', ()=>{ btnPlay.textContent='⏸ 暂停'; btnPlay.classList.add('primary'); });
audio.addEventListener('pause', ()=>{ btnPlay.textContent='▶️ 播放'; btnPlay.classList.add('primary'); });
audio.addEventListener('loadedmetadata', ()=>{
  tDur.textContent = fmt(audio.duration);
});
audio.addEventListener('timeupdate', ()=>{
  tCur.textContent = fmt(audio.currentTime);
  if(isFinite(audio.duration)){
    seek.value = (audio.currentTime / audio.duration) * 100;
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
