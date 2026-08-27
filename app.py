from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
from pathlib import Path
from queue import Empty, Queue
from urllib.parse import unquote, urlparse

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = APP_DIR / "downloads"
TOOLS_DIR = APP_DIR / "tools"
AUTH_PROFILE_DIR = APP_DIR / ".auth_browser_profile"
YTDLP_EXE = APP_DIR / "yt-dlp.exe"

# Official release verified when this version of the app was prepared.
YTDLP_VERSION = "2026.08.19"
YTDLP_URL = f"https://github.com/yt-dlp/yt-dlp/releases/download/{YTDLP_VERSION}/yt-dlp.exe"
YTDLP_SHA256 = "66674953fe251b89f4d08c5f0e35e0728679bd67ab3d7d05c0562af101dd3e7a"

DOWNLOADS_DIR.mkdir(exist_ok=True)
TOOLS_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="MediaCatch - yt-dlp", page_icon="⬇️", layout="centered")


def is_windows() -> bool:
    return os.name == "nt"


def valid_http_url(value: str) -> bool:
    try:
        p = urlparse(value.strip())
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def is_spa_fragment_url(value: str) -> bool:
    try:
        p = urlparse(value.strip())
        return bool(p.fragment) and (p.fragment.startswith("/") or "/" in p.fragment)
    except Exception:
        return False


