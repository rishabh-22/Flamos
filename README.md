# Flask-chat-app

## This is chat room based application made using Flask, MongoDB utilizing sockets functionality to create chat rooms and implement basic user authentication.

#### Chat history is stored in database.
#### The users need to sign up in order to be participate in chat and/or create a room.
#### Users will be required to provide a room password during the creation of the room which will be used to encrypt their messages before storing in the database.
#### Room editing is also provided which allows modifying room name, members, and deleting the room itself.
#### Room password can't be changed as it is used as encryption/decryption key. Changing it will result in a different key, which won't be able  to decrypt the stored messages.

## To run the application:
```
pip install -r requirements.txt
export MONGO_URI= <mongo_uri>
export SECRET_KEY = <secret_key>
```

and then run:

```
python app.py
```
