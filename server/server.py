import os
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
db = SQLAlchemy()
app = Flask(__name__, static_folder="static", template_folder="templates")
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(base_dir, os.getenv('DATABASE_FILENAME'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)

# -------------------- MODELS ------------------
class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Remetente
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Destinatário
    content = db.Column(db.Text, nullable=False)
    room_id = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.String(200), default=datetime.now().strftime("(%a, %d %b %Y %H:%M:%S GMT)"))
    duration = db.Column(db.Interval, nullable=False, default=lambda: timedelta(seconds=50))  # Duração padrão

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            # id only
            'sender_username': self.sender.username if self.sender else None,
            'recipient_username': self.recipient.username if self.recipient else None,
        }

    def get_content(self):
        return self.content

    def get_timestamp(self):
        return self.timestamp

    def __repr__(self):
        return f'<Message {self.id} from User {self.sender_id} to User {self.recipient_id}>'


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(80), nullable=False)
    session_key = db.Column(db.Text, unique=True, nullable=False)

    def get_user_id(self):
        return self.user_id

    def get_session_key(self):
        return self.session_key


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    public_key = db.Column(db.Text, nullable=False)
    # Store friend list as a comma-separated string
    friend_list = db.Column(db.Text, default='')

    def get_user_id(self):
        return self.id

    def get_username(self):
        return self.username

    def get_password_hashed(self):
        return self.password_hash

    def get_public_key(self):
        return self.public_key

    def get_friend_list(self):
        return self.friend_list.split(',') if self.friend_list else []

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_user_to_friendlist(self, username):
        friends = self.get_friend_list()
        if username not in friends:
            friends.append(username)
            self.friend_list = ','.join(friends)

    def is_user_in_friendlist(self, username):
        return username in self.get_friend_list()
    
# ---------- Helper Functions -------------
def add_message(sender_id, recipient_id, content, room, duration_seconds=30000, timestamp=datetime.now()):
    with app.app_context():
        new_message = Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content,
            room_id=room,
            duration=timedelta(seconds=duration_seconds),  # Duração da mensagem
            timestamp=timestamp
        )
        db.session.add(new_message)
        db.session.commit()


def add_user(username, password_hash, public_key):
    with app.app_context():
        new_user = User(username=username, password_hash=password_hash, public_key=public_key)
        db.session.add(new_user)
        db.session.commit()
        return new_user.id


def extract_user_ids(user_sender, user_recipient):
    sender = User.query.filter_by(username=user_sender).first().get_user_id()
    recipient = User.query.filter_by(username=user_recipient).first().get_user_id()
    return sender, recipient


# ---------- User Authentication Routes -------------


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']
    public_key = data['public_key']
    password_hash = generate_password_hash(password)
    # error handling
    # if User.query.filter_by(username=username).first():
    #     return jsonify({'message': 'User already exists'}), 401
    
    user = User(username=username, password_hash=password_hash, public_key=public_key)
    db.session.add(user)
    db.session.commit()
    print(f"\nDEBUG: Chave publica: {public_key}")
    return jsonify({
        'message': 'User registered successfully',
    }), 201


@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.get_password_hashed(), password):
        return jsonify({'message': 'Invalid credentials'}), 401

    return jsonify({'message': 'Login successful', 'username': username}), 200


@app.route('/messages/<username>/<room>', methods=['GET'])
def get_message_history(username, room):
    user_id = User.query.filter_by(username=username).first().get_user_id()

    if user_id is None:
        return jsonify({"message": "user not founded"}), 401
    history_messages = (Message.query.filter_by(room_id=room)
                        .order_by(Message.timestamp.asc()).all())
    message_contents = [message.get_content() for message in history_messages]
    message_senders = [message.sender.get_username() for message in history_messages]
    message_timestamps = [message.get_timestamp()for message in history_messages]

    return jsonify({"message": "Message history successfully recovered",
                    "history_messages": message_contents,
                    'message_senders': message_senders,
                    'message_timestamps': message_timestamps}), 200


# ---------- Chat Functions -------------


# ---------- User Routes -------------
@app.route('/user', methods=['POST'])
def add_user_in_friendlist():
    username = request.json['username']
    user_name_to_add = request.json['username_to_add']
    user = User.query.filter_by(username=username).first()
    user_name_to_add = User.query.filter_by(username=user_name_to_add).first().get_username()

    if user_name_to_add:
        user.add_user_to_friendlist(user_name_to_add)
        db.session.commit()
        return jsonify({'message': 'User successfully added', 'User added': user_name_to_add}), 200
    return jsonify({'message': 'User not founded'}), 401


@app.route('/all_users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    all_usernames = [user.get_username() for user in users]
    return jsonify({"users": all_usernames}), 200


@app.route('/public_key/<username>', methods=['GET'])
def get_user_public_key(username):
    user_public_key = User.query.filter_by(username=username).first().get_public_key()
    if user_public_key:
        return jsonify({"message": "public key successfully achieved", "user_public_key": user_public_key}), 200
    return jsonify({"message": "public key not founded"}), 401


# ---------- Friendlist Routes -------------

@app.route('/friendlist', methods=['POST'])
def is_user_in_friendlist():
    username = request.json['username']
    username_to_talk = request.json['username_to_talk']
    user_friend_list = User.query.filter_by(username=username).first().get_friend_list()

    if username_to_talk in user_friend_list:
        return jsonify({'status': True}), 200
    return jsonify({'message': 'User not found'}), 404


@app.route('/friendlist/<username>', methods=['GET'])
def get_friend_list(username):
    user = User.query.filter_by(username=username).first()
    if user:
        friend_list = user.get_friend_list()
        return jsonify({"friends": friend_list}), 200
    return jsonify({"message": "User not found"}), 404


# ---------- Chat Events Functions -------------
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    session = Session.query.filter_by(room_name=room).first()
    if not session:
        emit('generate_session_key', {'room': room})
    else:
        encrypted_session_key = session.get_session_key()
        print(encrypted_session_key)
        emit('receive_session_key', {'encrypted_session_key': encrypted_session_key, 'room': room})


@socketio.on('send_session_key')
def handle_session_key(data):
    room = data['room']
    encrypted_session_key = data['encrypted_session_key']
    session = Session(room_name=room, session_key=encrypted_session_key)
    db.session.add(session)
    db.session.commit()
    emit('receive_session_key', {'encrypted_session_key': encrypted_session_key, 'room': room},
         to=room, include_self=False)


@socketio.on('send_message')
def handle_send_message(data):
    encrypted_message = data['encrypted_message']
    username = data['username']
    user_to_talk = data['user_to_talk']
    room = data['room']
    timestamp = data['timestamp']
    sender_id, recipient_id = extract_user_ids(username, user_to_talk)
    add_message(sender_id, recipient_id, encrypted_message, room, timestamp=timestamp)
    print(f"Message added: {encrypted_message}")
    emit('receive_message', {'encrypted_message': encrypted_message, 'username': username, 
                    'room': room, 'timestamp': timestamp}, to=room, include_self=False)


"""
scheduler = BackgroundScheduler()
scheduler.add_job(func=clean_expired_messages, trigger="interval", seconds=20)  # Limpa a cada 20 segundos
scheduler.start()
"""

if __name__ == '__main__':
    socketio.run(app, debug=True)
    