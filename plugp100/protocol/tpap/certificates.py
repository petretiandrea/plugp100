"""TPAP device certificate parsing and verification."""

import base64
from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa

from plugp100.responses.tapo_exception import TapoProtocolError


class TpapCertificateVerifier:
    """Certificate helpers shared by the TPAP transport and handshake."""

    TPAP_ROOT_CA_PEM = """
-----BEGIN CERTIFICATE-----
MIICNzCCAdygAwIBAgIUNLD7w5j5WU/efCe8bqkfGSRGgLYwCgYIKoZIzj0EAwIw
ezEnMCUGA1UEAwweVFAtTElOSyBTWVNURU1TIERFVklDRSBST09UIENBMR0wGwYD
VQQKDBRUUC1MSU5LIFNZU1RFTVMgSU5DLjEPMA0GA1UEBwwGSXJ2aW5lMRMwEQYD
VQQIDApDYWxpZm9ybmlhMQswCQYDVQQGEwJVUzAgFw0yNDExMjIwMjU3NDhaGA8y
MDU0MTExNTAyNTc0OFowezEnMCUGA1UEAwweVFAtTElOSyBTWVNURU1TIERFVklD
RSBST09UIENBMR0wGwYDVQQKDBRUUC1MSU5LIFNZU1RFTVMgSU5DLjEPMA0GA1UE
BwwGSXJ2aW5lMRMwEQYDVQQIDApDYWxpZm9ybmlhMQswCQYDVQQGEwJVUzBZMBMG
ByqGSM49AgEGCCqGSM49AwEHA0IABLwo8H9H6BoJDvcoewi4wPrPryVXir4z4yXV
n29R5XCAcFfKk06pYPupG6pjaKOLKWXnaOdPZThDFxwGLo3urV2jPDA6MAsGA1Ud
DwQEAwIBhjAMBgNVHRMEBTADAQH/MB0GA1UdDgQWBBRivfUtiHYsZBOKo80uZEwk
XhBkdDAKBggqhkjOPQQDAgNJADBGAiEA+7j5jemtXcGYN0unH+9rjVhVAL7WrsOi
5rbc0IIvD6MCIQCZuGGssu4Ygt2V8Vr0QF2fO9wxfNB3aRRMYQ+6lMrLGA==
-----END CERTIFICATE-----
""".strip()

    @classmethod
    def _load_root_ca_certificate(cls) -> x509.Certificate:
        return x509.load_pem_x509_certificate(cls.TPAP_ROOT_CA_PEM.encode())

    @classmethod
    def _load_certificate_value(cls, certificate_value: str) -> x509.Certificate:
        raw_value = certificate_value.strip()
        if not raw_value:
            raise TapoProtocolError("Empty certificate value")

        candidates: list[bytes] = [raw_value.encode()]
        decoded_candidate: bytes | None = None
        try:
            decoded_candidate = base64.b64decode(raw_value, validate=True)
        except Exception:
            decoded_candidate = None
        if decoded_candidate is not None:
            candidates.insert(0, decoded_candidate)

        last_error: Exception | None = None
        for candidate in candidates:
            try:
                if b"-----BEGIN CERTIFICATE-----" in candidate:
                    return x509.load_pem_x509_certificate(candidate)
                return x509.load_der_x509_certificate(candidate)
            except Exception as exc:
                last_error = exc

        raise TapoProtocolError("Invalid certificate value") from last_error

    @staticmethod
    def _verify_certificate_validity(certificate: x509.Certificate) -> None:
        now = datetime.now(timezone.utc)
        if hasattr(certificate, "not_valid_before_utc"):
            not_before = certificate.not_valid_before_utc
            not_after = certificate.not_valid_after_utc
        else:
            not_before = certificate.not_valid_before.replace(tzinfo=timezone.utc)
            not_after = certificate.not_valid_after.replace(tzinfo=timezone.utc)
        if now < not_before or now > not_after:
            raise TapoProtocolError("Certificate is outside its validity period")

    @staticmethod
    def _verify_certificate_signature(
        certificate: x509.Certificate, issuer: x509.Certificate
    ) -> None:
        public_key = issuer.public_key()
        signature_hash = certificate.signature_hash_algorithm
        if signature_hash is None:
            raise TapoProtocolError("Certificate signature hash algorithm is unavailable")
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                certificate.signature,
                certificate.tbs_certificate_bytes,
                ec.ECDSA(signature_hash),
            )
            return
        if isinstance(public_key, rsa.RSAPublicKey):
            public_key.verify(
                certificate.signature,
                certificate.tbs_certificate_bytes,
                padding.PKCS1v15(),
                signature_hash,
            )
            return
        raise TapoProtocolError(
            f"Unsupported DAC issuer public key type: {type(public_key).__name__}"
        )

    @classmethod
    def _verify_dac_certificate_chain(
        cls,
        dac_ca_certificate: x509.Certificate,
        dac_ica_certificate: x509.Certificate | None,
    ) -> None:
        try:
            root_certificate = cls._load_root_ca_certificate()
            cls._verify_certificate_validity(dac_ca_certificate)
            if dac_ica_certificate is not None:
                cls._verify_certificate_validity(dac_ica_certificate)
                cls._verify_certificate_signature(dac_ca_certificate, dac_ica_certificate)
                cls._verify_certificate_signature(dac_ica_certificate, root_certificate)
            else:
                cls._verify_certificate_signature(dac_ca_certificate, root_certificate)
        except Exception as exc:
            raise TapoProtocolError(
                f"DAC certificate chain verification failed: {exc}"
            ) from exc
