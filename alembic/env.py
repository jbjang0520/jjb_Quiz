import sys
import os
from logging.config import fileConfig
from pathlib import Path
from sqlalchemy import engine_from_config, pool
from alembic import context

# sys.path에 app 디렉토리의 상위 경로를 추가하여 core 모듈을 찾을 수 있도록 설정
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Settings.py에서 환경설정 불러오기
from app.core.config import settings  # app/core/config.py 불러오기

# Alembic Config 객체
config = context.config

# alembic.ini에서 로깅 설정 불러오기
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 여기서 target_metadata는 Base.metadata 객체를 참조해야 함
# app.db.session에서 Base와 engine을 가져옵니다.
from app.db.session import Base  # session.py에서 Base 가져오기
target_metadata = Base.metadata

# 환경설정에서 DB 접속 정보 불러오기
POSTGRES_USER = settings.POSTGRES_USER
POSTGRES_PASSWORD = settings.POSTGRES_PASSWORD
POSTGRES_DB = settings.POSTGRES_DB
POSTGRES_SERVER = settings.POSTGRES_SERVER  # env 파일이나 환경 변수에서 가져옴

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:5432/{POSTGRES_DB}"

# Alembic 설정에 DB URL 주입
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline():
    """Offline 모드에서 마이그레이션 실행 (DB 연결 없이 SQL만 생성)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Online 모드에서 마이그레이션 실행 (DB 연결 필요)"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# 실행 모드에 따라 적절한 방식 호출
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()