# mediday

亲友间分享正念指导音频（静态网页，适合 GitHub Pages）。

## 目录结构

- `index.html` 首页（专辑列表）
- `waking-up.html` "醒来-50天冥想入门" 目录页
- `player.html` 音频播放页（进度、暂停、快进/后退）
- `manifest/waking-up_intro-50_chinese.json` 列表数据
- `waking-up_intro-50_chinese/` 50 个 mp3 文件
- `assets/` 样式与脚本
- `.nojekyll` 关闭 Jekyll 处理

## 本地预览

在项目根目录运行一个本地静态服务器（任选其一）：

```bash
python3 -m http.server 8000
# 或
npx serve -l 8000
```

然后访问：http://127.0.0.1:8000

## 部署到 GitHub Pages

1. 新建 GitHub 仓库（例如 `mediday`）。
2. 推送代码到 `main` 分支根目录（保持本项目结构不变）。
3. 在仓库 Settings → Pages：
   - Source 选择 `Deploy from a branch`
   - Branch 选择 `main`，`/ (root)`，保存
4. 稍等几分钟，访问 `https://<你的用户名>.github.io/mediday/`

说明：本项目使用相对路径，适配 GitHub Pages 的子路径部署；`.nojekyll` 确保静态文件直接可用。

## 专辑口令（家庭用途）

- 配置文件：`config/passwords.json`
- 结构示例：

```json
{
  "waking-up_intro-50_chinese": {
    "title": "醒来 - 50天冥想入门",
    "password": "wjhy53"
  }
}
```

- 机制：
  - 进入专辑页（如 `waking-up.html`）会弹出密码输入框，通过后在 `localStorage` 记住（浏览器内，仅当前设备）。
  - 直达播放页（`player.html`）时会再次校验音频所属专辑是否已通过。
  - 仅前端实现，不具备强安全性，请仅用于亲友小范围访问。

## 面向手机与大陆网络的考虑

- 不自动播放，仅预加载 metadata，提升成功率
- 设计简约、点击目标大、适合触控
- 提供“下载本音频”备用
- 若网络缓慢，可将 mp3 转为稍低比特率以减小体积

## 版权与私密

请确保仅在亲友间交流与学习用途，不要公开传播有版权限制的内容。


git add .
git commit -m "Initial site: album, player, password gate"
git branch -M main
git remote add origin https://github.com/vince-jq-sun/mediday.git
git push -u origin main