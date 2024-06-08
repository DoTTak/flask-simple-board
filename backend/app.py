import config
from flask import Flask
from apps.posts import posts_app

app = Flask(__name__)
app.register_blueprint(posts_app, url_prefix='/posts')

@app.route('/')
def index():
    # 홈 화면
    return f'{__name__}<br>홈 화면'

app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=bool(config.FLASK_DEBUG))