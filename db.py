from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from users import User

client = MongoClient("mongodb://rishabh:bhardwaj@chatapp-shard-00-00.j6n4l.mongodb.net:27017,chatapp-shard-00-01.j6n4l.mongodb.net:27017,chatapp-shard-00-02.j6n4l.mongodb.net:27017/ChatApp?ssl=true&replicaSet=atlas-b70y2i-shard-0&authSource=admin&retryWrites=true&w=majority")

db = client.get_database("ChatDB")
users = db.get_collection("users")


def save_user(username, email, password):
    pass_hash = generate_password_hash(password)
    users.insert_one({'_id': username, 'email': email, 'password': pass_hash})


def get_user(username):
    user_data = users.find_one({'_id': username})
    return User(user_data['_id'], user_data['email'], user_data['password'])
