from flask import Flask, render_template, request
from tests.test_data import test_posts

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    page = request.args.get('page') # 페이지 번호
    search = request.args.get('search') # 검색어
    search_type = request.args.get('type') # 검색타입(search_all, search_title, search_content)
    return render_template("pages/index.html", posts=test_posts)

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


app.run(debug=True)