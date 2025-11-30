import json
from http import HTTPStatus

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import logging
import os
import sys

# Garantir que o diretório raiz do projeto esteja no sys.path quando
# executamos `python server/server.py` diretamente — assim imports como
# `from logger_config import ...` funcionarão corretamente.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from logger_config import (
    log_user_registered, log_user_login, log_user_joined_session, log_user_left_session,
    log_public_key_saved, log_session_key_encrypted, log_session_key_decrypted,
    log_message_encrypted, log_message_decrypted, log_session_invalidated,
    log_friend_request_sent, log_friend_request_accepted, log_friend_request_rejected,
    log_chat_invitation_sent, log_chat_invitation_accepted, log_chat_invitation_declined,
    log_error, log_debug
)

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
    room_name = db.Column(db.String(80), nullable=False, unique=True)
    session_key = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)
    participants = db.Column(db.Text, default='')  # comma-separated user IDs

    def get_session_key(self):
        return self.session_key

    def get_participants(self):
        return [int(x) for x in self.participants.split(',') if x]

    def add_participant(self, user_id):
        participants = self.get_participants()
        if user_id not in participants:
            participants.append(user_id)
            self.participants = ','.join(map(str, participants))

    def remove_participant(self, user_id):
        participants = self.get_participants()
        if user_id in participants:
            participants.remove(user_id)
            self.participants = ','.join(map(str, participants))


class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.now)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_friend_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_friend_requests')

    def __repr__(self):
        return f'<FriendRequest {self.sender_id} -> {self.receiver_id}>'


class ChatInvitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inviter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined
    created_at = db.Column(db.DateTime, default=datetime.now)

    inviter = db.relationship('User', foreign_keys=[inviter_id], backref='sent_chat_invitations')
    invitee = db.relationship('User', foreign_keys=[invitee_id], backref='received_chat_invitations')

    def __repr__(self):
        return f'<ChatInvitation {self.inviter_id} -> {self.invitee_id} ({self.room_id})'

class MasterKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    master_key = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(200), nullable=False)

    def get_master_key(self):
        return self.master_key

    def set_master_key(self, master_key):
        self.master_key = master_key

    def get_timestamp(self):
        return self.timestamp

    def set_timestamp(self, timestamp):
        self.timestamp = timestamp

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    public_key = db.Column(db.Text, nullable=False)
    friend_list = db.Column(db.Text, default='')
    object_master_key = db.relationship(MasterKey)

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

    def get_object_master_key(self):
        return self.object_master_key

    # TODO: implementação para mudar a chave de tempos em tempos
    # (depois de fazer o login, de 3 em 3 meses mudar a chave) pegar o time stamp da chave
    # def set_master_key(self, master_key):

    def add_friend(self, friend_id):
        """Adiciona um amigo após aceitar pedido de amizade"""
        friends = self.get_friend_list()
        friend = User.query.get(friend_id)
        if friend and friend.username not in friends:
            friends.append(friend.username)
            self.friend_list = ','.join(friends)
            db.session.commit()

    def is_friend_with(self, username):
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
    master_key = data['master_key']
    password_hash = generate_password_hash(password)
    # error handling
    if User.query.filter_by(username=username).first():
        log_error(f"Tentativa de registro com username duplicado", "server.py", "register", f"Username: {username}")
        return (jsonify(detail="User already exists."), HTTPStatus.CONFLICT)
    
    user = User(username=username, password_hash=password_hash, public_key=public_key, master_key=master_key)
    db.session.add(user)
    db.session.commit()
    
    log_user_registered(username, "server.py", "register")
    log_public_key_saved(username, "server.py", "register")
    
    return jsonify({
        'message': 'User registered successfully',
    }), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.get_password_hashed(), password):
        log_error(f"Tentativa de login com credenciais inválidas", "server.py", "login", f"Username: {username}")
        return jsonify({'message': 'Invalid credentials'}), 401

    log_user_login(username, "server.py", "login")
    return jsonify({'message': 'Login successful', 'username': username}), 200

