import json
import socket
import ssl

from tls_utils import SPIFFETLSMaterial


EXPECTED_SERVER_ID = "spiffe://example.org/ns/demo/sa/service-b"


def call_service_b(tls_material):
    context = tls_material.client_context()

    with socket.create_connection(
        ("service-b.demo.svc.cluster.local", 8443),
        timeout=5
    ) as raw_socket:

        with context.wrap_socket(
            raw_socket,
            server_hostname="service-b.demo.svc.cluster.local"
        ) as tls_socket:

            certificate = tls_socket.getpeercert()

            server_ids = [
                value
                for name, value in certificate.get("subjectAltName", [])
                if name == "URI"
            ]

            if server_ids != [EXPECTED_SERVER_ID]:
                raise ssl.SSLError(
                    f"Unexpected server SPIFFE ID: {server_ids}"
                )

            request = (
                "GET /secure HTTP/1.1\r\n"
                "Host: service-b.demo.svc.cluster.local\r\n"
                "Connection: close\r\n\r\n"
            )

            tls_socket.sendall(request.encode())

            response = b""
            while True:
                chunk = tls_socket.recv(4096)
                if not chunk:
                    break
                response += chunk

            headers, body = response.split(b"\r\n\r\n", 1)

            print("HTTP response:")
            print(headers.decode())
            print("Response body:")
            print(json.dumps(json.loads(body), indent=2))


if __name__ == "__main__":
    from spiffe import X509Source

    source = X509Source()
    material = SPIFFETLSMaterial(source)

    try:
        print("Client SPIFFE ID:", material.svid.spiffe_id)
        call_service_b(material)
    finally:
        material.close()
        source.close()