def looks_like_direct_media_url(value: str) -> bool:
    low = value.lower().split("?", 1)[0]
    return any(ext in low for ext in (".m3u8", ".mpd", ".mp4", ".webm", ".m4v", ".mov", ".m4a", ".mp3"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_ytdlp() -> tuple[bool, str]:
    if not is_windows():
        return False, "The bundled binary bootstrap is intended for Windows."
    tmp = YTDLP_EXE.with_suffix(".exe.part")
    try:
        req = urllib.request.Request(YTDLP_URL, headers={"User-Agent": "Mozilla/5.0 yt-dlp-streamlit-app"})
        with urllib.request.urlopen(req, timeout=60) as response, tmp.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        digest = sha256_file(tmp)
        if digest.lower() != YTDLP_SHA256.lower():
            tmp.unlink(missing_ok=True)
            return False, f"Checksum mismatch. Expected {YTDLP_SHA256}, got {digest}."
        tmp.replace(YTDLP_EXE)
        return True, f"yt-dlp {YTDLP_VERSION} installed and verified."
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        return False, f"Could not download yt-dlp: {exc}"


def get_ytdlp_command() -> list[str] | None:
    if is_windows() and YTDLP_EXE.exists():
        return [str(YTDLP_EXE)]
    path = shutil.which("yt-dlp")
    if path:
        return [path]
    try:
        import yt_dlp  # noqa: F401
        return [sys.executable, "-m", "yt_dlp"]
    except Exception:
        return None


def find_ffmpeg() -> str | None:
    candidates = [
        shutil.which("ffmpeg"),
        str(APP_DIR / "ffmpeg.exe"),
        str(TOOLS_DIR / "ffmpeg.exe"),
        str(TOOLS_DIR / "ffmpeg" / "bin" / "ffmpeg.exe"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def ffmpeg_location_arg() -> list[str]:
    ff = find_ffmpeg()
    return ["--ffmpeg-location", str(Path(ff).parent)] if ff else []


def find_js_runtime() -> tuple[str, str] | None:
    """Return (runtime_name, executable_path). Deno is preferred by yt-dlp for YouTube."""
    deno = shutil.which("deno")
    if deno:
        return "deno", deno
    node = shutil.which("node")
    if node:
        return "node", node
    for name, candidate in (
        ("deno", TOOLS_DIR / "deno.exe"),
        ("deno", APP_DIR / "deno.exe"),
        ("node", TOOLS_DIR / "node.exe"),
        ("node", APP_DIR / "node.exe"),
    ):
        if candidate.exists():
            return name, str(candidate)
    return None


def js_runtime_args() -> list[str]:
    runtime = find_js_runtime()
    if not runtime:
        return []
    name, path = runtime
    return ["--js-runtimes", f"{name}:{path}"]


def youtube_ejs_args(value: str) -> list[str]:
    """Enable yt-dlp's official EJS challenge solver distribution for YouTube."""
    if is_youtube_url(value):
        return ["--remote-components", "ejs:github"]
    return []


def is_youtube_url(value: str) -> bool:
    try:
        host = urlparse(value.strip()).netloc.lower()
        return host.endswith("youtube.com") or host.endswith("youtu.be") or host.endswith("youtube-nocookie.com")
    except Exception:
        return False


def cookie_args(browser: str) -> list[str]:
    if browser == "None":
        return []
    return ["--cookies-from-browser", browser.lower()]


def request_context_args(referer: str) -> list[str]:
    args = [
        "--user-agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/151.0 Safari/537.36",
    ]
    if referer.strip():
        args += ["--referer", referer.strip()]
    return args


def run_capture(args: list[str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
        creationflags=subprocess.CREATE_NO_WINDOW if is_windows() else 0,
    )


def format_duration(seconds) -> str:
    try:
        s = int(seconds)
    except Exception:
        return "—"
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{sec:02d}" if h else f"{m:d}:{sec:02d}"


def format_count(value) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return "—"


def analyze_url(url: str, browser: str, playlist: bool, referer: str = "") -> tuple[dict | None, str | None]:
    cmd = get_ytdlp_command()
    if not cmd:
        return None, "yt-dlp is not available."
    args = cmd + ["--dump-single-json"]
    args += js_runtime_args()
    args += youtube_ejs_args(url)
    args += [] if playlist else ["--no-playlist"]
    args += cookie_args(browser)
    args += request_context_args(referer)
    args += [url]
    try:
        cp = run_capture(args, timeout=120)
    except subprocess.TimeoutExpired:
        return None, "Analysis timed out: the site took too long to respond."
    except Exception as exc:
        return None, f"Error during analysis: {exc}"
    if cp.returncode != 0:
        err = (cp.stderr or cp.stdout or "Unknown error").strip()
        return None, err[-5000:]
    try:
        return json.loads(cp.stdout), None
    except json.JSONDecodeError:
        return None, "yt-dlp did not return valid JSON metadata."


def available_heights(info: dict) -> list[int]:
    heights: set[int] = set()
    for f in info.get("formats") or []:
        h = f.get("height")
        if isinstance(h, (int, float)) and h > 0:
            heights.add(int(h))
    preferred = [4320, 2160, 1440, 1080, 720, 480, 360, 240, 144]
    ordered = [h for h in preferred if h in heights]
    return ordered + sorted(heights - set(preferred), reverse=True)


def safe_download_dir(raw: str) -> Path:
    raw = raw.strip()
    if not raw:
        return DOWNLOADS_DIR
    p = Path(os.path.expandvars(os.path.expanduser(raw)))
    p.mkdir(parents=True, exist_ok=True)
    return p.resolve()


def build_download_command(
    url: str,
    media_type: str,
    quality: str,
    output_dir: Path,
    browser: str,
    playlist: bool,
    subtitles: bool,
    referer: str = "",
) -> list[str]:
    cmd = get_ytdlp_command()
    if not cmd:
        raise RuntimeError("yt-dlp is not available")

    out_template = str(output_dir / "%(title).180B [%(id)s].%(ext)s")
    args = cmd + ["--newline", "--windows-filenames", "--no-overwrites", "--continue", "--output", out_template]
    args += js_runtime_args()
    args += youtube_ejs_args(url)
    args += [] if playlist else ["--no-playlist"]
    args += cookie_args(browser)
    args += request_context_args(referer)
    args += ffmpeg_location_arg()

    if subtitles:
        args += ["--write-subs", "--write-auto-subs", "--sub-langs", "it.*,en.*"]
        if find_ffmpeg():
            args += ["--convert-subs", "srt"]

    h = None if quality == "Best" else int(quality.replace("p", ""))

    if media_type == "MP4 Video":
        if find_ffmpeg():
            selector = "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"
            if h:
                selector = (
                    f"bv*[ext=mp4][height<={h}]+ba[ext=m4a]/"
                    f"b[ext=mp4][height<={h}]/"
                    f"bv*[height<={h}]+ba/b[height<={h}]"
                )
            args += ["-f", selector, "--merge-output-format", "mp4"]
        else:
            selector = "b[ext=mp4]/b"
            if h:
                selector = f"b[ext=mp4][height<={h}]/b[height<={h}]"
            args += ["-f", selector]
    elif media_type == "MP3 Audio":
        if not find_ffmpeg():
            raise RuntimeError("FFmpeg is required for MP3 conversion. Run INSTALL_FFMPEG.bat and restart the app.")
        args += ["-f", "ba/b", "-x", "--audio-format", "mp3", "--audio-quality", "0"]
    elif media_type == "Best available format":
        selector = "bv*+ba/b" if find_ffmpeg() else "b"
        if h:
            selector = f"bv*[height<={h}]+ba/b[height<={h}]" if find_ffmpeg() else f"b[height<={h}]"
        args += ["-f", selector]

    args += [url]
    return args


def stream_process(args: list[str], q: Queue):
    try:
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if is_windows() else 0,
        )
        if process.stdout:
            for line in process.stdout:
                q.put(("line", line.rstrip()))
        rc = process.wait()
        q.put(("done", rc))
    except Exception as exc:
        q.put(("error", str(exc)))


def progress_from_line(line: str) -> float | None:
    m = re.search(r"\[download\]\s+([0-9.]+)%", line)
    if not m:
        return None
    try:
        return min(1.0, max(0.0, float(m.group(1)) / 100.0))
    except Exception:
        return None


def do_download(args: list[str]) -> bool:
    q: Queue = Queue()
    thread = threading.Thread(target=stream_process, args=(args, q), daemon=True)
    thread.start()
    progress = st.progress(0.0)
    status = st.empty()
    log_box = st.empty()
    logs: list[str] = []
    success = False

    while thread.is_alive() or not q.empty():
        try:
            kind, payload = q.get(timeout=0.15)
        except Empty:
            continue

        if kind == "line":
            logs.append(payload)
            if len(logs) > 30:
                logs = logs[-30:]
            p = progress_from_line(payload)
            if p is not None:
                progress.progress(p)
            status.caption(payload[-220:])
            log_box.code("\n".join(logs), language=None)
        elif kind == "done":
            success = payload == 0
            if success:
                progress.progress(1.0)
                st.success("Download completed.")
            else:
                st.error(f"yt-dlp exited with code {payload}.")
        elif kind == "error":
            st.error(payload)

    thread.join(timeout=1)
    return success


def newest_files(folder: Path, limit: int = 8) -> list[Path]:
    try:
        files = [p for p in folder.iterdir() if p.is_file()]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return files[:limit]
    except Exception:
        return []


# Authenticated browser mode
MEDIA_EXTENSIONS = (".mp4", ".m3u8", ".mpd", ".webm", ".m4v", ".mov", ".m4a", ".mp3", ".aac", ".ts")
MEDIA_CONTENT_TYPES = (
    "video/",
    "audio/",
    "application/vnd.apple.mpegurl",
    "application/x-mpegurl",
    "application/dash+xml",
)


def playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except Exception:
        return False


def detect_browser_channel(preference: str) -> str:
    """Return Playwright channel name. Chrome/Edge must already be installed locally."""
    if preference == "Microsoft Edge":
        return "msedge"
    return "chrome"


def is_media_response(url: str, content_type: str) -> bool:
    low_url = url.lower().split("?", 1)[0]
    low_ct = (content_type or "").lower()
    return any(low_url.endswith(ext) for ext in MEDIA_EXTENSIONS) or any(low_ct.startswith(ct) for ct in MEDIA_CONTENT_TYPES)


def redact_candidate_label(candidate: dict, index: int) -> str:
    url = candidate.get("url", "")
    ct = candidate.get("content_type") or "media"
    try:
        name = unquote(Path(urlparse(url).path).name)
    except Exception:
        name = ""
    if not name:
        name = urlparse(url).netloc or f"media-{index}"
    if len(name) > 85:
        name = name[:82] + "…"
    return f"{index}. {name}  ·  {ct}"


def capture_authenticated_media(
    start_url: str,
    browser_preference: str,
    timeout_seconds: int,
    persist_session: bool,
) -> tuple[list[dict], list[dict], str | None]:
    """
    Opens a real local Chromium browser. The user performs login directly on the website.
    We capture only media request metadata/cookies after the browser has authenticated.
    No credentials are read or stored by this app.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return [], [], f"Playwright is not available: {exc}"

    if persist_session:
        profile_dir = AUTH_PROFILE_DIR
        profile_dir.mkdir(exist_ok=True)
        temp_profile = None
    else:
        temp_profile = tempfile.TemporaryDirectory(prefix="mediacatch-browser-")
        profile_dir = Path(temp_profile.name)

    found: list[dict] = []
    seen: set[str] = set()
    last_found_at: float | None = None
    channel = detect_browser_channel(browser_preference)

    try:
        with sync_playwright() as p:
            try:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    channel=channel,
                    headless=False,
                    no_viewport=True,
                    args=["--start-maximized"],
                )
            except Exception as first_exc:
                fallback = "msedge" if channel == "chrome" else "chrome"
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=str(profile_dir),
                        channel=fallback,
                        headless=False,
                        no_viewport=True,
                        args=["--start-maximized"],
                    )
                except Exception:
                    return [], [], (
                        f"Could not launch {browser_preference}. Make sure Chrome or Edge is installed. "
                        f"Details: {first_exc}"
                    )

            def on_response(response):
                nonlocal last_found_at
                try:
                    ct = response.headers.get("content-type", "")
                    u = response.url
                    if response.status not in (200, 206):
                        return
                    if not is_media_response(u, ct):
                        return
                    if not u.startswith(("http://", "https://")) or u in seen:
                        return
                    seen.add(u)
                    req_headers = response.request.headers
                    found.append(
                        {
                            "url": u,
                            "status": response.status,
                            "content_type": ct.split(";", 1)[0],
                            "request_headers": {
                                k.lower(): v
                                for k, v in req_headers.items()
                                if k.lower() in {"user-agent", "referer", "origin", "authorization"}
                            },
                        }
                    )
                    last_found_at = time.time()
                except Exception:
                    pass

            context.on("response", on_response)
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(start_url, wait_until="domcontentloaded", timeout=60_000)

            started = time.time()
            while time.time() - started < timeout_seconds:
                if context.pages:
                    # Use the most recent page: login/player flows may open a new tab.
                    page = context.pages[-1]
                time.sleep(0.35)
                # After the first media item, wait a few seconds to collect related streams.
                if last_found_at and time.time() - last_found_at > 4.0:
                    break

            cookies = context.cookies()
            context.close()

        return found, cookies, None
    except Exception as exc:
        return found, [], f"Error while capturing browser traffic: {exc}"
    finally:
        if temp_profile is not None:
            temp_profile.cleanup()


def cookie_domain_matches(cookie_domain: str, target_host: str) -> bool:
    d = cookie_domain.lstrip(".").lower()
    h = target_host.lower()
    return h == d or h.endswith("." + d)


def write_netscape_cookie_file(cookies: list[dict], target_url: str) -> str | None:
    if not cookies:
        return None
    host = urlparse(target_url).hostname or ""
    lines = ["# Netscape HTTP Cookie File", "# Created locally by MediaCatch; deleted after the download."]
    count = 0
    for c in cookies:
        domain = c.get("domain", "")
        if domain and host and not cookie_domain_matches(domain, host):
            continue
        include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
        path = c.get("path") or "/"
        secure = "TRUE" if c.get("secure") else "FALSE"
        expires = c.get("expires", -1)
        expires = int(expires) if isinstance(expires, (int, float)) and expires > 0 else 0
        name = str(c.get("name") or "")
        value = str(c.get("value") or "")
        if not name:
            continue
        lines.append("\t".join([domain, include_subdomains, path, secure, str(expires), name, value]))
        count += 1
    if not count:
        return None
    path = Path(tempfile.gettempdir()) / f"mediacatch-cookies-{uuid.uuid4().hex}.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def build_authenticated_download_command(candidate: dict, cookies: list[dict], output_dir: Path) -> tuple[list[str], str | None]:
    cmd = get_ytdlp_command()
    if not cmd:
        raise RuntimeError("yt-dlp is not available")
    url = candidate["url"]
    headers = candidate.get("request_headers") or {}
    out_template = str(output_dir / "%(title).180B [%(id)s].%(ext)s")
    args = cmd + ["--newline", "--windows-filenames", "--no-overwrites", "--continue", "--output", out_template]
    args += ffmpeg_location_arg()

    cookie_file = write_netscape_cookie_file(cookies, url)
    if cookie_file:
        args += ["--cookies", cookie_file]

    if headers.get("user-agent"):
        args += ["--user-agent", headers["user-agent"]]
    if headers.get("referer"):
        args += ["--referer", headers["referer"]]
    if headers.get("origin"):
        args += ["--add-header", f"Origin:{headers['origin']}"]
    if headers.get("authorization"):
        args += ["--add-header", f"Authorization:{headers['authorization']}"]

    # For manifests, ffmpeg/yt-dlp handles segments and merging; MP4 files are downloaded directly.
    args += [url]
    return args, cookie_file


def clear_auth_profile() -> tuple[bool, str]:
    if not AUTH_PROFILE_DIR.exists():
        return True, "No saved browser session found."
    try:
        shutil.rmtree(AUTH_PROFILE_DIR)
        return True, "Saved local browser session deleted."
    except Exception as exc:
        return False, f"Could not delete the session: {exc}. Close any Chrome/Edge windows opened by the app and try again."


st.title("MediaCatch")
st.caption(
    "Local Python/Streamlit media downloader with a standard yt-dlp mode and an authenticated browser mode "
    "for dynamic sites you are authorized to access."
)

if not is_windows():
    st.warning("This package is primarily prepared for Windows. On other systems, install yt-dlp in PATH or as a Python module.")

if get_ytdlp_command() is None:
    st.warning("yt-dlp is not available yet.")
    if is_windows() and st.button("Install official yt-dlp", type="primary"):
        with st.spinner("Downloading the official binary from GitHub and verifying SHA-256…"):
            ok, msg = download_ytdlp()
        (st.success if ok else st.error)(msg)
        if ok:
            st.rerun()
else:
    cmd = get_ytdlp_command()
    version_text = "available"
    if cmd:
        try:
            cp = run_capture(cmd + ["--version"], timeout=10)
            if cp.returncode == 0 and cp.stdout.strip():
                version_text = cp.stdout.strip()
        except Exception:
            pass
    st.success(f"yt-dlp: {version_text}")

ffmpeg = find_ffmpeg()
if ffmpeg:
    st.caption(f"FFmpeg detected: {ffmpeg}")
else:
    st.info("FFmpeg not detected. MP3 conversion and some high-quality stream merges require FFmpeg. Run INSTALL_FFMPEG.bat.")

js_runtime = find_js_runtime()
if js_runtime:
    st.caption(f"JavaScript runtime for YouTube: {js_runtime[0]} · {js_runtime[1]}")
    st.caption("YouTube EJS solver: automatic via the official yt-dlp component (ejs:github)")
else:
    st.warning(
        "No JavaScript runtime detected. YouTube may return false ‘This video is not available’ errors without Deno/Node. "
        "Deno is recommended on Windows; run INSTALL_DENO.bat."
    )
    deno_bat = APP_DIR / "INSTALL_DENO.bat"
    if is_windows() and deno_bat.exists() and st.button("Install Deno for YouTube", key="install_deno_btn"):
        try:
            os.startfile(deno_bat)  # type: ignore[attr-defined]
            st.info("The installer window has opened. When it finishes, close and restart this app.")
        except Exception as exc:
            st.error(f"Could not launch INSTALL_DENO.bat: {exc}")

with st.sidebar:
    st.header("Destination")
    output_dir_text = st.text_input("Download folder", value=str(DOWNLOADS_DIR))
    if st.button("Open download folder", use_container_width=True):
        try:
            target = safe_download_dir(output_dir_text)
            if is_windows():
                os.startfile(target)  # type: ignore[attr-defined]
            else:
                st.info(str(target))
        except Exception as exc:
            st.error(str(exc))
    st.caption("This app does not remove or bypass DRM. Use it only for content you are authorized to download.")

standard_tab, auth_tab = st.tabs([
    "Standard · YouTube / TikTok / Vimeo / direct URLs",
    "Authenticated browser · login-protected sites",
])

with standard_tab:
    st.subheader("Standard download")
    st.write("Use this mode for YouTube, TikTok, Vimeo, other sites supported by yt-dlp, and direct MP4/M3U8/MPD URLs.")

    c1, c2 = st.columns(2)
    with c1:
        browser = st.selectbox(
            "Browser cookies (optional)",
            ["None", "Firefox", "Chrome", "Edge"],
            help="Useful for content that requires a browser session. On some Chrome/Windows versions, cookie extraction can fail because of DPAPI; use Firefox or the authenticated-browser mode in that case.",
            key="std_browser",
        )
        playlist = st.checkbox("Allow playlists", value=False, key="std_playlist")
    with c2:
        subtitles = st.checkbox("Download IT/EN subtitles", value=False, key="std_subtitles")
        referer = st.text_input(
            "Referer (optional)",
            placeholder="https://example.com/course-page",
            help="Useful for direct streams that validate the referring page.",
            key="std_referer",
        )

    url = st.text_input("Video URL", placeholder="https://youtube.com/...  or https://.../video.mp4", key="std_url")

    if url.strip() and is_spa_fragment_url(url) and not looks_like_direct_media_url(url):
        st.warning("This looks like a dynamic web-app URL (#/...). If yt-dlp returns Unsupported URL, use the ‘Authenticated browser’ tab.")

    analyze_clicked = st.button("Analyze", use_container_width=True, disabled=not bool(url.strip()), key="std_analyze")

    if "info" not in st.session_state:
        st.session_state.info = None
    if "last_url" not in st.session_state:
        st.session_state.last_url = ""

    if analyze_clicked:
        if not valid_http_url(url):
            st.error("Enter a valid http/https URL.")
        elif get_ytdlp_command() is None:
            st.error("Install yt-dlp first.")
        else:
            with st.spinner("Analyzing video…"):
                info, err = analyze_url(url.strip(), browser, playlist, referer)
            if err:
                st.error(err)
                low_err = err.lower()
                if is_youtube_url(url):
                    if find_js_runtime() is None:
                        st.warning(
                            "This YouTube error likely means the JavaScript runtime required by yt-dlp is missing. "
                            "Install Deno with INSTALL_DENO.bat, then close and restart the app."
                        )
                    elif "challenge solving failed" in low_err or "remote component" in low_err or "ejs" in low_err:
                        st.warning(
                            "YouTube requested an EJS challenge. MediaCatch automatically enables yt-dlp’s official solver via ejs:github. "
                            "If this warning still appears, make sure GitHub is reachable and update yt-dlp with UPDATE_YT_DLP.bat."
                        )
                if "unsupported url" in low_err or "401" in low_err or "unauthorized" in low_err or "dpapi" in low_err:
                    st.info(
                        "For a dynamic page or a file that requires login, switch to the ‘Authenticated browser’ tab. "
                        "Sign in directly in the local browser window; the app does not ask for your username or password."
                    )
                st.session_state.info = None
            else:
                st.session_state.info = info
                st.session_state.last_url = url.strip()

    info = st.session_state.info
    if info and st.session_state.last_url == url.strip():
        st.divider()
        thumb = info.get("thumbnail")
        if thumb:
            try:
                st.image(thumb, width=420)
            except Exception:
                pass
        st.subheader(info.get("title") or "Video")
        uploader = info.get("uploader") or info.get("channel") or "—"
        m1, m2, m3 = st.columns(3)
        m1.metric("Author", str(uploader)[:30])
        m2.metric("Duration", format_duration(info.get("duration")))
        m3.metric("Views", format_count(info.get("view_count")))

        heights = available_heights(info)
        quality_options = ["Best"] + [f"{h}p" for h in heights]
        media_type = st.selectbox("Format", ["MP4 Video", "Best available format", "MP3 Audio"], key="std_format")
        quality = st.selectbox("Maximum quality", quality_options, key="std_quality")
        if media_type == "MP3 Audio" and not ffmpeg:
            st.warning("Install FFmpeg before converting to MP3.")

        if st.button("Download", type="primary", use_container_width=True, key="std_download"):
            try:
                out_dir = safe_download_dir(output_dir_text)
                args = build_download_command(
                    url=url.strip(),
                    media_type=media_type,
                    quality=quality,
                    output_dir=out_dir,
                    browser=browser,
                    playlist=playlist,
                    subtitles=subtitles,
                    referer=referer,
                )
                ok = do_download(args)
                if ok:
                    recent = newest_files(out_dir)
                    if recent:
                        st.caption("Recently created files:")
                        for p in recent[:8]:
                            st.write(f"• {p.name}")
            except Exception as exc:
                st.error(str(exc))

with auth_tab:
    st.subheader("Dynamic / login-protected sites")
    st.write(
        "This is an additional mode for dynamic sites. Paste the course or player page. MediaCatch opens a local browser window: "
        "sign in directly on the website and start the video. The app does not read or store usernames or passwords; "
        "it only detects media requests already authorized by your browser session."
    )

    auth_url = st.text_input("Page to open", placeholder="https://example.com/#/online-course-player/...", key="auth_url")
    ca, cb = st.columns(2)
    with ca:
        auth_browser = st.selectbox("Local browser", ["Google Chrome", "Microsoft Edge"], key="auth_browser")
        persist_session = st.checkbox(
            "Remember login session on this PC",
            value=True,
            help="Stores a separate browser profile inside the app folder. Credentials are handled by the website/browser, not by MediaCatch.",
            key="auth_persist",
        )
    with cb:
        auth_timeout = st.selectbox(
            "Maximum time for login + video start",
            [60, 120, 180, 300],
            index=2,
            format_func=lambda x: f"{x} seconds",
            key="auth_timeout",
        )
        if st.button("Delete saved browser session", use_container_width=True, key="clear_auth"):
            ok, msg = clear_auth_profile()
            (st.success if ok else st.error)(msg)

    with st.expander("How this mode works"):
        st.markdown(
            """
1. Click **Open browser and detect media**.
2. Chrome/Edge opens with a separate MediaCatch profile.
3. If needed, sign in **directly on the website**.
4. Open the course/player and start the video.
5. When MediaCatch detects MP4/M3U8/MPD or another media request, it records the URL and session context needed for the download.
6. Return here, choose the detected media and click **Download captured media**.

The browser window closes automatically a few seconds after media is detected or when the timeout expires.
            """
        )

    if not playwright_available():
        st.error("Playwright is not installed in this environment. Close the app and run START_APP.bat again; dependencies are installed automatically.")

    capture_clicked = st.button(
        "Open browser and detect media",
        type="primary",
        use_container_width=True,
        disabled=not bool(auth_url.strip()) or not playwright_available(),
        key="auth_capture",
    )

    if "auth_candidates" not in st.session_state:
        st.session_state.auth_candidates = []
    if "auth_cookies" not in st.session_state:
        st.session_state.auth_cookies = []
    if "auth_source_url" not in st.session_state:
        st.session_state.auth_source_url = ""

    if capture_clicked:
        if not valid_http_url(auth_url):
            st.error("Enter a valid http/https URL.")
        else:
            st.info(
                "A browser window has been opened. Sign in on the website if needed and start the video. "
                "Do not enter credentials into Streamlit; use them only in the website window."
            )
            with st.spinner("Waiting for media from the browser…"):
                candidates, cookies, err = capture_authenticated_media(
                    start_url=auth_url.strip(),
                    browser_preference=auth_browser,
                    timeout_seconds=int(auth_timeout),
                    persist_session=persist_session,
                )
            if err:
                st.error(err)
            if candidates:
                st.session_state.auth_candidates = candidates
                st.session_state.auth_cookies = cookies
                st.session_state.auth_source_url = auth_url.strip()
                st.success(f"Detected {len(candidates)} media item(s). Select one to download.")
            else:
                st.session_state.auth_candidates = []
                st.session_state.auth_cookies = []
                st.warning(
                    "No media detected. Try again with a longer timeout and make sure the video is actually playing. "
                    "If the site uses DRM, this app does not attempt to bypass it."
                )

    candidates = st.session_state.auth_candidates
    if candidates:
        labels = [redact_candidate_label(c, i + 1) for i, c in enumerate(candidates)]
        selected_label = st.selectbox("Detected media", labels, key="auth_candidate_choice")
        selected_index = labels.index(selected_label)
        candidate = candidates[selected_index]

        st.caption(f"HTTP {candidate.get('status', '—')} · {candidate.get('content_type') or 'content type not declared'}")
        st.code(candidate.get("url", ""), language=None)

        if st.button("Download captured media", type="primary", use_container_width=True, key="auth_download"):
            cookie_file = None
            try:
                out_dir = safe_download_dir(output_dir_text)
                args, cookie_file = build_authenticated_download_command(
                    candidate=candidate,
                    cookies=st.session_state.auth_cookies,
                    output_dir=out_dir,
                )
                ok = do_download(args)
                if ok:
                    recent = newest_files(out_dir)
                    if recent:
                        st.caption("Recently created files:")
                        for p in recent[:8]:
                            st.write(f"• {p.name}")
            except Exception as exc:
                st.error(str(exc))
            finally:
                if cookie_file:
                    try:
                        Path(cookie_file).unlink(missing_ok=True)
                    except Exception:
                        pass

st.divider()
with st.expander("Limitations and safety"):
    st.write(
        "Authenticated browser mode uses a real browser window on your PC and can optionally keep a separate browser profile "
        "to preserve the website session. Credentials are entered directly on the website and are never requested by MediaCatch. "
        "The downloader does not remove DRM and must not be used for content you are not authorized to download."
    )
