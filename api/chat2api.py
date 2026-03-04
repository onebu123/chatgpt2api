import asyncio
import json
import time
import types

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Form, HTTPException, Request, Security
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from starlette.background import BackgroundTask

import utils.globals as globals
from api.models import model_proxy
from app import app, security_scheme, templates
from chatgpt.ChatService import ChatService
from chatgpt.authorization import refresh_all_tokens
from utils.Logger import logger
from utils.configs import admin_api_key, api_prefix, authorization_list, scheduled_refresh
from utils.retry import async_retry

scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def app_start():
    if scheduled_refresh:
        scheduler.add_job(
            id="refresh",
            func=refresh_all_tokens,
            trigger="cron",
            hour=3,
            minute=0,
            day="*/2",
            kwargs={"force_refresh": True},
        )
        scheduler.start()
        asyncio.get_event_loop().call_later(0, lambda: asyncio.create_task(refresh_all_tokens(force_refresh=False)))


async def to_send_conversation(request_data, req_token):
    chat_service = ChatService(req_token)
    try:
        await chat_service.set_dynamic_data(request_data)
        await chat_service.get_chat_requirements()
        return chat_service
    except HTTPException as e:
        await chat_service.close_client()
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        await chat_service.close_client()
        logger.error(f"Server error, {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


async def process(request_data, req_token):
    chat_service = await to_send_conversation(request_data, req_token)
    await chat_service.prepare_send_conversation()
    res = await chat_service.send_conversation()
    return chat_service, res


def _extract_bearer_token(request: Request):
    auth_header = request.headers.get("authorization", "")
    if not auth_header:
        return ""
    auth_parts = auth_header.split(" ", 1)
    if len(auth_parts) != 2:
        return ""
    if auth_parts[0].lower() != "bearer":
        return ""
    return auth_parts[1].strip()


def _verify_token_admin(request: Request, form_admin_key: str | None = None):
    bearer_token = _extract_bearer_token(request)
    header_admin_key = request.headers.get("x-admin-key", "").strip()
    query_admin_key = request.query_params.get("admin_key", "").strip()
    form_admin_key = (form_admin_key or "").strip()

    provided_candidates = [header_admin_key, query_admin_key, form_admin_key, bearer_token]
    provided_key = next((item for item in provided_candidates if item), "")

    if admin_api_key:
        if provided_key == admin_api_key:
            return
        raise HTTPException(status_code=401, detail="Unauthorized admin request")

    if authorization_list:
        if provided_key in authorization_list:
            return
        raise HTTPException(status_code=401, detail="Unauthorized admin request")

    raise HTTPException(
        status_code=403,
        detail="Token management is disabled. Set ADMIN_API_KEY or AUTHORIZATION.",
    )


def _get_tokens_count():
    return len(set(globals.token_list) - set(globals.error_token_list))


def _build_models_payload():
    # 返回一组稳定的 OpenAI 风格模型列表，避免客户端探测 /v1/models 失败。
    extra_models = {
        "auto",
        "text-davinci-002-render-sha",
        "gpt-4o-canmore",
        "gpt-4-mobile",
        "gpt-4.5o",
        "o1-pro",
        "o3-mini-medium",
        "o3-mini-low",
    }
    model_ids = sorted(set(model_proxy.keys()) | set(model_proxy.values()) | extra_models)
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": now,
                "owned_by": "openai",
            }
            for model_id in model_ids
        ],
    }


