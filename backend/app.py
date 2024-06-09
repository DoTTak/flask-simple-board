import os
import re
import time
import threading
import datetime
from random import randint
import config
import pymysql
from flask import Flask, redirect, request, render_template, session, url_for, make_response, send_file
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    get_jwt_identity, get_jwt, jwt_required,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    JWTManager, exceptions, decode_token, 
)
from jwt.exceptions import ExpiredSignatureError
from apps.posts import posts_app
from apps.users import users_app

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.register_blueprint(posts_app, url_prefix='/posts')
app.register_blueprint(users_app, url_prefix='/profile')

app.config['MAIL_SERVER'] = config.MAIL_SERVER
app.config['MAIL_PORT'] = config.MAIL_PORT
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = config.MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = config.MAIL_USE_SSL
mail = Mail(app)

app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['BCRYPT_LEVEL'] = 10
bcrypt = Bcrypt(app)

app.config["JWT_SECRET_KEY"] = config.SECRET_KEY
app.config["JWT_TOKEN_LOCATION"] = ['cookies'] # 웹 브라우저 사용으로 쿠키 키용
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=1) # Access Token 만료 1시간 지정
jwt = JWTManager(app)

# 만료 시간(ext) 이전에 토큰을 만료시킬 경우(로그아웃, 토큰 재요청)
# 아래에 jti(토큰 고유 식별자)를 추가하여 차단할 수 있다.
black_list = {}

# 인증 실패 시 로그인 페이지로 이동
@app.errorhandler(exceptions.NoAuthorizationError)
def handle_auth_error(e):
    response = {"status": "warning", "msg": "로그인이 필요한 페이지 입니다.", "redirect_url": "/login"}
    return render_template('pages/login.html', response=response)

# 중복된 토큰 사용 시 로그인 페이지로 이동
# NOTE: 일반적인 경우 중복된 토큰을 사용할 수 없음 -> 토큰 삭제 
#        - ex) 만료되기 이전에 로그아웃을 한 뒤, 해당 토큰을 또 재사용한 경우
@app.errorhandler(exceptions.RevokedTokenError)
def handle_auth_error(e):
    response = {"status": "warning", "msg": "비정상적인 요청을 하셨습니다.\\n로그인을 다시 해주세요.", "redirect_url": "/login"}
    resp = make_response(render_template('pages/login.html', response=response))
    unset_jwt_cookies(resp)
    return resp

# Refresh Token 만료 시 로그인 페이지로 이동
# NOTE: Access Token은 매 라우팅 요청 시마다 갱신됨 단, @jwt_rquired() 데코레이터가 있는 경우만
@app.errorhandler(ExpiredSignatureError)
def handle_token_expired(e):
    response = {"status": "warning", "msg": "로그인 세션 만료\\n로그인을 다시 해주세요.", "redirect_url": "/login"}
    resp = make_response(render_template('pages/login.html', response=response))
    unset_jwt_cookies(resp)
    return resp

