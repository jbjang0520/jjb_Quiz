import redis
from typing import Any, Dict, Optional, Union
import json
import pickle
from fastapi.responses import Response, JSONResponse

from app.core.config import settings

# 전역 Redis 클라이언트 인스턴스
_redis_client = None


def setup_cache() -> redis.Redis:
    """
    Redis 클라이언트 연결을 초기화합니다.
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,  # Redis 호스트
            port=settings.REDIS_PORT,  # Redis 포트
            db=0,  # 사용할 데이터베이스 인덱스
            decode_responses=False,  # pickle 호환을 위해 바이트로 반환
            socket_timeout=5,  # Redis 연결 시간 초과 설정
        )
    
    return _redis_client


def get_cache() -> "RedisCache":
    """
    Redis 캐시 인스턴스를 반환합니다.
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = setup_cache()  # Redis 클라이언트를 설정합니다.
    
    return RedisCache(_redis_client)


class RedisCache:
    """
    다양한 데이터와 응답을 처리할 수 있는 Redis 캐시 래퍼 클래스입니다.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값을 가져옵니다. 복잡한 객체의 역직렬화도 처리합니다.
        """
        try:
            data = self.redis.get(key)
            if data is None:
                return None  # 값이 없으면 None을 반환
            
            # Response 객체로 역직렬화 시도
            try:
                response_data = pickle.loads(data)
                if isinstance(response_data, dict) and "response_type" in response_data:
                    if response_data["response_type"] == "json":
                        return JSONResponse(
                            content=response_data["content"],
                            status_code=response_data["status_code"],
                            headers=response_data["headers"]
                        )
                    # 필요한 다른 응답 타입 추가 가능
                return response_data
            except:
                # 기본적인 문자열 또는 JSON 처리로 포맷을 되돌림
                try:
                    return json.loads(data)
                except:
                    return data.decode("utf-8") if isinstance(data, bytes) else data
        except Exception as e:
            print(f"Cache get error: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """
        캐시에 값을 저장합니다. 복잡한 객체를 직렬화하여 저장하며, 만료 시간도 설정합니다.
        """
        try:
            # FastAPI Response 객체 처리
            if isinstance(value, Response):
                # JSONResponse에 대해서는 본문(content)을 저장
                if isinstance(value, JSONResponse):
                    cache_data = {
                        "response_type": "json",
                        "content": value.body.decode("utf-8") if isinstance(value.body, bytes) else value.body,
                        "status_code": value.status_code,
                        "headers": dict(value.headers)
                    }
                    serialized = pickle.dumps(cache_data)
                else:
                    # 다른 Response 타입은 전체 객체를 직렬화
                    serialized = pickle.dumps(value)
            else:
                # 일반 Python 객체 처리
                if isinstance(value, (dict, list, tuple, bool, int, float, str)):
                    serialized = json.dumps(value).encode("utf-8")
                else:
                    serialized = pickle.dumps(value)
            
            self.redis.set(key, serialized, ex=expire)  # 캐시에서 설정할 만료 시간과 함께 저장
            return True
        except Exception as e:
            print(f"Cache set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        캐시에서 특정 키를 삭제합니다.
        """
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {str(e)}")
            return False
    
    def clear_prefix(self, prefix: str) -> int:
        """
        특정 접두사를 가진 모든 키를 삭제합니다.
        삭제된 키의 개수를 반환합니다.
        """
        try:
            keys = self.redis.keys(f"{prefix}*")
            if keys:
                return self.redis.delete(*keys)  # 해당 키들을 한번에 삭제
            return 0
        except Exception as e:
            print(f"Cache clear_prefix error: {str(e)}")
            return 0
    
    def clear_all(self) -> bool:
        """
        전체 캐시를 삭제합니다 (주의해서 사용하세요).
        """
        try:
            self.redis.flushdb()  # 모든 데이터베이스의 키를 삭제
            return True
        except Exception as e:
            print(f"Cache clear_all error: {str(e)}")
            return False