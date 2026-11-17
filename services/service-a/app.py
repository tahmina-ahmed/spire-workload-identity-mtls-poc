from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from spiffe import X509Source


@asynccontextmanager
async def lifespan(app: FastAPI):
    with X509Source() as source:
        app.state.x509_source = source
        yield


app = FastAPI(
    title="SPIRE Service A",
    lifespan=lifespan
)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/identity")
def identity(request: Request):
    source = request.app.state.x509_source
    svid = source.svid

    return {
        "service": "service-a",
        "spiffe_id": str(svid.spiffe_id),
        "identity_type": "X509-SVID",
        "status": "authenticated"
    }
