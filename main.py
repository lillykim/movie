from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.users import user_router
from routes.movies import movie_router
from routes.admin import admin_router
from database.connection import conn
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션이 시작될 때 실행 코드
    print("애플리케이션 시작")
    conn()

    yield
    # 애플리케이션이 종료될 때 실행 코드
    print("애플리케이션 종료")


app = FastAPI(lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware
# 환경변수에서 CORS 허용 도메인 읽기 (여러 개일 경우 ,로 구분)
origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173","http://my-project-bucket-46.s3-website.ap-northeast-2.amazonaws.com","https://my-pic-saving-bucket.s3.ap-northeast-2.amazonaws.com"],
    allow_origins=origins, # 수정: 환경변수 사용
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/users")
app.include_router(movie_router, prefix="/movies")
app.include_router(admin_router, prefix="/admin")

@app.get("/")
def root():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)