# YouTube Compatibility

MediaCatch includes an additional compatibility layer for recent YouTube extraction changes.

## Why this exists

A YouTube video can play normally in a web browser while yt-dlp reports errors such as:

```text
This video is not available
```

In some cases the video is not actually unavailable. The failure can be caused by YouTube JavaScript challenges that require both:

- a supported JavaScript runtime
- yt-dlp's EJS challenge-solver scripts

## What MediaCatch does automatically

For YouTube URLs MediaCatch:

1. Detects a supported JavaScript runtime.
2. Prefers **Deno** when available.
3. Falls back to **Node.js** when appropriate.
4. Passes the runtime explicitly to yt-dlp.
5. Enables the official EJS remote component:

```text
--remote-components ejs:github
```

6. Uses `yt-dlp[default]` as the Python dependency so the companion EJS package is installed together with yt-dlp.
7. Shows more useful diagnostics when a failure appears related to challenge solving.

## Recommended Windows setup

Run:

```text
INSTALL_DENO.bat
```

Then close and restart MediaCatch.

Deno is currently the recommended JavaScript runtime for yt-dlp's YouTube EJS workflow.

## Manual test

A direct yt-dlp test can be performed with:

```powershell
py -m yt_dlp --js-runtimes deno --remote-components ejs:github "https://www.youtube.com/watch?v=VIDEO_ID"
```

If Node.js is being used instead:

```powershell
py -m yt_dlp --js-runtimes node --remote-components ejs:github "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Keeping compatibility current

YouTube changes frequently. Keep yt-dlp and its default dependencies updated:

```powershell
.\.venv\Scripts\python.exe -m pip install -U "yt-dlp[default]"
```

or run:

```text
UPDATE_YT_DLP.bat
```

## Limitations

This feature improves compatibility with current yt-dlp-supported YouTube challenges. It does not guarantee that every YouTube video can be downloaded. Availability can still depend on region, authentication, age restrictions, account state, live-stream status, upstream yt-dlp support, and future YouTube changes.

MediaCatch does not remove or bypass DRM.