@app.route('/auth_code/<username>/', methods=['GET'])
def get_user_master_key(username):
    master_key = User.query.filter_by(username=username).first().get_object_master_key().get_master_key()

    if master_key:
        return jsonify({'message': 'User master key achieved', 'master_key': master_key}), 200

@app.route('/master_key_timestamp/<username>', methods=['GET'])
def get_user_master_key_timestamp(username):
    timestamp = User.query.filter_by(username=username).first().get_object_master_key().get_timestamp()
    gap_of_time = datetime.now() - timestamp
    if gap_of_time.days > 90:
        return True
    else:
        return False

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


# ---------- User Routes (FRIEND REQUESTS) -------------

@app.route('/friend_request/send', methods=['POST'])
def send_friend_request():
    """Envia um pedido de amizade"""
    data = request.json
    sender_username = data['sender_username']
    receiver_username = data['receiver_username']

    sender = User.query.filter_by(username=sender_username).first()
    receiver = User.query.filter_by(username=receiver_username).first()

    if not sender or not receiver:
        log_error("Usuário não encontrado ao enviar friend request", "server.py", "send_friend_request", f"De: {sender_username}, Para: {receiver_username}")
        return jsonify({'message': 'User not found'}), 404

    if sender.is_friend_with(receiver_username):
        log_debug(f"Tentativa de friend request com amigo já existente", "server.py", "send_friend_request")
        return jsonify({'message': 'Already friends'}), 400

    # Verifica se já existe pedido pendente
    existing_request = FriendRequest.query.filter_by(
        sender_id=sender.id, receiver_id=receiver.id, status='pending'
    ).first()
    if existing_request:
        log_debug(f"Friend request duplicado detectado", "server.py", "send_friend_request")
        return jsonify({'message': 'Friend request already sent'}), 400

    friend_request = FriendRequest(sender_id=sender.id, receiver_id=receiver.id)
    db.session.add(friend_request)
    db.session.commit()

    log_friend_request_sent(sender_username, receiver_username, "server.py", "send_friend_request")

    # Notifica o receptor
    socketio.emit('friend_request_notification', {
        'sender_username': sender_username,
        'request_id': friend_request.id
    }, room=receiver_username, namespace='/')

    return jsonify({
        'message': 'Friend request sent',
        'request_id': friend_request.id
    }), 201


@app.route('/friend_request/<request_id>/accept', methods=['POST'])
def accept_friend_request(request_id):
    """Aceita um pedido de amizade"""
    friend_request = FriendRequest.query.get(request_id)
    
    if not friend_request:
        log_error("Friend request não encontrado", "server.py", "accept_friend_request", f"Request ID: {request_id}")
        return jsonify({'message': 'Request not found'}), 404

    if friend_request.status != 'pending':
        log_debug(f"Tentativa de aceitar friend request já processado", "server.py", "accept_friend_request")
        return jsonify({'message': 'Request already processed'}), 400

    sender = friend_request.sender
    receiver = friend_request.receiver

    # Adiciona como amigos (bilateral)
    sender.add_friend(receiver.id)
    receiver.add_friend(sender.id)

    friend_request.status = 'accepted'
    db.session.commit()

    log_friend_request_accepted(sender.username, receiver.username, "server.py", "accept_friend_request")

    # Notifica o remetente
    socketio.emit('friend_request_accepted', {
        'friend_username': receiver.username
    }, room=sender.username, namespace='/')

    return jsonify({'message': 'Friend request accepted'}), 200


@app.route('/friend_request/<request_id>/reject', methods=['POST'])
def reject_friend_request(request_id):
    """Rejeita um pedido de amizade"""
    friend_request = FriendRequest.query.get(request_id)
    
    if not friend_request:
        log_error("Friend request não encontrado", "server.py", "reject_friend_request", f"Request ID: {request_id}")
        return jsonify({'message': 'Request not found'}), 404

    if friend_request.status != 'pending':
        log_debug(f"Tentativa de rejeitar friend request já processado", "server.py", "reject_friend_request")
        return jsonify({'message': 'Request already processed'}), 400

    log_friend_request_rejected(friend_request.sender.username, friend_request.receiver.username, "server.py", "reject_friend_request")
    
    friend_request.status = 'rejected'
    db.session.commit()

    return jsonify({'message': 'Friend request rejected'}), 200


