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
  // Prompt loop with up to 3 attempts
  for(let i=0;i<3;i++){
    const tip = i===0 ? '' : '（再试一次）';
    const input = window.prompt(`请输入「${entry.title || slug}」的访问密码${tip}`);
    if(input == null){
      // cancel
      return false;
    }
    if(String(input) === correct){
      grantAlbumAccess(slug);
      return true;
    } else {
      alert('密码不正确');
    }
  }
  return false;
}