# 토큰 재발행
# ref. https://flask-jwt-extended.readthedocs.io/en/stable/refreshing_tokens.html#implicit-refreshing-with-cookies
@app.after_request
def refresh_expiring_jwts(response):
    try:
        jwt_info = get_jwt()
        exp_timestamp = jwt_info["exp"]
        now = datetime.datetime.now(datetime.timezone.utc)
        # Access Token 만료시간이 1시간인데, 30분 내에 재 요청 올 경우 Access Token 재발행
        target_timestamp = datetime.datetime.timestamp(now + datetime.timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            additional_claims = {
                "user_id": jwt_info['user_id'], 
                "email": jwt_info['email'], 
                "name": jwt_info['name']
            }
            access_token = create_access_token(identity=get_jwt_identity(), additional_claims=additional_claims)
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response

@app.route('/download/<int:upload_id>')
@jwt_required()
def download(upload_id):

    # 데이터베이스 연결자 및 커서 생성
    conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql=f"""
    SELECT * FROM uploads WHERE id=%s
    """
    cursor.execute(sql, (upload_id))
    file_info = cursor.fetchone()

    # 자신의 파일인지 검증
    sql=f"""
    SELECT user_id, password FROM posts WHERE id = %s
    """
    cursor.execute(sql, (file_info['post_id']))
    post_info = cursor.fetchone()
    cursor.close()
    conn.close()

    # 비밀번호 걸린 게시글의 파일 여부 확인
    if post_info['password']:
        # 세션이 없거나자신의 파일도 아닌 경우 리다이렉트
        if not session.get(f"view_{file_info['post_id']}", None):
            if post_info['user_id'] != get_jwt_identity():
                return redirect("/")

    try:
        # 경로 문제(맨 앞 디렉터리 경로 제외)
        file_path = file_info['file_path']
        return_file = send_file(file_path, as_attachment=True, download_name=file_info['file_name'])
    except:
        file_path = file_path[file_path.find("/")+1:]
        return_file = send_file(file_path, as_attachment=True, download_name=file_info['file_name'])
    finally:
        return return_file

@app.route('/file_delete/<int:file_id>', methods=['POST'])
@jwt_required()
def file_delete(file_id):

    # 데이터베이스 연결자 및 커서 생성
    conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 파일 검색 질의(본인 파일 확인)
    sql=f"""
    SELECT 
        uploads.id as file_id,
        file_path,
        posts.user_id
    FROM 
        uploads 
    INNER JOIN 
        posts 
    ON 
        posts.id = post_id 
    WHERE 
        uploads.id = %s AND posts.user_id = %s
    """
    cursor.execute(sql, (file_id, get_jwt_identity()))
    file_info = cursor.fetchone()
    
    # 파일 삭제 처리
    if file_info:
        os.remove(file_info['file_path'])
        sql = f"""
        DELETE FROM uploads WHERE id = %s
        """
        cursor.execute(sql, (file_info['file_id']))
        conn.commit()
    
    cursor.close()
    conn.close()

    return {"status": "success", "msg": "성공적으로 삭제되었습니다."}


@app.route('/')
@jwt_required()
def index():
    # Document Root 접속 시 posts로 이동
    return redirect('/posts')

@app.route('/logout', methods=['GET'])
def logout():
    response = {"status": "success", "msg": "로그아웃", "redirect_url": "/login"}
    resp = make_response(render_template('pages/login.html', response=response))
    unset_jwt_cookies(resp)
    return resp
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("pages/login.html")
    else:
        try:
            email = request.form['form-email']
            password = request.form['form-password']
        except:
            return render_template("pages/login.html", response={"status": "error", "msg": "아이디 또는 비밀번호를 잘못 입력하셨습니다."})

        conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 이메일이 존재하는지 확인하기 위한 SQL 구문
        sql = f"""
        SELECT * FROM `users` WHERE email=%s
        """
        cursor.execute(sql, (email))
        user = cursor.fetchone()

        # 계정이 없는 경우        
        if not user or not bcrypt.check_password_hash(user['password'], password):
            return render_template("pages/login.html", response={"status": "error", "msg": "아이디 또는 비밀번호를 잘못 입력하셨습니다."})

        # 클레임 설정
        additional_claims = {"user_id": user['id'], "email": user['email'], "name": user['name']}
        # Access Token 생성
        access_token = create_access_token(identity=user['id'], additional_claims=additional_claims)
        # Refresh Token 생성
        refresh_token = create_refresh_token(identity=user['id'], additional_claims=additional_claims)
        
        # Token 쿠키 지정
        resp = make_response(redirect(url_for('index')))
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)

        return resp