@app.route('/friend_requests/<username>', methods=['GET'])
def get_friend_requests(username):
    """Retorna pedidos de amizade pendentes"""
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404

    pending_requests = FriendRequest.query.filter_by(
        receiver_id=user.id, status='pending'
    ).all()

    requests_data = [{
        'request_id': req.id,
        'sender_username': req.sender.username,
        'created_at': req.created_at.isoformat()
    } for req in pending_requests]

    return jsonify({'friend_requests': requests_data}), 200


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


# ---------- Friendlist Routes (ATUALIZADO) -------------

@app.route('/friendlist/<username>', methods=['GET'])
def get_friend_list(username):
    user = User.query.filter_by(username=username).first()
    if user:
        friend_list = user.get_friend_list()
        return jsonify({"friends": friend_list}), 200
    return jsonify({"message": "User not found"}), 404


# ---------- CHAT INVITATION ROUTES (NOVO) ----------

@app.route('/chat_invitation/send', methods=['POST'])
def send_chat_invitation():
    """Envia um convite para iniciar chat"""
    data = request.json
    inviter_username = data['inviter_username']
    invitee_username = data['invitee_username']
    room_id = data.get('room_id')

    inviter = User.query.filter_by(username=inviter_username).first()
    invitee = User.query.filter_by(username=invitee_username).first()

    if not inviter or not invitee:
        log_error("Usuário não encontrado ao enviar chat invitation", "server.py", "send_chat_invitation", f"De: {inviter_username}, Para: {invitee_username}")
        return jsonify({'message': 'User not found'}), 404

    if not inviter.is_friend_with(invitee_username):
        log_error("Tentativa de convite para chat sem amizade", "server.py", "send_chat_invitation", f"De: {inviter_username}, Para: {invitee_username}")
        return jsonify({'message': 'You are not friends with this user'}), 403

    # Verifica se já existe convite pendente
    existing_invitation = ChatInvitation.query.filter_by(
        inviter_id=inviter.id, invitee_id=invitee.id, 
        room_id=room_id, status='pending'
    ).first()
    if existing_invitation:
        log_debug(f"Chat invitation duplicado detectado", "server.py", "send_chat_invitation")
        return jsonify({'message': 'Chat invitation already sent'}), 400

    chat_invitation = ChatInvitation(
        inviter_id=inviter.id,
        invitee_id=invitee.id,
        room_id=room_id
    )
    db.session.add(chat_invitation)
    db.session.commit()

    log_chat_invitation_sent(inviter_username, invitee_username, room_id, "server.py", "send_chat_invitation")

    # Notifica o convidado
    socketio.emit('chat_invitation_notification', {
        'inviter_username': inviter_username,
        'room_id': room_id,
        'invitation_id': chat_invitation.id
    }, room=invitee_username, namespace='/')

    return jsonify({
        'message': 'Chat invitation sent',
        'invitation_id': chat_invitation.id
    }), 201


@app.route('/chat_invitation/<invitation_id>/accept', methods=['POST'])
def accept_chat_invitation(invitation_id):
    """Aceita um convite de chat"""
    invitation = ChatInvitation.query.get(invitation_id)
    
    if not invitation:
        log_error("Chat invitation não encontrado", "server.py", "accept_chat_invitation", f"Invitation ID: {invitation_id}")
        return jsonify({'message': 'Invitation not found'}), 404

    if invitation.status != 'pending':
        log_debug(f"Tentativa de aceitar chat invitation já processado", "server.py", "accept_chat_invitation")
        return jsonify({'message': 'Invitation already processed'}), 400

    invitation.status = 'accepted'
    db.session.commit()

    log_chat_invitation_accepted(invitation.invitee.username, invitation.inviter.username, invitation.room_id, "server.py", "accept_chat_invitation")

    # Notifica o remetente do convite
    socketio.emit('chat_invitation_accepted', {
        'invitee_username': invitation.invitee.username,
        'room_id': invitation.room_id
    }, room=invitation.inviter.username, namespace='/')

    return jsonify({'message': 'Chat invitation accepted'}), 200


