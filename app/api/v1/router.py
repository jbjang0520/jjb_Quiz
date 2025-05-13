from fastapi import APIRouter

from app.api.v1.endpoints import users, auth, quizzes, questions, submissions

api_router = APIRouter()

# 인증 관련 라우트
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# 사용자 관련 라우트
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 퀴즈 관련 라우트
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])

# 문제 관련 라우트
api_router.include_router(questions.router, prefix="/quizzes", tags=["questions"])

# 제출 관련 라우트
api_router.include_router(submissions.router, prefix="/quizzes", tags=["submissions"])