import config
from flask import Flask, redirect, request, render_template
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


app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=bool(config.FLASK_DEBUG))