@app.route('/chat_invitation/<invitation_id>/decline', methods=['POST'])
def decline_chat_invitation(invitation_id):
    """Declina um convite de chat"""
    invitation = ChatInvitation.query.get(invitation_id)
    
    if not invitation:
        log_error("Chat invitation não encontrado", "server.py", "decline_chat_invitation", f"Invitation ID: {invitation_id}")
        return jsonify({'message': 'Invitation not found'}), 404

    if invitation.status != 'pending':
        log_debug(f"Tentativa de rejeitar chat invitation já processado", "server.py", "decline_chat_invitation")
        return jsonify({'message': 'Invitation already processed'}), 400

    log_chat_invitation_declined(invitation.invitee.username, invitation.inviter.username, invitation.room_id, "server.py", "decline_chat_invitation")
    
    invitation.status = 'declined'
    db.session.commit()

    # Notifica o remetente
    socketio.emit('chat_invitation_declined', {
        'invitee_username': invitation.invitee.username,
        'room_id': invitation.room_id
    }, room=invitation.inviter.username, namespace='/')

    return jsonify({'message': 'Chat invitation declined'}), 200


@app.route('/chat_invitations/<username>', methods=['GET'])
def get_chat_invitations(username):
    """Retorna convites de chat pendentes"""
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404

    pending_invitations = ChatInvitation.query.filter_by(
        invitee_id=user.id, status='pending'
    ).all()

    invitations_data = [{
        'invitation_id': inv.id,
        'inviter_username': inv.inviter.username,
        'room_id': inv.room_id,
        'created_at': inv.created_at.isoformat()
    } for inv in pending_invitations]

    return jsonify({'chat_invitations': invitations_data}), 200


@app.route('/user/<username>/sent_invitations', methods=['GET'])
def get_sent_invitations(username):
    """Retorna convites de chat enviados pelo usuário (pending ou accepted)"""
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Get both pending and accepted invitations sent by this user
    sent_invitations = ChatInvitation.query.filter_by(
        inviter_id=user.id
    ).filter(ChatInvitation.status.in_(['pending', 'accepted'])).all()

    invitations_data = [{
        'invitation_id': inv.id,
        'invitee_username': inv.invitee.username,
        'room_id': inv.room_id,
        'status': inv.status,
        'created_at': inv.created_at.isoformat()
    } for inv in sent_invitations]

    return jsonify({'sent_invitations': invitations_data}), 200


@app.route('/user/<username>/active_chats', methods=['GET'])
def get_active_chats(username):
    """Retorna salas de chat ativas onde o usuário é participante"""
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Get sessions where user is a participant
    sessions = Session.query.all()
    active_chats = []
    
    for session in sessions:
        participants = session.get_participants()
        if user.id in participants and session.is_active:
            active_chats.append({
                'room_id': session.room_name,
                'is_active': session.is_active,
                'participant_count': len(participants)
            })
    
    return jsonify({'active_chats': active_chats}), 200


@app.route('/user', methods=['POST'])
def old_add_user_in_friendlist():
    """DESCONTINUADO: Use /friend_request/send"""
    return jsonify({'message': 'Use /friend_request/send endpoint'}), 410


@app.route('/friendlist', methods=['POST'])
def is_user_friend():
    """Verifica se dois usuários são amigos"""
    username = request.json['username']
    username_to_check = request.json.get('username_to_talk') or request.json.get('username_to_check')
    user = User.query.filter_by(username=username).first()

    if not user or not user.is_friend_with(username_to_check):
        return jsonify({'message': 'Not friends'}), 404

    return jsonify({'status': True}), 200


# ---------- Chat Events Functions (MELHORADO PARA SEGURANÇA) -------------

