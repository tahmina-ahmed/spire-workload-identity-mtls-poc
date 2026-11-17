import json
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


EXPECTED_CLIENT_ID = "spiffe://example.org/ns/demo/sa/service-a"


class MTLSHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path != "/secure":
            self.send_error(404)
            return

        try:
            client_spiffe_id = self.connection.getpeercert()[
                "subjectAltName"
            ]

            client_ids = [
                value for name, value in client_spiffe_id
                if name == "URI"
            ]

            if client_ids != [EXPECTED_CLIENT_ID]:
                self.send_error(403, "Unauthorized SPIFFE identity")
                return

            response = {
                "service": "service-b",
                "authenticated_client": client_ids[0],
                "authorization": "allowed",
                "transport": "mutual-tls"
            }

            body = json.dumps(response).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except Exception:
            self.send_error(403, "Client identity verification failed")


def start_mtls_server(tls_material):
    server = ThreadingHTTPServer(("0.0.0.0", 8443), MTLSHandler)
    server.socket = tls_material.server_context().wrap_socket(
        server.socket,
        server_side=True
    )

    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    return server
