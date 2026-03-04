import warnings

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from utils.configs import enable_gateway, api_prefix

warnings.filterwarnings("ignore")


api_prefix_path = ""
if isinstance(api_prefix, str) and api_prefix.strip():
    api_prefix_path = api_prefix.strip("/")

docs_url = f"/{api_prefix_path}/docs" if api_prefix_path else "/docs"
redoc_url = f"/{api_prefix_path}/redoc" if api_prefix_path else "/redoc"
openapi_url = f"/{api_prefix_path}/openapi.json" if api_prefix_path else "/openapi.json"

log_config = uvicorn.config.LOGGING_CONFIG
default_format = "%(asctime)s | %(levelname)s | %(message)s"
access_format = r'%(asctime)s | %(levelname)s | %(client_addr)s: %(request_line)s %(status_code)s'
log_config["formatters"]["default"]["fmt"] = default_format
log_config["formatters"]["access"]["fmt"] = access_format

app = FastAPI(docs_url=docs_url, redoc_url=redoc_url, openapi_url=openapi_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
security_scheme = HTTPBearer()

from app import app

import api.chat2api

if enable_gateway:
    import gateway.share
    import gateway.login
    import gateway.chatgpt
    import gateway.gpts
    import gateway.admin
    import gateway.v1
    import gateway.backend
else:
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
    async def reverse_proxy():
        raise HTTPException(status_code=404, detail="Gateway is disabled")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5005)
    # uvicorn.run("app:app", host="0.0.0.0", port=5005, ssl_keyfile="key.pem", ssl_certfile="cert.pem")