@socketio.on('join')
def on_join(data):
    """
    Evento quando usuário entra em uma sala de chat.
    CORRIGIDO: Implementa handshake em cadeia para múltiplos participantes
    """
    room = data['room']
    username = data.get('username')
    user_id = data.get('user_id')
    
    join_room(room)
    log_user_joined_session(username, room, "server.py", "on_join")

    session = Session.query.filter_by(room_name=room).first()
    
    if not session:
        # PRIMEIRA PESSOA: Deve gerar a session_key
        log_debug(f"Primeira pessoa na sala {room}, gerando nova session_key", "server.py", "on_join")
        emit('generate_session_key', {'room': room, 'username': username})
    else:
        # OUTROS PARTICIPANTES
        session.add_participant(user_id)
        session.is_active = True
        db.session.commit()
        
        log_user_joined_session(username, room, "server.py", "on_join")
        
        # 🔗 Handshake em Cadeia:
        # 1. Avisar os PRIMEIROS participantes que um novo entrou
        # 2. Enviar a chave pública do novo participante
        # 3. Primeiro re-criptografa a chave para o novo
        # 4. Novo descriptografa com sua chave privada
        
        # Busca a chave pública do novo participante
        new_user = User.query.filter_by(username=username).first()
        new_user_public_key = new_user.get_public_key() if new_user else None
        
        emit('new_participant_joined', {
            'room': room,
            'new_username': username,
            'new_public_key': new_user_public_key,  # ✅ Agora envia a chave pública
            'participant_count': len(session.get_participants())
        }, to=room, skip_sid=request.sid)  # Avisar TODOS MENOS o novo
        
        # Notifica outros que alguém entrou
        emit('user_joined', {
            'username': username,
            'room': room,
            'participant_count': len(session.get_participants())
        }, to=room, include_self=False)


@socketio.on('leave')
def on_leave(data):
    """
    Evento quando usuário sai de uma sala.
    Remove participante. A sala permanece ativa se houver outros participantes.
    MELHORADO: Suporta grupo chat (não invalida sessão, apenas remove participante)
    """
    room = data['room']
    username = data.get('username')
    user_id = data.get('user_id')
    
    leave_room(room)
    log_user_left_session(username, room, "server.py", "on_leave")

    session = Session.query.filter_by(room_name=room).first()
    if session:
        session.remove_participant(user_id)
        
        # Se foi o último participante, destrói a sessão
        if not session.get_participants():
            log_debug(f"Último participante saiu - sessão destruída", "server.py", "on_leave")
            db.session.delete(session)
        else:
            # MELHORADO: Manter session ativa se houver participantes
            # Para grupo chat, a sessão continua valendo para os restantes
            session.is_active = True  # ← MANTER ATIVA para outros
            log_session_invalidated(room, username, "server.py", "on_leave")
        
        db.session.commit()

    # Notifica resto da sala que alguém saiu
    emit('user_left', {
        'username': username,
        'room': room
    }, to=room, include_self=False)


@socketio.on('send_session_key')
def handle_session_key(data):
    """
    🔗 HANDSHAKE EM CADEIA - Primeira pessoa gera session_key
    
    FLUXO:
    1. ALICE gera chave aleatória (32 bytes)
    2. ALICE criptografa com RSA de BOB e envia ao servidor
    3. Servidor armazena encrypted_key
    4. Quando BOB recebe: descriptografa com sua chave privada ✅
    5. Quando CARLOS entra: Servidor notifica ALICE/BOB que novo chegou
    6. ALICE/BOB re-criptografa para CARLOS usando RSA de CARLOS
    7. CARLOS descriptografa com sua chave privada ✅
    """
    room = data['room']
    encrypted_session_key = data['encrypted_session_key']
    username = data.get('username', 'Unknown')
    
    # Armazena: a chave criptografada (pelo primeiro participante)
    session = Session.query.filter_by(room_name=room).first()
    if not session:
        session = Session(room_name=room, session_key=encrypted_session_key)
        db.session.add(session)
    else:
        # Se já existe, atualiza com a chave do novo participante
        session.session_key = encrypted_session_key
    
    db.session.commit()
    
    log_session_key_encrypted(username, room, "server.py", "handle_session_key")


