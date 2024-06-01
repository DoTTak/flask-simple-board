import math
import pymysql
from flask import Flask, render_template, request
from tests.test_data import test_posts


PAGE_POST_LIMIT = 10 # 페이지 당 보여질 게시글의 갯수
PAGE_GROUP_LIMIT = 5 # 페이지 그룹 당 페이지 갯수, ex. 4인 경우 << 1,2,3,4 >>

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    try:
        page = int(request.args.get('page', 1)) # 페이지 번호
        # 음수로 전달된 값은 무조건 1로 초기화
        if page <= 0:
            page = 1
    except:
        # 페이지 번호는 에러 발생 시 무조건 1로 초기화
        page = 1
    search = request.args.get('search') # 검색어
    search_type = request.args.get('type', "search_all") # 검색타입(search_all, search_title, search_content)
    
    # LIMIT 절은 0부터 시작, ex. LIMIT 0 10, LIMIT 10 10
    limit_start = (int(page) * PAGE_POST_LIMIT) - PAGE_POST_LIMIT # LIMIT 시작 번호

    # 데이터베이스 연결자 및 커서 생성
    conn = pymysql.connect(host="localhost", user="root", password ='!root1234', db='flask-simple-board', charset='utf8')
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
    
    return render_template("pages/index.html", posts=posts, pagination=pagination)

@app.route('/view/<int:post_id>', methods=['GET'])
def view(post_id):
    return render_template("pages/detail.html")

@app.route('/write', methods=['GET', 'POST'])
def write():
    if request.method == 'GET':
        # GET 요청 시 글쓰기 페이지 렌더링
        return render_template("pages/write.html")
    else:
        # POST 요청 시 글쓰기(INSERT) 처리
        title = request.form['title'] # 제목
        author = request.form['author'] # 작성자
        content = request.form['content'] # 내용

@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'GET':
        # GET 요청 시 글수정 페이지 렌더링
        return render_template("pages/update.html")
    else:
        # POST 요청 시 글수정(UPDATE) 처리
        post_id = request.form['id'] # 글번호
        content = request.form['content'] # 내용
        title = request.form['title'] # 제목

@app.route('/delete', methods=['POST'])
def delete():
    # 해당 라우팅은 글삭제 처리만을 작업하므로, 별도의 페이지는 없다.
    post_id = request.form['id'] # 글번호
    return '글삭제'


app.run(port=8000, debug=True)