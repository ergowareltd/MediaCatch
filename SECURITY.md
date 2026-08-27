# Security notes

MediaCatch can open an authenticated browser session and temporarily use cookies or request headers that are already present in that local session.

- Never commit `.auth_browser_profile/`, exported cookies, downloaded media, `.env` files, or local browser profiles.
- Do not paste usernames, passwords, session cookies, bearer tokens, or `Copy as cURL` output into public issues.
- The authenticated browser profile is stored locally only when the user enables session persistence.
- MediaCatch does not attempt to remove or bypass DRM.
- Signed media URLs may expire and should be treated as sensitive while valid.

If you discover a security issue, avoid publishing secrets or exploit details in a public issue. Contact the repository owner privately instead.
