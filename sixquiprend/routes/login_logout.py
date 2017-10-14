from flask import request, jsonify
from flask_login import login_required, current_user, \
     login_user, logout_user
from sixquiprend.models.user import User
from sixquiprend.sixquiprend import app

@app.route('/login', methods=['POST'])
def login():
    user = User.login(request.get_json()['username'], request.get_json()['password'])
    login_user(user, remember=True)
    return jsonify(user=user), 201

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    current_user.logout()
    logout_user()
    return jsonify(), 201

@app.route('/users/register', methods=['POST'])
def register():
    if app.config['ALLOW_REGISTER_USERS'] != True:
        return jsonify(error='Registering is deactivated'), 403
    user = User.register(request.get_json()['username'], request.get_json()['password'])
    return jsonify(user=user), 201
