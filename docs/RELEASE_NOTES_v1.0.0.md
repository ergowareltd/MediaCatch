# MediaCatch v1.0.0

MediaCatch v1.0.0 introduces a local Streamlit interface for yt-dlp with two complementary workflows: standard downloads for supported platforms and authenticated browser capture for dynamic/login-protected websites.

## Highlight: enhanced YouTube compatibility

Recent YouTube changes can require JavaScript challenge solving before yt-dlp can access valid media. In these cases a video may play normally in the browser while a downloader incorrectly reports that the video is unavailable.

MediaCatch addresses this by automatically:

- detecting a supported JavaScript runtime
- preferring Deno and falling back to Node.js
- passing the runtime to yt-dlp
- enabling the official yt-dlp EJS challenge solver through `--remote-components ejs:github`
- installing yt-dlp with its `default` dependency group so the EJS companion package is available
- surfacing targeted diagnostics for JavaScript/EJS challenge failures

This feature reduces the manual configuration normally required to handle current YouTube extraction changes.

## Other features

- YouTube, TikTok, Vimeo and other yt-dlp-supported sites
- direct MP4, M3U8/HLS and MPD/DASH URLs
- quality selection and MP4/best-format/MP3 workflows
- optional subtitles and playlists
- authenticated browser capture for authorized media behind login
- optional persistent browser session in a separate Chrome/Edge profile
- FFmpeg detection and helper installation
- local-first operation with no credential fields in the Streamlit UI

## Notes

MediaCatch does not remove or bypass DRM. Users are responsible for downloading only media they own or are authorized to download and for complying with applicable laws and website terms.
