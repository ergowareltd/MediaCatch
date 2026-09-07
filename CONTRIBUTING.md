# Contributing to MediaCatch

Thank you for your interest in contributing to MediaCatch.

MediaCatch is a local Streamlit media downloader powered by yt-dlp, with authenticated browser capture for logged-in environments and enhanced YouTube compatibility.

## Before contributing

Please keep the following principles in mind:

- Do not add DRM bypass or circumvention features.
- Do not add functionality intended to bypass access controls without authorization.
- Authenticated browser features must rely on sessions legitimately established by the user.
- Never store or request website passwords inside MediaCatch.
- Keep local user data, browser profiles, cookies and downloaded media out of the repository.
- Preserve compatibility with the supported Python versions whenever possible.

## Development setup

Requirements:

- Python 3.11 or newer
- Git
- FFmpeg recommended
- Chrome or Microsoft Edge for authenticated browser mode
- Deno recommended for current YouTube compatibility

Clone the repository:

```bash
git clone https://github.com/ergowareltd/MediaCatch.git
cd MediaCatch
