# Changelog

All notable changes to MediaCatch will be documented in this file.

## [1.0.0] - 2026-08-27

### Added

- Standard yt-dlp download mode for YouTube, TikTok, Vimeo and other supported sites.
- Direct MP4, M3U8/HLS and MPD/DASH download support.
- Authenticated browser capture mode for dynamic and login-protected websites.
- Optional persistent local browser session using a separate Chrome/Edge profile.
- FFmpeg detection and Windows installer helper.
- Deno installer helper for current YouTube compatibility.

### Enhanced YouTube compatibility

- Added automatic JavaScript runtime detection, preferring Deno and falling back to Node.js.
- Added automatic yt-dlp EJS challenge-solver activation for YouTube via:

```text
--remote-components ejs:github
```

- Switched the Python dependency to `yt-dlp[default]` so the companion EJS package is installed with yt-dlp.
- Added targeted diagnostics for JavaScript/EJS challenge failures that can otherwise appear as misleading errors such as `This video is not available`.
- Added documentation explaining why a video may play correctly in a browser while yt-dlp fails without the current JavaScript/EJS compatibility layer.

### Security and privacy

- No username/password fields are used by authenticated browser mode.
- Login credentials remain between the user and the target website.
- Local browser session data, cookies, downloads, tools and virtual environments are excluded from Git.
- MediaCatch does not remove or bypass DRM.
