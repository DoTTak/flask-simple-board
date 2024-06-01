# python 3.8.10 이미지를 베이스 이미지로 지정
FROM python:3.8.10

# 작업 디렉터리 지정
WORKDIR /app

# flask 프로젝트 폴더(backend) 작업 디렉터리에 복사
COPY ./backend /app

# 패키지 설치
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# app.py(flask 앱) 실행
CMD ["python", "app.py"]