import os
import uuid
import config
import pymysql
from werkzeug.utils import secure_filename
from flask import render_template, request, Blueprint, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity

users_app = Blueprint('users', __name__, template_folder='templates')

@users_app.route('/', methods=['GET'])
@jwt_required()
def profile():

    # 데이터베이스 연결자 및 커서 생성
    conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 나의 정보 조회
    sql=f"""
    SELECT * FROM users WHERE id = %s
    """
    cursor.execute(sql, (get_jwt_identity()))
    user = cursor.fetchone()

    return render_template("pages/profile.html", user=user)

@users_app.route('/view/<int:user_id>', methods=['GET'])
@jwt_required()
def profile_view(user_id):

    # 데이터베이스 연결자 및 커서 생성
    conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 나의 정보 조회
    sql=f"""
    SELECT * FROM users WHERE id = %s
    """
    cursor.execute(sql, (get_jwt_identity()))
    user = cursor.fetchone()
    
    # 타인 정보 조회
    sql=f"""
    SELECT * FROM users WHERE id = %s
    """
    cursor.execute(sql, (user_id))
    profile = cursor.fetchone()

    if not profile:
        response = {"status": "error", "msg": "존재하지 않는 사용자 입니다", "redirect_url": "/"} 
    else:
        response = {}

    return render_template("pages/profile_view.html", user=user, profile=profile, response=response)


@users_app.route('/edit', methods=['GET', 'POST'])
@jwt_required()
def profile_edit():
    if request.method == 'GET':

        # 데이터베이스 연결자 및 커서 생성
        conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 나의 정보 조회
        sql=f"""
        SELECT * FROM users WHERE id = %s
        """
        cursor.execute(sql, (get_jwt_identity()))
        user = cursor.fetchone()
        print(user)
        
        return render_template("pages/profile_edit.html", user=user)
    else:
        
        # 데이터베이스 연결자 및 커서 생성
        conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 나의 정보 조회
        sql=f"""
        SELECT * FROM users WHERE id = %s
        """
        cursor.execute(sql, (get_jwt_identity()))
        user = cursor.fetchone()
        
        try:
            profile_img = request.files.get('profile_img', "")
            name = request.form.get('form-name', "").strip()
            school = request.form.get('form-school', "").strip()
            text = request.form.get('form-text', "").strip()
        except:
            return {"status": "error", "msg": "입력값을 확인해주세요."}

        if not name or not school:
            return {"status": "error", "msg": "이름, 학교는 필수 입력 입니다."}

        if profile_img:

            if not ("." in profile_img.filename and \
                profile_img.filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS):
                return {"status": "error", "msg": "파일 확장자를 확인해주세요."}

            file_name = secure_filename(profile_img.filename)
            new_file_name = "profile" + "_" + str(user['id']) + "." + file_name.lower()
            file_path = os.path.join(config.UPLOAD_DIR, new_file_name)
            profile_img.save(file_path)

            # 유저 정보 수정 질의
            sql=f"""
            UPDATE 
                `users`
            SET
                `name` = %s,
                `school` = %s,
                `introduce` = %s,
                `profile_name` = %s,
                `profile_path` = %s
            WHERE
                `id`=%s
            """
            cursor.execute(sql, (name, school, text, new_file_name, file_path, user['id']))
            
        else:
            # 유저 정보 수정 질의
            sql=f"""
            UPDATE 
                `users`
            SET
                `name` = %s,
                `school` = %s,
                `introduce` = %s
            WHERE
                `id`=%s
            """
            cursor.execute(sql, (name, school, text, get_jwt_identity()))
            
        conn.commit()

        cursor.close()
        conn.close()
        return {"status": "success", "msg": "수정되었습니다.", "redirect_url": "/profile"}

@users_app.route('/image_serve/<filename>')
def image_serve(filename):
    return send_from_directory('uploads', filename)