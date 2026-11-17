from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from spiffe import X509Source

from tls_utils import SPIFFETLSMaterial
from mtls_server import start_mtls_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    source = X509Source()
    tls_material = SPIFFETLSMaterial(source)
    mtls_server = start_mtls_server(tls_material)

    app.state.x509_source = source
    app.state.tls_material = tls_material
    app.state.mtls_server = mtls_server

    try:
        yield
    finally:
        mtls_server.shutdown()
        mtls_server.server_close()
        tls_material.close()
        source.close()


app = FastAPI(
    title="SPIRE Service B",
    lifespan=lifespan
)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/identity")
def identity(request: Request):
    source = request.app.state.x509_source
    svid = source.get_x509_context().default_svid

    return {
        "service": "service-b",
        "spiffe_id": str(svid.spiffe_id),
        "identity_type": "X509-SVID",
        "status": "authenticated"
    }
