from flask import request, session, \
     render_template, jsonify
from sixquiprend.sixquiprend import app
from flask_login import login_required, current_user, \
     login_user, logout_user
from sixquiprend.models import *

@app.route('/')
def get_index():
    return render_template('index.html')

@app.route("/login", methods=["POST"])
def login():
    user = User.query.filter(User.username == request.json['username']).first()
    if user:
        if user.verify_password(request.json['password']):
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            return jsonify(status=True)
        else:
            return jsonify(status=False)
    else:
        return jsonify(status=False)

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    """Logout the current user."""
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return jsonify(status=False)

@app.route('/cards')
def show_cards():
    cards = Card.query.all()
    return jsonify(cards=[c.serialize() for c in cards])

@app.route('/current_user')
def get_current_user():
    if current_user.is_authenticated:
        return jsonify(is_logged_in=True)
    else:
        return jsonify(is_logged_in=False)