@socketio.on('send_reencrypted_session_key')
def send_reencrypted_session_key(data):
    """
    🔗 HANDSHAKE EM CADEIA - Recebe chave re-criptografada de um participante
    
    Quando ALICE re-criptografa para CARLOS, ela envia a nova chave criptografada
    (que só CARLOS consegue descriptografar com sua chave privada)
    """
    room = data['room']
    new_username = data['new_username']
    encrypted_for_new = data['encrypted_session_key']  # Criptografada com RSA de new_username
    
    log_debug(
        f"Chave re-criptografada recebida para {new_username} na sala {room}",
        "server.py",
        "send_reencrypted_session_key"
    )
    
    # Envia APENAS para o novo participante
    # (Servidor não sabe qual é o SID dele, então emite para o room e ele pega)
    emit('receive_reencrypted_session_key', {
        'encrypted_session_key': encrypted_for_new,
        'room': room,
        'from_username': data.get('from_username', 'participant')
    }, to=room)
    
    log_debug(
        f"Chave re-criptografada enviada para {new_username}",
        "server.py",
        "send_reencrypted_session_key"
    )
    
    # Envia para TODOS na sala (menos quem enviou)
    # Todos descriptografam com sua própria chave privada
    emit('receive_session_key', {
        'encrypted_session_key': encrypted_session_key,
        'room': room,
        'from_user': username
    }, to=room, include_self=False)


@socketio.on('send_message')
def handle_send_message(data):
    """
    Recebe mensagem criptografada e armazena.
    Suporta tanto mensagens 1-a-1 quanto mensagens de grupo.
    
    - Chat 1-a-1: user_to_talk é o nome do outro usuário
    - Chat grupo: user_to_talk é None
    """
    encrypted_message = data['encrypted_message']
    username = data['username']
    user_to_talk = data.get('user_to_talk')  # None para chats de grupo
    room = data['room']
    timestamp = data['timestamp']
    
    # Determina o tipo de chat
    is_group_chat = user_to_talk is None
    
    # Validação de segurança depende do tipo de chat
    if is_group_chat:
        # Chat de grupo: valida se a Session existe e está ativa
        session = Session.query.filter_by(room_name=room).first()
        if not session or not session.is_active:
            log_error("Tentativa de enviar mensagem em sessão de grupo inativa ou inexistente", "server.py", "handle_send_message", f"Room: {room}")
            emit('error', {'message': 'Chat session has ended or is no longer active'})
            return
    
    # Processa IDs de usuário
    try:
        if is_group_chat:
            # Para chats de grupo, recipient_id é o mesmo do sender (apenas log)
            sender_id, recipient_id = extract_user_ids(username, username)
        else:
            # Para chats 1-a-1, recipient_id é o do outro usuário
            sender_id, recipient_id = extract_user_ids(username, user_to_talk)
    except Exception as e:
        log_error("Falha ao processar IDs de usuários", "server.py", "handle_send_message", f"De: {username}, Para: {user_to_talk}, Erro: {str(e)}")
        emit('error', {'message': 'Failed to process message'})
        return
    
    # Armazena a mensagem
    add_message(sender_id, recipient_id, encrypted_message, room, timestamp=timestamp)
    
    # Log apropriado para tipo de chat
    if is_group_chat:
        log_message_encrypted(username, "group", room, "server.py", "handle_send_message")
    else:
        log_message_encrypted(username, user_to_talk, room, "server.py", "handle_send_message")
    
    # Distribui para TODOS na sala EXCETO o remetente
    # (O remetente já vê a mensagem localmente)
    emit('receive_message', {
        'encrypted_message': encrypted_message,
        'username': username,
        'room': room,
        'timestamp': timestamp
    }, to=room, include_self=False)



"""
scheduler = BackgroundScheduler()
scheduler.add_job(func=clean_expired_messages, trigger="interval", seconds=20)  # Limpa a cada 20 segundos
scheduler.start()
"""

if __name__ == '__main__':
    socketio.run(app, debug=True)
    