@app.route('/register', methods=['GET', 'POST'])
def register():
    input_data = {"input_data": {"email": "", "email_auth": "", "token": "", "name": "", "school": ""}}
    if request.method == 'GET':
        # 세션 초기화
        session.clear()
        response = {"data": input_data}
        return render_template("pages/register.html", response=response)
    else:
        email = request.form.get("form-email", "").strip()
        email_auth = request.form.get("form-email-auth", "").strip()
        token = request.form.get("form-email-token", "").strip()
        password = request.form.get("form-password", "").strip()
        password2 = request.form.get("form-password2", "").strip()
        name = request.form.get("form-name", "").strip()
        school = request.form.get("form-school", "").strip()

        # 이메일 인증번호가 다를 경우 인증번호 초기화
        if email_auth != session.get(f"otp_{email}", None):
            session.clear()
            return render_template("pages/register.html", response={"status": "error", "msg": "인증번호가 다릅니다.\\n다시 시도해주세요.", "redirect_url": "/register", "data": input_data})

        # 클라이언트에 새로고침 발생 시 데이터를 다시 입력하기 위함
        input_data['input_data'] = {
            "email": email,
            "email_auth": email_auth,
            "token": token,
            # "password": password, # 비밀번호는 제외
            # "password2": password2, # 비밀번호는 제외
            "name": name,
            "school": school
        }
        if not email or not email_auth or not token or not password or not password2 or not name or not school:
            return render_template("pages/register.html", response={"status": "error", "msg": "입력값을 확인해주세요.", "data": input_data})

        # 패스워드 확인        
        if password != password2:
            return render_template("pages/register.html", response={"status": "error", "msg": "비밀번호가 같지 않습니다.\\n다시 확인해주세요.", "data": input_data})
        
        # 길이 검사
        if len(password) < 8:
            return render_template("pages/register.html", response={"status": "error", "msg": "패스워드가 너무 짧습니다.(8자 이상))", "data": input_data})
        if len(name) < 4:
            return render_template("pages/register.html", response={"status": "error", "msg": "이름이 너무 짧습니다.(4자 이상))", "data": input_data})

        
        # 이메일 중복검사, 이메일 인증 요청, 이메일 인증 번호 입력 모두 완료해야
        # 회원가입 실시
        if session.get("is_email_check", None) and session.get("is_send_email", None) and session.get("is_email_auth", None):
            # 이메일 세션 검증 완료 했으니 초기화
            session.clear()

            conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # 이메일이 존재하는지 확인하기 위한 SQL 구문
            sql = f"""
            SELECT `email` FROM `users` WHERE email=%s
            """
            cursor.execute(sql, (email))
            is_exists_email = cursor.fetchone()
            
            # 회원가입 insert전, 한번 더 이메일 중복 여부 검사
            if is_exists_email:
                cursor.close()
                conn.close()

                status = "error"
                msg = "이미 사용중인 이메일 주소입니다.\\n다시 시도해주세요."
                return render_template("pages/register.html", response={"status": "error", "msg": "비밀번호가 같지 않습니다.\\n다시 확인해주세요.", "data": input_data})
                
            else:
                sql = f"""
                INSERT INTO
                    `users` (`email`, `name`, `password`, `school`)
                VALUES
                    (%s, %s, %s, %s);
                """
                cursor.execute(sql, (email, name, bcrypt.generate_password_hash(password), school))
                conn.commit()
                return render_template("pages/register.html", response={"status": "success", "msg": f"{name}님, 회원가입을 축하드립니다", "redirect_url": "/login", "data": input_data})

            cursor.close()
            conn.close()

        else:
            return render_template("pages/register.html", response={"status": "error", "msg": "이메일 인증 과정이 비정상적입니다.\\n다시 시도해주세요.", "redirect_url": "/register", "data": input_data})



