# 베이스 이미지로 Python 3.13.3 버전을 사용
FROM python:3.13.3

# 작업 디렉터리를 /app으로 설정
WORKDIR /app

# 깃허브에서 직접 클론해서 빌드하려면 아래처럼 url 입력
# (점(.)을 붙이면 /app에 바로 복제됨)
# requirements.txt 파일에 명시된 패키지를 설치
RUN git clone  -b movie-for-cloud https://github.com/lillykim/movie.git . && \
    pip install --no-cache-dir -r requirements.txt

# 컨테이너가 시작될 때 실행할 명령어를 지정
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD uvicorn main:app --host "0.0.0.0" --port 8000