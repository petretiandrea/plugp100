from plugp100.common.credentials import AuthCredential
from plugp100.encryption.helpers import sha256, sha1, md5


def klap_handshake_v1() -> "KlapHandshakeRevision":
    return KlapHandshakeRevision()


def klap_handshake_v2() -> "KlapHandshakeRevision":
    return KlapHandshakeRevisionV2()


# lot of issue are related to mismatch of server version. So I think using older version could work.
class KlapHandshakeRevision:
    def generate_auth_hash(self, credentials: AuthCredential) -> bytes:
        return md5(
            md5(credentials.username.encode()) + md5(credentials.password.encode())
        )

    def handshake1_seed_auth_hash(
        self, local_seed: bytes, remote_seed: bytes, auth_hash: bytes
    ) -> bytes:
        return sha256(local_seed + auth_hash)

    def handshake2_seed_auth_hash(
        self, local_seed: bytes, remote_seed: bytes, auth_hash: bytes
    ) -> bytes:
        return sha256(remote_seed + auth_hash)


class KlapHandshakeRevisionV2(KlapHandshakeRevision):
    def generate_auth_hash(self, credentials: AuthCredential) -> bytes:
        return sha256(
            sha1(credentials.username.encode()) + sha1(credentials.password.encode())
        )

    def handshake1_seed_auth_hash(
        self, local_seed: bytes, remote_seed: bytes, auth_hash: bytes
    ) -> bytes:
        return sha256(local_seed + remote_seed + auth_hash)

    def handshake2_seed_auth_hash(
        self, local_seed: bytes, remote_seed: bytes, auth_hash: bytes
    ) -> bytes:
        return sha256(remote_seed + local_seed + auth_hash)