@app.post(f"/{api_prefix}/v1/chat/completions" if api_prefix else "/v1/chat/completions")
async def send_conversation(request: Request, credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    req_token = credentials.credentials
    try:
        request_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "Invalid JSON body"})
    chat_service, res = await async_retry(process, request_data, req_token)
    try:
        if isinstance(res, types.AsyncGeneratorType):
            background = BackgroundTask(chat_service.close_client)
            return StreamingResponse(res, media_type="text/event-stream", background=background)
        background = BackgroundTask(chat_service.close_client)
        return JSONResponse(res, media_type="application/json", background=background)
    except HTTPException as e:
        await chat_service.close_client()
        if e.status_code == 500:
            logger.error(f"Server error, {str(e)}")
            raise HTTPException(status_code=500, detail="Server error")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        await chat_service.close_client()
        logger.error(f"Server error, {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@app.get(f"/{api_prefix}/v1/models" if api_prefix else "/v1/models")
async def list_models(credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authorization header is missing")
    return _build_models_payload()


@app.get(f"/{api_prefix}/tokens" if api_prefix else "/tokens", response_class=HTMLResponse)
async def upload_html(request: Request, admin_key: str | None = None):
    _verify_token_admin(request, admin_key)
    return templates.TemplateResponse(
        "tokens.html",
        {
            "request": request,
            "api_prefix": api_prefix,
            "tokens_count": _get_tokens_count(),
            "token_admin_enabled": bool(admin_api_key),
            "admin_key": admin_key or "",
        },
    )


@app.post(f"/{api_prefix}/tokens/upload" if api_prefix else "/tokens/upload")
async def upload_post(request: Request, text: str = Form(...), admin_key: str | None = Form(None)):
    _verify_token_admin(request, admin_key)
    lines = text.split("\n")
    valid_tokens = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    if not valid_tokens:
        raise HTTPException(status_code=400, detail="No valid tokens found in request.")

    existing_tokens = set(globals.token_list)
    new_tokens = [token for token in valid_tokens if token not in existing_tokens]

    if new_tokens:
        globals.token_list.extend(new_tokens)
        with open(globals.TOKENS_FILE, "a", encoding="utf-8") as f:
            for token in new_tokens:
                f.write(token + "\n")

    logger.info(f"Token count: {len(globals.token_list)}, Error token count: {len(globals.error_token_list)}")
    return {"status": "success", "tokens_count": _get_tokens_count(), "added_count": len(new_tokens)}


@app.post(f"/{api_prefix}/tokens/clear" if api_prefix else "/tokens/clear")
async def clear_tokens(request: Request, admin_key: str | None = Form(None)):
    _verify_token_admin(request, admin_key)
    globals.token_list.clear()
    globals.error_token_list.clear()
    with open(globals.TOKENS_FILE, "w", encoding="utf-8") as f:
        f.write("")
    logger.info(f"Token count: {len(globals.token_list)}, Error token count: {len(globals.error_token_list)}")
    return {"status": "success", "tokens_count": _get_tokens_count()}


@app.post(f"/{api_prefix}/tokens/error" if api_prefix else "/tokens/error")
async def error_tokens(request: Request, admin_key: str | None = Form(None)):
    _verify_token_admin(request, admin_key)
    error_tokens_list = list(set(globals.error_token_list))
    return {"status": "success", "error_tokens": error_tokens_list}


@app.get(f"/{api_prefix}/tokens/add/{{token}}" if api_prefix else "/tokens/add/{token}")
async def add_token(token: str, request: Request, admin_key: str | None = None):
    _verify_token_admin(request, admin_key)
    token = token.strip()
    if token and not token.startswith("#") and token not in set(globals.token_list):
        globals.token_list.append(token)
        with open(globals.TOKENS_FILE, "a", encoding="utf-8") as f:
            f.write(token + "\n")
    logger.info(f"Token count: {len(globals.token_list)}, Error token count: {len(globals.error_token_list)}")
    return {"status": "success", "tokens_count": _get_tokens_count()}


@app.post(f"/{api_prefix}/seed_tokens/clear" if api_prefix else "/seed_tokens/clear")
async def clear_seed_tokens(request: Request, admin_key: str | None = Form(None)):
    _verify_token_admin(request, admin_key)
    globals.seed_map.clear()
    globals.conversation_map.clear()
    with open(globals.SEED_MAP_FILE, "w", encoding="utf-8") as f:
        f.write("{}")
    with open(globals.CONVERSATION_MAP_FILE, "w", encoding="utf-8") as f:
        f.write("{}")
    logger.info(f"Seed token count: {len(globals.seed_map)}")
    return {"status": "success", "seed_tokens_count": len(globals.seed_map)}
