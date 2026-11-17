import ssl
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding
from spiffe import TrustDomain


class SPIFFETLSMaterial:

    def __init__(self, source):
        context = source.get_x509_context()
        self.svid = context.default_svid

        bundle = source.get_bundle_for_trust_domain(
            TrustDomain("example.org")
        )

        self.temp_dir = tempfile.TemporaryDirectory(
            prefix="spiffe-tls-"
        )
        self.directory = Path(self.temp_dir.name)

        self.cert_file = self.directory / "svid-chain.pem"
        self.key_file = self.directory / "svid-key.pem"
        self.ca_file = self.directory / "trust-bundle.pem"

        certificate_pem = b"".join(
            cert.public_bytes(Encoding.PEM)
            for cert in self.svid.cert_chain
        )

        private_key_pem = self.svid.private_key.private_bytes(
            encoding=Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        ca_pem = b"".join(
            cert.public_bytes(Encoding.PEM)
            for cert in bundle.x509_authorities
        )

        self.cert_file.write_bytes(certificate_pem)
        self.key_file.write_bytes(private_key_pem)
        self.ca_file.write_bytes(ca_pem)

        self.key_file.chmod(0o600)
        self.cert_file.chmod(0o600)
        self.ca_file.chmod(0o600)

    def server_context(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2

        context.load_cert_chain(
            certfile=str(self.cert_file),
            keyfile=str(self.key_file)
        )

        context.load_verify_locations(
            cafile=str(self.ca_file)
        )

        context.verify_mode = ssl.CERT_REQUIRED

        return context

    def client_context(self):
        context = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH,
            cafile=str(self.ca_file)
        )

        context.minimum_version = ssl.TLSVersion.TLSv1_2

        # SPIFFE identity is verified explicitly using the URI SAN.
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED

        context.load_cert_chain(
            certfile=str(self.cert_file),
            keyfile=str(self.key_file)
        )

        return context

    @staticmethod
    def peer_spiffe_id(tls_socket):
        certificate = tls_socket.getpeercert()

        uri_sans = [
            value
            for name, value in certificate.get("subjectAltName", [])
            if name == "URI"
        ]

        if len(uri_sans) != 1:
            raise ssl.SSLError(
                "Peer certificate must contain exactly one SPIFFE URI SAN"
            )

        return uri_sans[0]

    def close(self):
        self.temp_dir.cleanup()
