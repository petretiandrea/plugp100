import ssl
from typing import Optional

from yarl import URL

DEVICE_CIPHERS = ":".join(
    [
        "ECDHE-RSA-AES128-GCM-SHA256",
        "AES256-GCM-SHA384",
        "AES256-SHA256",
        "AES128-GCM-SHA256",
        "AES128-SHA256",
        "AES256-SHA",
    ]
)


def ssl_context_for_url(url: str) -> Optional[ssl.SSLContext]:
    """Return the TLS context used by local devices for HTTPS endpoints."""
    if URL(url).scheme != "https":
        return None

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.set_ciphers(DEVICE_CIPHERS)
    context.check_hostname = False
    # TP-Link devices use locally issued certificates that cannot be validated
    # through the system CA store. Authentication remains protocol-level.
    context.verify_mode = ssl.CERT_NONE
    return context
