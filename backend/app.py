from flask import Flask, render_template
from test_data import test_posts

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("pages/index.html", posts=test_posts)

@app.route('/view')
def view():
    return render_template("pages/detail.html")

@app.route('/write')
def write():
    return render_template("pages/write.html")

@app.route('/update')
def update():
    return render_template("pages/update.html")

@app.route('/delete')
def delete():
    # 해당 라우팅은 글삭제 처리만을 작업하므로, 별도의 페이지는 없다.
    return '글삭제'


app.run(debug=True)