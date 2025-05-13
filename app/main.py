from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
import uvicorn
import time

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.init_db import init_db
from app.services.caching_service import setup_cache, get_cache
from app.api import deps

# FastAPI 앱 초기화
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Quiz System API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS 미들웨어 설정
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 캐시 미들웨어
class CacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # GET 요청이 아닌 경우 캐싱 건너뛰기
        if request.method != "GET":
            return await call_next(request)

        # 응답이 캐시에 있는지 확인
        cache_key = f"{request.url.path}?{request.url.query}"
        cache = get_cache()
        cached_response = cache.get(cache_key)

        if cached_response:
            return cached_response

        # 캐시에 없는 경우 요청 처리 및 응답 캐싱
        response = await call_next(request)

        # 성공적인 응답만 캐싱
        if 200 <= response.status_code < 300:
            cache.set(cache_key, response, expire=300)  # 5분 동안 캐싱

        return response

# 캐싱을 위한 미들웨어 추가
app.add_middleware(CacheMiddleware)

# API 라우터 초기화
app.include_router(api_router, prefix=settings.API_V1_STR)

# Rate limiting 미들웨어를 여기에 추가할 수 있습니다.

@app.on_event("startup")
async def startup_event():
    # 필요한 경우 데이터베이스 초기화
    db = SessionLocal()
    try:
        # 첫 번째 관리자 사용자로 데이터베이스 초기화
        init_db(db)
        # 캐시 연결 설정
        setup_cache()
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Quiz System API에 오신 것을 환영합니다. 문서는 /api/v1/docs에서 확인하세요."}

@app.get("/health")
def health_check():
    return {"status": "정상", "timestamp": time.time()}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)