# flask-simple-board

# 프로젝트 실행 방법

https://github.com/DoTTak/flask-simple-board/commits/main/ 커밋 기준으로 `docker` 를 이용해서 `flask-simple-board` 프로젝트를 실행하는 방법에 대한 설명이다.

## 1. git clone

```bash
git clone https://github.com/DoTTak/flask-simple-board.git
cd flask-simple-board
```

![스크린샷 2024-06-02 오전 5.58.06.png](./images/ca88b31c-5a03-460c-aa7b-40afd76be1e5.png)

## 2. MySQL 설치 및 구동

`/db/data` 경로에 이미 테스트 데이터가 셋팅되어 있다.

```bash
docker run --name mysql -e MYSQL_ROOT_PASSWORD='!root1234' -e MYSQL_DATABASE='flask-simple-board' -e TZ='Asia/Seoul' -e LC_ALL='C.UTF-8' -p 3306:3306 -d -v ./db/data:/var/lib/mysql mysql:latest
```

![스크린샷 2024-06-02 오전 5.59.42.png](./images/eb729b91-d5a5-47d3-8313-415129d63e32.png)

## 3. flask-sample-board 이미지 빌드

```bash
docker build --tag dottak/flask-simple-board:0.1 .
```

![스크린샷 2024-06-02 오전 6.00.45.png](./images/51caa1ba-e5b1-49cc-8c81-0ebdeba9028c.png)

## 4. flask-sample-board 이미지 실행

```bash
docker run -p 80:80 --name flask -v ./backend:/app dottak/flask-simple-board:0.1
```

![스크린샷 2024-06-02 오전 6.02.59.png](./images/0848af99-d44a-4186-96ea-3572bca0bcf7.png)

## 5. 서버 접속

브라우저를 통해 [`http://127.0.0.1`](http://127.0.0.1:80) 으로 접속하면 아래의 웹 페이지와 접속 로그가 출력된다.

![스크린샷 2024-06-02 오전 6.04.13.png](./images/5aed2ee6-a9f2-4c13-8164-7ecf735f8bcd.png)

![스크린샷 2024-06-02 오전 6.04.32.png](./images/de78a039-e91a-48da-a6f6-ce28d6d38732.png)
