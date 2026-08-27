# MediaCatch

MediaCatch is a local Streamlit-based media downloader powered by **yt-dlp**. It combines a normal downloader for supported platforms with an optional **authenticated browser capture** mode for dynamic websites where media is available only after signing in.

> Use MediaCatch only for media you own or are authorized to download. The application does not remove or bypass DRM.

## Features

- YouTube, TikTok, Vimeo and other sites supported by yt-dlp
- Direct MP4, M3U8/HLS and MPD/DASH URLs
- MP4 video, best available format and MP3 audio extraction
- Quality selection
- Optional playlists and IT/EN subtitles
- Optional browser cookies and Referer header
- Authenticated browser mode using a separate Chrome/Edge profile
- Automatic capture of authorized direct media requests from dynamic sites
- Persistent local login session as an opt-in feature
- FFmpeg detection
- YouTube JavaScript runtime detection
- yt-dlp EJS challenge solver support via `ejs:github`

## Two operating modes

### 1. Standard mode

Use this for normal yt-dlp-compatible URLs such as YouTube, TikTok, Vimeo, supported websites, and direct media URLs.

Paste a video URL, click **Analyze**, choose the format/quality, then click **Download**.

### 2. Authenticated browser mode

Use this when a website requires a login, uses a dynamic single-page application, or returns errors such as `Unsupported URL` or `401 Unauthorized` when the media URL is accessed outside the browser session.

MediaCatch opens a separate Chrome or Edge window. You sign in **directly on the website**. The app never asks for your username or password. Once you start the video, MediaCatch detects authorized MP4/HLS/DASH media requests and can pass the required session context to yt-dlp.

The browser profile can optionally be stored locally in `.auth_browser_profile/` so you do not need to sign in every time. This folder is excluded from Git.

## Requirements

- Windows 10/11 is the primary supported setup
- Python 3.11+
- Google Chrome or Microsoft Edge for authenticated browser mode
- FFmpeg for MP3 conversion and many high-quality audio/video merges
- Deno (recommended) or a supported Node.js runtime for current YouTube JavaScript challenges

## Quick start on Windows

1. Download or clone this repository.
2. Double-click `START_APP.bat`.
3. The script creates `.venv`, installs Python dependencies and launches Streamlit.
4. If you need MP3 or merged high-quality formats, run `INSTALL_FFMPEG.bat` once.
5. For best current YouTube compatibility, run `INSTALL_DENO.bat` once and restart MediaCatch.

Manual startup:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## YouTube and EJS challenges

Recent YouTube extraction can require both a JavaScript runtime and yt-dlp's EJS challenge-solver scripts. MediaCatch detects Deno/Node and enables:

```text
--remote-components ejs:github
```

for YouTube URLs. Deno is the recommended runtime in yt-dlp's current documentation.

## FFmpeg

MediaCatch can download some formats without FFmpeg, but FFmpeg is recommended for:

- merging separate high-quality video/audio streams
- MP3 extraction
- subtitle conversion
- many HLS/DASH workflows

On Windows, `INSTALL_FFMPEG.bat` installs FFmpeg through WinGet when available.

## Privacy and local session handling

Authenticated browser mode is designed so credentials stay between you and the website:

- MediaCatch does not provide username/password fields.
- Login happens inside the real browser window.
- Captured cookies/header context is used locally for the requested media download.
- Persistent browser data is stored only when the user opts in.
- `.auth_browser_profile/`, `downloads/`, `.venv/`, cookies and local tools are ignored by Git.

See [SECURITY.md](SECURITY.md) for additional notes.

## Limitations

- MediaCatch does **not** remove or bypass DRM.
- Some sites actively block automated clients or change frequently.
- Signed URLs can expire and may need to be captured again.
- Browser-cookie extraction from Chrome on Windows can fail because of DPAPI/Application-Bound Encryption; authenticated browser mode avoids relying on the normal Chrome profile for those cases.
- Site availability depends on yt-dlp extractors and upstream website changes.

## Updating yt-dlp

Run:

```text
UPDATE_YT_DLP.bat
```

or update manually inside the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -U "yt-dlp[default]"
```

## Legal notice

MediaCatch is a general-purpose local tool. Users are responsible for complying with copyright law, website terms, access permissions and applicable regulations. Do not use it to obtain content you are not authorized to download or to circumvent DRM/access-control technologies.

## License

MediaCatch source code is released under the [MIT License](LICENSE). Third-party projects retain their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
