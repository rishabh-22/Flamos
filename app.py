import os
from datetime import datetime
from bson.json_util import dumps
from flask import Flask, render_template, redirect, request, url_for
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_socketio import SocketIO, join_room, leave_room
from pymongo.errors import DuplicateKeyError

from crypto import generate_key_from_password
from db import get_user, save_user, get_rooms_for_user, save_room, add_room_members, get_room, is_room_member, \
    get_room_members, get_messages, is_room_admin, update_room, remove_room_members, save_message, get_all_users, \
    remove_room, get_room_key

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def home():
    rooms = []
    if current_user.is_authenticated:
        rooms = get_rooms_for_user(current_user.username)
    return render_template("index.html", rooms=rooms)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for('home'))
        else:
            message = 'Failed to login, please check username and password!'
    return render_template('login.html', message=message)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            save_user(username, email, password)
            return redirect(url_for('login'))
        except DuplicateKeyError:
            message = 'Username already taken, please try with a different username!'
    return render_template('signup.html', message=message)


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/create-room/', methods=['GET', 'POST'])
@login_required
def create_room():
    try:
        message = ''
        if request.method == 'POST':
            room_name = request.form.get('room_name')
            usernames = [username.strip() for username in request.form.get('members').split(',')]
            if current_user.username in usernames:
                usernames.remove(current_user.username)

            password = request.form.get('room_password')
            key = generate_key_from_password(password)

            if len(room_name) and len(usernames):
                room_id = save_room(room_name, current_user.username, key)
                for username in usernames:
                    if username not in get_all_users():
                        message = 'Please add valid names of existing users!'
                        return render_template('create_room.html', message=message)
                add_room_members(room_id, room_name, usernames, current_user.username)
                return redirect(url_for('view_room', room_id=room_id))
            else:
                message = 'Failed to create room! Please check the input values of members.'
        return render_template('create_room.html', message=message)
    except DuplicateKeyError:
        message = 'You already have a room with that name. Try another name!'
        return render_template('create_room.html', message=message)


@app.route('/rooms/<room_id>/')
@login_required
def view_room(room_id):
    room = get_room(room_id)
    message = request.args.get('message')
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        key = get_room_key(room_id)
        messages = get_messages(room_id, key)
        return render_template('view_room.html', username=current_user.username, room=room, room_members=room_members,
                               messages=messages, message=message)
    else:
        message = 'Room not found!'
        rooms = get_rooms_for_user(current_user.username)
        return render_template("index.html", rooms=rooms, message=message)


@app.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    if room and is_room_admin(room_id, current_user.username):
        existing_room_members = [member['_id']['username'] for member in get_room_members(room_id)]
        room_members_str = ",".join(existing_room_members)
        message = ''
        if request.method == 'POST':
            room_name = request.form.get('room_name')
            room['name'] = room_name
            update_room(room_id, room_name)

            new_members = [username.strip() for username in request.form.get('members').split(',')]
            members_to_add = list(set(new_members) - set(existing_room_members))
            members_to_remove = list(set(existing_room_members) - set(new_members))
            if len(members_to_add):
                for member in members_to_add:
                    if member not in get_all_users():
                        message = 'Please add valid names of existing users!'
                        return render_template('edit_room.html', room=room, room_members_str=room_members_str,
                                               message=message)
                add_room_members(room_id, room_name, members_to_add, current_user.username)
            if len(members_to_remove):
                if current_user.username in members_to_remove:
                    members_to_remove.remove(current_user.username)
                    message = "Admins can't remove themselves. "
                existing_set = set(existing_room_members)
                existing_set.remove(current_user.username)
                if existing_set == set(members_to_remove):
                    message = 'Rooms should have at least two members.'
                    return render_template('edit_room.html', room=room, room_members_str=room_members_str,
                                           message=message)
                remove_room_members(room_id, members_to_remove)
            message += 'Room edited successfully'
            return redirect(url_for('view_room', room_id=room_id, message=message))
        return render_template('edit_room.html', room=room, room_members_str=room_members_str, message=message)
    else:
        message = 'Room not found!'
        rooms = get_rooms_for_user(current_user.username)
        return render_template("index.html", rooms=rooms, message=message)


@app.route('/rooms/<room_id>/delete')
@login_required
def delete_room(room_id):
    remove_room(room_id)
    message = 'Room deleted successfully!'
    rooms = get_rooms_for_user(current_user.username)
    return render_template("index.html", rooms=rooms, message=message)


@app.route('/rooms/<room_id>/messages/')
@login_required
def get_older_messages(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        page = int(request.args.get('page', 0))
        key = get_room_key(room_id)
        messages = get_messages(room_id, key, page)
        return dumps(messages)
    else:
        return 'Room not found', 404


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info(f"{data['username']} has joined the room {data['room']}.")
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['username'],
                                                                    data['room'],
                                                                    data['message']))
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    key = get_room_key(data['room'])
    save_message(data['room'], data['message'], data['username'], key)
    socketio.emit('receive_message', data, room=data['room'])


@socketio.on("leave_room")
def handle_leave_room_event(data):
    app.logger.info(f'{data["username"]} has left the room{data["room"]}.')
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])


@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    socketio.run(app, debug=True)
