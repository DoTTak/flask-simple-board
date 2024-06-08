import config
import pymysql
import re
from flask import Flask, redirect, request, render_template, session
from apps.posts import posts_app
from apps.users import users_app

app = Flask(__name__)
app.register_blueprint(posts_app, url_prefix='/posts')
app.register_blueprint(users_app, url_prefix='/profile')

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
        return render_template("pages/register.html")

@app.route('/email_check', methods=['POST'])
def email_check():
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
    else:
        data = {"result": False}
        msg = "이미 사용중인 이메일 주소입니다."

    return {"status": "success", "msg": msg, "redirect_url": "", "data": data}


app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=bool(config.FLASK_DEBUG))