@app.route('/email_check', methods=['POST'])
def email_check():
    # 세션 활성화
    session['is_email_check'] = False # 이메일 중복 검사 여부
    session['is_send_email'] = False # 이메일 전송 여부
    session['is_email_auth'] = False # 이메일 인증 여부

    try:
        email = request.form.get("email", None)
        if not email:
            return {"status": "error", "msg": "입력값을 확인해주세요."}
    except:
        return {"status": "error", "msg": "입력값을 확인해주세요."}

    # 이메일 유효성 검사
    email_validator = re.compile('^[a-zA-Z0-9+-\_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    if not email_validator.match(email):
        return {"status": "error", "msg": "이메일 형식 아닙니다."}
    
    # 데이터베이스 연결자 및 커서 생성
    conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 이메일이 존재하는지 확인하기 위한 SQL 구문
    sql = f"""
    SELECT `email` FROM `users` WHERE email=%s
    """
    cursor.execute(sql, (email))
    is_exists_email = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not is_exists_email:
        data = {"result": True}
        msg = "사용 가능한 이메일 주소입니다.\n사용하시겠습니까?"

        session['email'] = email
        session['is_email_check'] = True
    else:
        data = {"result": False}
        msg = "이미 사용중인 이메일 주소입니다."

    return {"status": "success", "msg": msg, "redirect_url": "", "data": data}

@app.route('/email_verify', methods=['POST'])
def email_verify():
    try:
        email = request.form.get("email", None)
        if not email:
            return {"status": "error", "msg": "입력값을 확인해주세요."}
    except:
        return {"status": "error", "msg": "입력값을 확인해주세요."}

    # 이메일 중복 확인 세션 검증
    if not session.get('is_email_check', None) or email != session.get('email', None):
        return {"status": "error", "msg": "이메일 중복확인을 다시 해주세요."}
    
    # 이메일 재전송 방지
    if session.get("is_send_email", None) and time.time() - float(session.get(f'time_{email}')) < 30:
        return {"status": "success", "msg": "이미 이메일을 전송했습니다.\n30초 후 다시 이용하세요.", "data": {"result": True}}

    # 인증메일 발송
    session[f'otp_{email}'] = str(randint(100000, 999999))  # 세션에 인증번호 저장
    session[f'time_{email}'] = str(time.time()) # 인증번호 생성 시간 저장
    session[f'is_send_email'] = True # 이메일 전송 여부
    msg = Message('[인증메일] 인증메일 발송', sender='flaskmailtest6@gmail.com', recipients=[email])
    msg.body = '인증 번호: '+ session[f'otp_{email}']
    mail.send(msg) # 메일 보내기
    return {"status": "success", "msg": "인증메일이 발송되었습니다.", "data": {"result": True, "token": session[f'time_{email}']}}

@app.route('/email_auth', methods=['POST'])
def email_auth():
    try:
        email = request.form.get("email", None)
        token = request.form.get("token", None)
        email_auth = request.form.get("email_auth", None)
        if not email or not email_auth or not token:
            return {"status": "error", "msg": "입력값을 확인해주세요."}
    except:
        return {"status": "error", "msg": "입력값을 확인해주세요."}

    # 이메일 중복 확인 세션 검증
    if not session.get('is_email_check', None) or email != session.get('email', None):
        return {"status": "error", "msg": "이메일 중복확인을 다시 해주세요."}
    
    # 이메일 인증 메시지 전송 단계 검증 및 세션 데이터 검증
    if not session.get('is_send_email') or session.get(f'time_{email}') != token:
        session.clear()
        return {"status": "error", "msg": "이메일 인증 단계에 문제가 발생됐습니다.\n처음부터 다시 시도해주세요.", "redirect_url": "/register"}

    # 이메일 인증번호 만료
    if time.time() - float(session.get(f'time_{email}')) > 300:
        session.clear()
        return {"status": "error", "msg": "이메일 인증 시간이 만료되었습니다.\n처음부터 다시 시도해주세요.", "redirect_url": "/register"}

    # 인증메일 검증
    if session.get(f'otp_{email}', None) == email_auth:
        session['is_email_auth'] = True
        return {"status": "success", "msg": "메일 인증을 완료했습니다.", "data": {"result": True}}
    else:
        return {"status": "success", "msg": "잘못된 인증번호 입니다.", "data": {"result": False}}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=bool(config.FLASK_DEBUG))