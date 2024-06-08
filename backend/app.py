import re
import time
from random import randint
import config
import pymysql
from flask import Flask, redirect, request, render_template, session
from flask_mail import Mail, Message
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

@app.route('/')
def index():
    return redirect('/posts')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("pages/login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        # 세션 초기화
        session.clear()
        return render_template("pages/register.html")

@app.route('/email_check', methods=['POST'])
def email_check():
    # 세션 활성화
    session['is_email_check'] = False

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
    session[f'is_send_email'] = True # 이메일 전송 
    msg = Message('[인증메일] 인증메일 발송', sender='flaskmailtest6@gmail.com', recipients=[email])
    msg.body = '인증 번호: '+ session[f'otp_{email}']
    mail.send(msg) # 메일 보내기
    return {"status": "success", "msg": "인증메일이 발송되었습니다.", "data": {"result": True}}


app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=bool(config.FLASK_DEBUG))