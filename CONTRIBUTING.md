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
```

Create a virtual environment.

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install development dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

## Run MediaCatch

```bash
python -m streamlit run app.py
```

## Run the tests

Before submitting changes, run:

```bash
python -m pytest -q
```

Also verify that the main application compiles:

```bash
python -m py_compile app.py
```

GitHub Actions automatically runs the test suite on supported Python versions for pushes and pull requests.

## Reporting bugs

Before opening a bug report:

1. Make sure you are using the latest MediaCatch version.
2. Update yt-dlp if appropriate.
3. Check that FFmpeg and the required browser/runtime are correctly installed.
4. Check existing GitHub Issues for the same problem.

When reporting a bug, include:

- Operating system
- Python version
- MediaCatch version
- yt-dlp version
- Browser used, if relevant
- Whether authenticated browser mode was involved
- The error message or relevant log output
- Steps needed to reproduce the problem

Do not include passwords, authentication tokens, cookies or other private credentials.

## Feature requests

Feature requests are welcome.

Please explain:

- What problem the feature would solve
- How you expect it to work
- Whether it affects standard downloads, authenticated browser mode, YouTube compatibility or another part of MediaCatch

## Pull requests

Keep pull requests focused on one change whenever possible.

Before submitting a pull request:

- Run the tests
- Check Python syntax
- Avoid unrelated code formatting changes
- Update documentation if user-facing behavior changes
- Add or update tests when changing testable functionality

Use a clear title and explain what changed and why.

## Code style

Prefer:

- Clear Python code
- Small and focused functions
- Explicit error handling
- Cross-platform behavior where practical
- Descriptive names
- Minimal additional dependencies

Avoid introducing external services or telemetry unless there is a clear reason and it is explicitly documented.

## Security

If you discover a security issue, do not publish sensitive details in a public issue.

Please refer to `SECURITY.md` for the appropriate reporting process.

## License

By contributing to MediaCatch, you agree that your contributions may be distributed under the repository's MIT License.
