from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient, DESCENDING
from werkzeug.security import generate_password_hash

from crypto import encrypt_message, decrypt_message
from users import User
import os

mongo_uri = os.environ.get('MONGO_URI')
client = MongoClient(port=27017)
MESSAGE_FETCH_LIMIT = 3

db = client.get_database("ChatDB")
users = db.get_collection("users")
rooms = db.get_collection("rooms")
room_members = db.get_collection("room_members")
messages = db.get_collection("messages")
rooms.create_index('headers', unique=True)


def save_user(username, email, password):
    pass_hash = generate_password_hash(password)
    users.insert_one({'_id': username, 'email': email, 'password': pass_hash})


def get_user(username):
    user_data = users.find_one({'_id': username})
    if user_data:
        return User(user_data['_id'], user_data['email'], user_data['password'])


def save_room(room_name, created_by, password):
    room_id = rooms.insert_one({'headers': {'name': room_name, 'created_by': created_by},
                                'password': password,
                                'created_at': datetime.now()}).inserted_id
    add_room_member(room_id, room_name, created_by, created_by, is_room_admin=True)
    return room_id


def update_room(room_id, room_name):
    rooms.update_one({'_id': ObjectId(room_id)}, {'$set': {'headers.name': room_name}})
    room_members.update_many({'_id.room_id': ObjectId(room_id)}, {'$set': {'room_name': room_name}})


def get_room(room_id):
    return rooms.find_one({'_id': ObjectId(room_id)})


def add_room_member(room_id, room_name, username, added_by, is_room_admin=False):
    room_members.insert_one({'_id': {'room_id': ObjectId(room_id), 'username': username}, 'room_name': room_name,
                             'added_by': added_by, 'added_at': datetime.now(), 'is_room_admin': is_room_admin})


def add_room_members(room_id, room_name, usernames, added_by):
    room_members.insert_many([{'_id': {'room_id': ObjectId(room_id), 'username': username}, 'room_name': room_name,
                               'added_by': added_by, 'added_at': datetime.now(), 'is_room_admin': False}
                              for username in usernames])


def remove_room_members(room_id, usernames):
    room_members.delete_many({'_id': {'$in': [{'room_id': ObjectId(room_id), 'username': username}
                                              for username in usernames]}})


def get_room_members(room_id):
    return list(room_members.find({'_id.room_id': ObjectId(room_id)}))


def get_rooms_for_user(username):
    return list(room_members.find({'_id.username': username}))


def is_room_member(room_id, username):
    return room_members.count_documents({'_id': {'room_id': ObjectId(room_id), 'username': username}})


def is_room_admin(room_id, username):
    return room_members.find_one({'_id': {'room_id': ObjectId(room_id), 'username': username}})['is_room_admin']


def save_message(room_id, text, sender, key):
    encrypted_message = encrypt_message(text, key)
    messages.insert_one({'room_id': room_id, 'text': encrypted_message, 'sender': sender, 'created_at': datetime.now()})


def get_messages(room_id, key, page=0):
    offset = page * MESSAGE_FETCH_LIMIT
    total_messages = list(
        messages.find({'room_id': room_id}).sort('_id', DESCENDING).limit(MESSAGE_FETCH_LIMIT).skip(offset))
    for message in total_messages:
        message['created_at'] = message['created_at'].strftime("%d %b, %H:%M")
    for message in total_messages:
        message['text'] = decrypt_message(message['text'], key)
    return total_messages[::-1]


def get_all_users():
    all_users = list(users.find({}, {'_id': 1}))
    names = [data['_id'] for data in all_users]
    return names


def remove_room(room_id):
    rooms.remove({'_id': ObjectId(room_id)})
    room_members.delete_many({'_id.room_id': ObjectId(room_id)})


def get_room_key(room_id):
    room = rooms.find_one({'_id': ObjectId(room_id)})
    return room['password']
