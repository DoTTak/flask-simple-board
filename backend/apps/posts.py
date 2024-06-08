import os
import math
import pymysql
import config
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, Blueprint
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

PAGE_POST_LIMIT = 10 # 페이지 당 보여질 게시글의 갯수
PAGE_GROUP_LIMIT = 5 # 페이지 그룹 당 페이지 갯수, ex. 4인 경우 << 1,2,3,4 >>

posts_app = Blueprint('posts', __name__, template_folder='templates')

@posts_app.route('/', methods=['GET'])
@jwt_required()
def index():
    try:
        page = int(request.args.get('page', 1)) # 페이지 번호
        # 음수로 전달된 값은 무조건 1로 초기화
        if page <= 0:
            page = 1
    except:
        # 페이지 번호는 에러 발생 시 무조건 1로 초기화
        page = 1
    search = request.args.get('search', "") # 검색어
    search_type = request.args.get('type', "search_all") # 검색타입(search_all, search_title, search_content)
    
    # LIMIT 절은 0부터 시작, ex. LIMIT 0 10, LIMIT 10 10
    limit_start = (int(page) * PAGE_POST_LIMIT) - PAGE_POST_LIMIT # LIMIT 시작 번호

    # 데이터베이스 연결자 및 커서 생성
    conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 검색어 입력 시
    if search:
        # 검색 타입 설정
        if search_type == "search_title":
            sql_search_type = "title"
        elif search_type == "search_content":
            sql_search_type = "content"
        else:
            sql_search_type = "CONCAT(title, content)" # 전체 검색

        # 필요 입력 값: 검색어, LIMIT 시작 번호
        sql = f"""
        SELECT
            SQL_CALC_FOUND_ROWS
            * 
        FROM 
            posts 
        WHERE 
            REPLACE({sql_search_type}, ' ', '') 
        LIKE 
            CONCAT('%%', REPLACE(%s, ' ', ''), '%%')
        ORDER BY 
            id DESC 
        LIMIT 
            %s, {PAGE_POST_LIMIT};
        """

        cursor.execute(sql, (search, limit_start))

    else:
        # 필요 입력 값: LIMIT 시작 번호
        sql = f"""
        SELECT 
            SQL_CALC_FOUND_ROWS
            * 
        FROM 
            posts 
        ORDER BY 
            id DESC 
        LIMIT %s, {PAGE_POST_LIMIT};
        """
        
        cursor.execute(sql, (limit_start))
    
    # 조회된 게시글 목록
    posts = cursor.fetchall()
    
    # 질의한 쿼리의 전체 갯수 가져오기(limit을 제외한 전체 갯수)
    cursor.execute("SELECT FOUND_ROWS() as total_post_count;")
    total_post_count = cursor.fetchone()['total_post_count'] # 질의 결과의 전체 게시글 수

    # 데이터베이스, 커서 연결 해제
    cursor.close()
    conn.close()

    # 페이지네이션 처리
    total_post_count = total_post_count # 전체 컨텐츠 수
    total_page_count = math.ceil(total_post_count / PAGE_POST_LIMIT)
    page_group = math.ceil(page / PAGE_GROUP_LIMIT)
    page_group_start = ((page_group - 1) * PAGE_GROUP_LIMIT) + 1 # 페이지 그룹의 첫 번째 페이지 번호
    page_group_end = page_group * PAGE_GROUP_LIMIT  # 페이지 그룹의 마지막 페이지번호
    if page_group_end > total_page_count:
        page_group_end = total_page_count
    has_prev = page > PAGE_GROUP_LIMIT
    has_next = page_group_end != total_page_count

    pagination = {
        "current_page": page, # 현재 페이지 번호
        "total_page_count": total_page_count, # 전체 페이지 갯수
        "page_group_start": page_group_start, # 현재 페이지 그룹의 시작 번호
        "page_group_end": page_group_end, # 현재 페이지 그룹의 끝 번호
        "has_next": has_next, # 이전 버튼 여부, 이전 페이지 그룹으로 이동
        "has_prev": has_prev # 다음 버튼 여부, 다음 페이지 그룹으로 이동
    }
    return render_template("pages/index.html", posts=posts, search_info={"search": search, "type": search_type}, pagination=pagination)

@posts_app.route('/view/<int:post_id>', methods=['GET'])
def view(post_id):

    # 데이터베이스 연결자 및 커서 생성
    conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 게시글 검색 질의 수행
    sql = f"""
    SELECT 
        posts.id as post_id, title, content, name, posts.created_at
    FROM 
        posts 
    LEFT JOIN 
        users 
    ON 
        posts.user_id = users.id 
    WHERE posts.id=%s
    """
    cursor.execute(sql, post_id)
    
    # 조회된 게시글 정보 가져오기
    post = cursor.fetchone()
    
    # 업로드 파일 조회
    sql = f"""
    SELECT id as file_id, file_name FROM uploads WHERE post_id = %s
    """
    cursor.execute(sql, (post['post_id']))
    upload_list = cursor.fetchall()

    # 데이터베이스, 커서 연결 해제
    cursor.close()
    conn.close()

    response = {"status": "success", "msg": "", "redirect_url": ""}
    if not post:
        response = {"status": "error", "msg": "존재하지 않는 게시글 입니다.", "redirect_url": "/posts"}

    return render_template("pages/detail.html", post=post, upload_list=upload_list, response=response)

