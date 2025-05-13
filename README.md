# Quiz System

퀴즈 시스템은 FastAPI 프레임워크와 PostgreSQL 데이터베이스를 사용하여 구현된 RESTful API 애플리케이션입니다. 이 시스템은 관리자가 퀴즈를 생성하고 사용자가 퀴즈를 응시할 수 있는 기능을 제공합니다.

## 기능

### 관리자
- 퀴즈 생성, 수정, 삭제
- 문제 생성, 수정, 삭제
- 선택지 관리
- 모든 퀴즈 조회
- 사용자 제출 결과 조회

### 사용자
- 퀴즈 목록 조회
- 퀴즈 응시
- 문제 풀이 및 답안 제출
- 결과 확인

## 기술 스택

- **프레임워크**: FastAPI
- **데이터베이스**: PostgreSQL
- **ORM**: SQLAlchemy
- **인증**: JWT (JSON Web Tokens)
- **의존성 관리**: Poetry
- **캐싱**: Redis
- **컨테이너화**: Docker & Docker Compose

## 설치 및 실행

### 필요 조건

- Docker와 Docker Compose가 설치되어 있어야 합니다.
- Poetry 설치 (로컬 개발 시)

### Docker Compose로 실행하기

1. 프로젝트를 클론합니다:
   ```bash
   git clone https://github.com/yourusername/quiz-system.git
   cd quiz-system
   ```

2. 환경 변수 파일을 생성합니다:
   ```bash
   cp .env.example .env
   ```

3. .env 파일을 원하는 설정으로 수정합니다.

4. Docker Compose로 애플리케이션을 실행합니다:
   ```bash
   docker-compose up -d
   ```

5. API 문서는 다음 URL에서 확인할 수 있습니다:
   - Swagger UI: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

### 로컬에서 개발 실행

1. Poetry를 사용하여 의존성을 설치합니다:
   ```bash
   poetry install
   ```

2. PostgreSQL 및 Redis를 실행합니다:
   ```bash
   docker-compose up -d db redis
   ```

3. 환경 변수를 설정합니다:
   ```bash
   cp .env.example .env
   ```

4. 데이터베이스 마이그레이션을 실행합니다:

   PostgreSQL 데이터베이스를 생성합니다 (필요시):
   ```bash
   sudo -u postgres psql
   CREATE DATABASE quiz_db;
   \q
   ```

   Alembic 마이그레이션을 실행합니다:
   ```bash
   poetry run alembic upgrade head
   ```

## 시드 데이터 삽입

기본 퀴즈 데이터를 추가하려면 아래 명령어를 실행하세요.

### Docker 환경에서 실행할 경우

```bash
docker compose exec app poetry run python app/seed/seed_from_json.py
```

### 로컬 개발 환경에서 실행할 경우

```bash
poetry run python -m app.seed.seed_from_json
```

시드 데이터는 `app/seed/data.json` 파일을 기준으로 삽입됩니다. 퀴즈와 문제 데이터를 수정하고자 한다면 해당 JSON 파일을 편집하세요.

## 프로젝트 구조

```
fastapi-quiz-system/
├── pyproject.toml         # Poetry 구성 파일
├── README.md              # 프로젝트 설명
├── alembic/               # 데이터베이스 마이그레이션
├── app/
│   ├── __init__.py
│   ├── main.py            # 애플리케이션 진입점
│   ├── core/              # 핵심 설정 및 유틸리티
│   ├── api/               # API 엔드포인트
│   ├── models/            # 데이터베이스 모델
│   ├── schemas/           # Pydantic 스키마
│   ├── crud/              # CRUD 작업
│   ├── services/          # 비즈니스 로직
│   └── db/                # 데이터베이스 설정
```

## API 엔드포인트

### 인증
- `POST /api/v1/auth/login` - 사용자 로그인
- `POST /api/v1/auth/signup` - 새 사용자 등록

### 사용자
- `GET /api/v1/users/` - 모든 사용자 목록 (관리자용)
- `GET /api/v1/users/me` - 현재 사용자 정보

### 퀴즈
- `GET /api/v1/quizzes/` - 퀴즈 목록
- `POST /api/v1/quizzes/` - 퀴즈 생성 (관리자용)
- `GET /api/v1/quizzes/{quiz_id}` - 퀴즈 상세 정보
- `PUT /api/v1/quizzes/{quiz_id}` - 퀴즈 수정 (관리자용)
- `DELETE /api/v1/quizzes/{quiz_id}` - 퀴즈 삭제 (관리자용)

### 문제
- `GET /api/v1/quizzes/{quiz_id}/questions/` - 문제 목록
- `POST /api/v1/quizzes/{quiz_id}/questions/` - 문제 생성 (관리자용)
- `PUT /api/v1/quizzes/{quiz_id}/questions/{question_id}` - 문제 수정 (관리자용)
- `DELETE /api/v1/quizzes/{quiz_id}/questions/{question_id}` - 문제 삭제 (관리자용)

### 제출
- `POST /api/v1/quizzes/{quiz_id}/submissions/` - 퀴즈 응시 시작
- `PUT /api/v1/quizzes/{quiz_id}/submissions/{submission_id}/answer` - 답안 제출
- `PUT /api/v1/quizzes/{quiz_id}/submissions/{submission_id}/submit` - 퀴즈 완료 제출
- `GET /api/v1/quizzes/{quiz_id}/submissions/{submission_id}/result` - 결과 조회



.env 파일의 내용을 아래와같이 생성해주세요

# PostgreSQL
# 로컬 개발에서는 localhost, 도커에서는 db를 사용할 수 있도록 환경 변수 추가
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_DB=quiz_db

# PgAdmin
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECRET_KEY=my-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=720 # 추후 60 정도로 수정
ALGORITHM=HS256

# Application
PROJECT_NAME=Quiz System
API_V1_STR=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost", "http://localhost:8080", "http://localhost:3000"]

# First admin user
FIRST_ADMIN_EMAIL=admin@example.com
FIRST_ADMIN_PASSWORD=admin

# 개발 환경 구분을 위한 환경 변수
IS_DOCKER=false