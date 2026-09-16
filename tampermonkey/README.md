# CrossVideo Userscript

CrossVideo Userscript 用于识别网页中的主要 HTML5 视频播放器，并将观看进度同步到用户配置的 CrossVideo API 服务。

## Features

- Sync HTML5 video progress across devices and supported websites
- Resume prompt for previously watched videos
- Login and registration from the Tampermonkey menu
- Searchable, paginated playback history
- Delete individual history records
- Filter history to the current website
- Cross-device website blocklist
- Configurable API address with no server address embedded in the published script
- SPA route changes and dynamic video elements supported

## Installation

1. Install Tampermonkey or Violentmonkey.
2. Open `crossvideo.user.js` in this directory.
3. Create a new userscript and paste the file contents into it.
4. Save and enable the userscript.
5. Open the userscript menu and select `登录 / 注册账号`.
6. Enter the API base address, for example:

```text
https://your-domain.example
```

The script appends `/api/v1` automatically. Do not include `/api/v1` in the address field.

## Permissions

The script uses these userscript APIs:

- `GM_setValue` and `GM_getValue` for global token, username, and API address storage
- `GM_xmlhttpRequest` for cross-origin API requests
- `GM_registerMenuCommand` and `GM_unregisterMenuCommand` for menu actions
- `GM_addValueChangeListener` to synchronize menu state across browser tabs

The published script declares `@connect *` because each user configures their own API server. For personal deployments, `@connect` can be narrowed to the actual API host.

## Backend

The backend must provide the CrossVideo FastAPI service. Start it from the repository's `backend` directory, then enter its public base address in the userscript login window.

The script expects the API routes under:

```text
/api/v1
```

## Website blocklist

The blocklist uses the exact hostname from the browser address bar, such as `www.bilibili.com`. It does not collect CDN or embedded resource hosts. Blocking a site removes the user's existing records for that hostname and causes future progress synchronization from that hostname to be ignored.

## License

MIT License
