from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from users import User
import os

mongo_uri = os.environ.get('MONGO_URI')


client = MongoClient(mongo_uri)

db = client.get_database("ChatDB")
users = db.get_collection("users")


def save_user(username, email, password):
    pass_hash = generate_password_hash(password)
    users.insert_one({'_id': username, 'email': email, 'password': pass_hash})


def get_user(username):
    user_data = users.find_one({'_id': username})
    return User(user_data['_id'], user_data['email'], user_data['password'])
