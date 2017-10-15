from flask import request, jsonify
from flask_login import login_required, current_user
from sixquiprend.models.user import User
from sixquiprend.sixquiprend import app, admin_required

@app.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Display all users (admin only). Accepts offset and limit (up to 50),
    and active argument filter"""
    limit = max(0, min(50, int(request.args.get('limit', 50))))
    offset = max(0, int(request.args.get('offset', 0)))
    active = request.args.get('active')
    users = User.query
    if active != None:
        users = User.query.filter(User.active == (active != 'false'))
    users = users.order_by(User.id).limit(limit).offset(offset).all()
    return jsonify(users=users)

@app.route('/users/count', methods=['GET'])
@login_required
@admin_required
def count_users():
    """Count all users (admin only). Accepts active argument filter"""
    active = request.args.get('active')
    users = User.query
    if active != None:
        users = User.query.filter(User.active == (active != 'false'))
    count = users.count()
    return jsonify(count=count)

@app.route('/users/<int:user_id>/activate', methods=['PUT'])
@login_required
@admin_required
def activate_user(user_id):
    """Activate a user (admin only)"""
    user = User.find(user_id)
    user.change_active(True)
    return jsonify(user=user), 200

@app.route('/users/<int:user_id>/deactivate', methods=['PUT'])
@login_required
@admin_required
def deactivate_user(user_id):
    """Deactivate a user (admin only)"""
    user = User.find(user_id)
    user.change_active(False)
    return jsonify(user=user), 200

@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    User.delete(user_id)
    return '', 204

@app.route('/users/current')
def get_current_user():
    """Get current user status"""
    if current_user.is_authenticated:
        user = User.find(current_user.id)
        return jsonify(user=user)
    else:
        return jsonify(user={})
