// Simple client-side password gate (not secure; for family use only)
// Uses config/passwords.json and localStorage to remember access per album.

const STORAGE_PREFIX = 'album_access_';

export function storageKey(slug){
  return STORAGE_PREFIX + slug;
}

export function hasAlbumAccess(slug){
  try { return localStorage.getItem(storageKey(slug)) === 'ok'; }
  catch { return false; }
}

export function grantAlbumAccess(slug){
  try { localStorage.setItem(storageKey(slug), 'ok'); } catch {}
}

export function clearAlbumAccess(slug){
  try { localStorage.removeItem(storageKey(slug)); } catch {}
}

export function albumFromSrc(src){
  try {
    const p = src || '';
    // Heuristic: first path segment is album folder
    // e.g. waking-up_intro-50_chinese/wu_day1.mp3
    const m = p.match(/^([^\/?#]+)\//);
    return m ? m[1] : null;
  } catch { return null; }
}

export async function fetchPasswords(){
  const res = await fetch('config/passwords.json', { cache: 'no-cache' });
  if(!res.ok) throw new Error('加载密码配置失败');
  return res.json();
}

export async function ensureAlbumAccess(slug){
  if(hasAlbumAccess(slug)) return true;
  const cfg = await fetchPasswords();
  const entry = cfg[slug];
  if(!entry){
    // No password configured → allow
    return true;
  }
  const correct = String(entry.password || '');

  const ok = await openPasswordGate({ title: entry.title || slug, correct });
  if(ok){
    grantAlbumAccess(slug);
    return true;
  }
  return false;
}

// In-page password gate with accessible focus and keyboard handling
function openPasswordGate({ title, correct }){
  return new Promise(resolve => {
    const backdrop = document.createElement('div');
    backdrop.className = 'pw-backdrop';

    const modal = document.createElement('div');
    modal.className = 'pw-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'pw-title');

    modal.innerHTML = `
      <h2 id="pw-title">请输入「${title}」的访问密码</h2>
      <input type="password" class="pw-input" placeholder="输入密码" autocomplete="current-password" />
      <div class="pw-error" aria-live="polite"></div>
      <div class="pw-actions">
        <button type="button" class="pw-btn secondary">取消</button>
        <button type="button" class="pw-btn primary">确认</button>
      </div>
    `;

    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);

    const input = modal.querySelector('.pw-input');
    const error = modal.querySelector('.pw-error');
    const [cancelBtn, okBtn] = modal.querySelectorAll('.pw-actions .pw-btn');

    const cleanup = () => {
      try { document.body.removeChild(backdrop); } catch {}
    };

    const submit = () => {
      const val = String(input.value || '');
      if(val === String(correct)){
        cleanup();
        resolve(true);
      } else {
        error.textContent = '密码不正确';
        input.classList.add('pw-input-error');
        input.focus();
        input.select();
      }
    };

    okBtn.addEventListener('click', submit);
    cancelBtn.addEventListener('click', () => { cleanup(); resolve(false); });
    backdrop.addEventListener('click', (e) => {
      // prevent accidental close when clicking outside modal content
      if(e.target === backdrop){ /* do nothing */ }
    });
    input.addEventListener('keydown', (e) => {
      if(e.key === 'Enter') submit();
      if(e.key === 'Escape') { cleanup(); resolve(false); }
    });
    okBtn.addEventListener('keydown', (e) => {
      if(e.key === 'Enter') submit();
    });

    // Autofocus
    setTimeout(() => { input.focus(); }, 0);
  });
}
