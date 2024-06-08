from flask import render_template, request, Blueprint


users_app = Blueprint('users', __name__, template_folder='templates')

@users_app.route('/', methods=['GET'])
def profile():
    return render_template("pages/profile.html")

@users_app.route('/edit', methods=['GET', 'POST'])
def profile_edit():
    if request.method == 'GET':
        return render_template("pages/profile_edit.html")
    else:
        pass
