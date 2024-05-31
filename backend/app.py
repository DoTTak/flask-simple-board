from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '게시판 글 목록'

@app.route('/view')
def view():
    return '글보기'

@app.route('/write')
def write():
    return '글쓰기'

@app.route('/update')
def update():
    return '글수정'

@app.route('/delete')
def delete():
    return '글삭제'


app.run(debug=True)