@posts_app.route('/write', methods=['GET', 'POST'])
@jwt_required()
def write():
    if request.method == 'GET':
        # GET 요청 시 글쓰기 페이지 렌더링
        return render_template("pages/write.html")
    else:
        try:
            title = request.form['form-title'].strip() # 제목, 좌우 공백 제거
            content = request.form['form-content'].strip() # 내용, 좌우 공백 제거
        except KeyError:
            # 요청 데이터가 없는 경우 처리
            return {"status": "error", "msg": "입력값을 확인해주세요."}
        
        # 유효성검사 작성
        if (title == "" or content == ""):
            return {"status": "error", "msg": "입력값을 확인해주세요."}

        # 데이터베이스 연결자 및 커서 생성
        conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 게시글 추가 질의
        sql = f"""
        INSERT INTO
            `posts` (`title`, `content`, `user_id`)
        VALUES
            (%s, %s, %s);
        """
        cursor.execute(sql, (title, content, get_jwt_identity()))
        conn.commit()

        # 방금 추가한 게시글 ID 가져오는 질의
        cursor.execute("SELECT LAST_INSERT_ID() as post_id;")
        post_id = cursor.fetchone()['post_id']

        # 파일 업로드 처리
        for upload_file in request.files.getlist('file_list'):
            file_name = secure_filename(upload_file.filename)
            # 파일명 중복 안되게끔 처리
            new_file_name = str(uuid.uuid4()) + "_" + file_name
            file_path = os.path.join(config.UPLOAD_DIR, new_file_name)
            file_size = upload_file.content_length
            upload_file.save(file_path)
            # 업로드 기록 남기기
            sql = f"""
            INSERT INTO
                `uploads` (`file_path`, `file_name`, `file_size`, `post_id`)
            VALUES
                (%s, %s, %s, %s);
            """
            cursor.execute(sql, (file_path, file_name, file_size, post_id))
            conn.commit()

        # 데이터베이스, 커서 연결 해제
        cursor.close()
        conn.close()

        # 응답값 작성
        response = {
            "status": "success", 
            "msg": "성공적으로 저장되었습니다.", 
            "redirect_url": f"/posts/view/{post_id}"
        }
        return response

@posts_app.route('/update/<int:post_id>', methods=['GET', 'POST'])
def update(post_id):
    
    # 데이터베이스 연결자 및 커서 생성
    conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 게시글 검색 질의 수행
    sql = f"""
    SELECT
        * 
    FROM 
        posts 
    WHERE
        id=%s
    """
    cursor.execute(sql, post_id)
    
    # 조회된 게시글 정보 가져오기
    post = cursor.fetchone()

    try:
        # 조회된 게시글이 없는 경우
        if not post:
            return render_template("pages/update.html", post=post, response={"status": "error", "msg": "존재하지 않는 게시글 입니다.", "redirect_url": "/posts"})

        # 조회된 게시글이 있는 경우
        if request.method == 'GET':
            # GET 요청 시 글수정 페이지 렌더링
            return render_template("pages/update.html", post=post)
        else:
            # POST 요청 시 글수정(UPDATE) 처리
            try:
                title = request.form['form-title'].strip() # 제목
                content = request.form['form-content'].strip() # 내용
            except:
                # 요청 데이터가 없는 경우 처리
                return render_template("pages/update.html", post=post, response={"status": "error", "msg": "입력값을 확인해주세요."})

            # 유효성검사 작성
            if (title == "" or content == ""):
                return render_template("pages/update.html", post=post, response={"status": "error", "msg": "입력값을 확인해주세요."})
            
            # 게시글 수정 질의
            sql = f"""
            UPDATE
                `posts`
            SET
                `title` = %s,
                `content` = %s
            WHERE
                `id` = %s
            """
            cursor.execute(sql, (title, content, post_id))
            conn.commit()

            # 응답값 작성
            response = {
                "status": "success", 
                "msg": "", 
                "redirect_url": f"/posts/view/{post_id}"
            }
    
            return render_template("pages/update.html", post=post, response=response)

    finally:
        # 데이터베이스, 커서 연결 해제
        cursor.close()
        conn.close()

@posts_app.route('/delete', methods=['POST'])
def delete():
    # 해당 라우팅은 글삭제 처리만을 작업하므로, 별도의 페이지는 없다.
    # 글 삭제는 Ajax방식으로 요청
    
    post_id = request.form.get('post_id', "").strip() # 제목

    if post_id == "":
        return {"status": "error", "msg": "존재하지 않는 게시글 입니다.", "redirect_url": "/posts"}

    # 데이터베이스 연결자 및 커서 생성
    conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password =config.DB_PASSWORD, db=config.DB_DATABSE, charset='utf8')
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 게시글 검색 질의 수행
    sql = f"""
    SELECT
        * 
    FROM 
        posts 
    WHERE
        id=%s
    """
    cursor.execute(sql, post_id)
    
    # 조회된 게시글 정보 가져오기
    post = cursor.fetchone()

    try:
        # 조회된 게시글이 없는 경우
        if not post:
            return {"status": "error", "msg": "존재하지 않는 게시글 입니다.", "redirect_url": "/posts"}

        # 게시글 삭제 질의
        sql = f"""
        DELETE FROM
            `posts`
        WHERE
            id = %s;
        """
        cursor.execute(sql, (post_id))
        conn.commit()

        # 응답값 작성
        response = {
            "status": "success", 
            "msg": "삭제되었습니다.", 
            "redirect_url": f"/posts" # 삭제는 다시 홈으로 이동
        }

        return response

    finally:
        # 데이터베이스, 커서 연결 해제
        cursor.close()
        conn.close()
