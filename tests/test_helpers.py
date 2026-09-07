from app import (
    format_duration,
    is_youtube_url,
    looks_like_direct_media_url,
    progress_from_line,
    valid_http_url,
)


def test_valid_http_url():
    assert valid_http_url("https://example.com")
    assert valid_http_url("http://example.com/video")
    assert not valid_http_url("ftp://example.com")
    assert not valid_http_url("example.com")
    assert not valid_http_url("")


def test_is_youtube_url():
    assert is_youtube_url("https://www.youtube.com/watch?v=abc123")
    assert is_youtube_url("https://youtu.be/abc123")
    assert is_youtube_url("https://www.youtube-nocookie.com/embed/abc123")
    assert not is_youtube_url("https://vimeo.com/123456")
    assert not is_youtube_url("https://example.com")


def test_looks_like_direct_media_url():
    assert looks_like_direct_media_url("https://example.com/video.mp4")
    assert looks_like_direct_media_url("https://example.com/master.m3u8?token=123")
    assert looks_like_direct_media_url("https://example.com/stream.mpd")
    assert looks_like_direct_media_url("https://example.com/audio.mp3")
    assert not looks_like_direct_media_url("https://example.com/watch/123")


def test_format_duration():
    assert format_duration(65) == "1:05"
    assert format_duration(3600) == "1:00:00"
    assert format_duration(3661) == "1:01:01"
    assert format_duration("invalid") == "—"


def test_progress_from_line():
    assert progress_from_line("[download]  25.0% of 10.00MiB") == 0.25
    assert progress_from_line("[download] 100.0% of 10.00MiB") == 1.0
    assert progress_from_line("some unrelated log line") is None
