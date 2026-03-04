from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def mask_secret(value, prefix=4, suffix=4):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return text
    if len(text) <= prefix + suffix:
        return "*" * len(text)
    return f"{text[:prefix]}{'*' * (len(text) - prefix - suffix)}{text[-suffix:]}"


def mask_token(token):
    if token is None:
        return None
    token_text = str(token).strip()
    if not token_text:
        return token_text
    if "," in token_text:
        return ",".join(mask_secret(part.strip(), prefix=6, suffix=4) for part in token_text.split(","))
    return mask_secret(token_text, prefix=6, suffix=4)


def mask_token_list(tokens):
    if tokens is None:
        return None
    return [mask_token(token) for token in tokens]


def mask_proxy_url(proxy_value):
    if proxy_value is None:
        return None
    if isinstance(proxy_value, list):
        return [mask_proxy_url(item) for item in proxy_value]

    proxy_text = str(proxy_value).strip()
    if not proxy_text:
        return proxy_text

    try:
        parts = urlsplit(proxy_text)
    except Exception:
        return mask_secret(proxy_text, prefix=3, suffix=2)

    username = parts.username
    password = parts.password
    if not username and not password:
        return proxy_text

    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    safe_user = mask_secret(username or "", prefix=1, suffix=1) if username else ""
    safe_password = "***" if password else ""
    auth_part = safe_user if not safe_password else f"{safe_user}:{safe_password}"
    netloc = f"{auth_part}@{host}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
