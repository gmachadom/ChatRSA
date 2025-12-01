# 🏗️ Arquitetura do ChatRSA (Versão Melhorada)

## Diagrama Geral

```
┌──────────────────────────────────────────────────────────────────┐
│                     CAMADAS DA APLICAÇÃO                         │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────┐          ┌──────────────────┐
│   CLIENT (CLI)      │          │   CLIENT (WEB)   │
│  client.client.py   │  ◄────►  │   streamlit      │
│                     │          │   (pages/*.py)   │
└──────────┬──────────┘          └────────┬─────────┘
           │                              │
           │         HTTP/SocketIO        │
           └──────────────┬───────────────┘
                          │
                    ┌─────▼──────┐
                    │   SERVIDOR │
                    │  Flask +   │
                    │  SocketIO  │
                    └─────┬──────┘
                          │
                    ┌─────▼──────┐
                    │  DATABASE  │
                    │  SQLite    │
                    │  site.db   │
                    └────────────┘
```

---

## 📦 Componentes Principais

### 1. **Cliente (Frontend)**

#### Estrutura

```
client/
├── __init__.py
├── client.py              # Lógica principal do cliente
├── session_keys/          # Chaves de sessão criptografadas
└── users_key/             # Chaves privadas criptografadas
```

#### Funções Principais em `client.py`

```python
# ========== AUTENTICAÇÃO ==========
register_user(username, password)
login_user(username, password)

# ========== AMIZADE ==========
send_friend_request(sender, receiver)           # NOVO
get_pending_friend_requests(username)           # NOVO
accept_friend_request(request_id)               # NOVO
reject_friend_request(request_id)               # NOVO
get_friend_list(username)

# ========== CONVITE DE CHAT ==========
send_chat_invitation(inviter, invitee, room)    # NOVO
get_pending_chat_invitations(username)          # NOVO
accept_chat_invitation(invitation_id)           # NOVO
decline_chat_invitation(invitation_id)          # NOVO

# ========== CHAT ==========
join(username, room, user_id)
leave_room_client(room, username, user_id)
request_user_public_key(username, room)
send_message(username, recipient, message, room, timestamp)
get_message_history(username, room)

# ========== EVENTOS SOCKETIO ==========
@sio.on('generate_session_key')
@sio.on('receive_session_key')
@sio.on('receive_message')
@sio.on('user_joined')                          # NOVO
@sio.on('user_left')                            # NOVO
```

### 2. **Servidor (Backend)**

#### Estrutura

```
server/
├── __init__.py
├── server.py              # Aplicação Flask principal
├── utils.py               # Funções criptográficas
└── __pycache__/
```

#### Modelos de Dados

```python
# ========== USER ==========
class User:
    - id (Primary Key)
    - username (Unique)
    - password_hash
    - public_key
    - friend_list (comma-separated)

# ========== FRIENDREQUEST (NOVO) ==========
class FriendRequest:
    - id (Primary Key)
    - sender_id (Foreign Key → User)
    - receiver_id (Foreign Key → User)
    - status: pending | accepted | rejected
    - created_at

# ========== CHATINVITATION (NOVO) ==========
class ChatInvitation:
    - id (Primary Key)
    - inviter_id (Foreign Key → User)
    - invitee_id (Foreign Key → User)
    - room_id
    - status: pending | accepted | declined
    - created_at

# ========== MESSAGE ==========
class Message:
    - id (Primary Key)
    - sender_id (Foreign Key → User)
    - recipient_id (Foreign Key → User)
    - content (CRIPTOGRAFADO)
    - room_id
    - timestamp
    - duration (TTL)

# ========== SESSION (MELHORADO) ==========
class Session:
    - id (Primary Key)
    - room_name (Unique)
    - session_key (CRIPTOGRAFADO com RSA)
    - created_at
    - is_active (Invalidação ao sair)
    - participants (Rastreamento de IDs)
```

#### Endpoints REST

```
┌─────────────────────────────────────────────────────────┐
│                  AUTENTICAÇÃO                            │
├──────────────────────────────────────────────────────────┤
POST   /register              Registrar novo usuário
POST   /login                 Fazer login
├─────────────────────────────────────────────────────────┤
│              GERENCIAR AMIGOS (NOVO)                     │
├──────────────────────────────────────────────────────────┤
POST   /friend_request/send            Enviar pedido
POST   /friend_request/<id>/accept      Aceitar pedido
POST   /friend_request/<id>/reject      Rejeitar pedido
GET    /friend_requests/<username>      Listar pedidos
├─────────────────────────────────────────────────────────┤
│          GERENCIAR CONVITES DE CHAT (NOVO)              │
├──────────────────────────────────────────────────────────┤
POST   /chat_invitation/send            Enviar convite
POST   /chat_invitation/<id>/accept      Aceitar convite
POST   /chat_invitation/<id>/decline     Declinar convite
GET    /chat_invitations/<username>      Listar convites
├─────────────────────────────────────────────────────────┤
│                    USUÁRIOS                              │
├──────────────────────────────────────────────────────────┤
GET    /all_users                       Listar todos
GET    /public_key/<username>           Obter chave pública
GET    /friendlist/<username>           Listar amigos
POST   /friendlist                      Verificar amizade
├─────────────────────────────────────────────────────────┤
│                    MENSAGENS                             │
├──────────────────────────────────────────────────────────┤
GET    /messages/<username>/<room>      Histórico
└─────────────────────────────────────────────────────────┘
```

#### Eventos SocketIO

```
┌─────────────────────────────────────────────────────┐
│              EVENTOS DE CHAT                         │
├──────────────────────────────────────────────────────┤
join               Entrar em sala
leave              Sair de sala
send_session_key   Enviar chave de sessão
send_message       Enviar mensagem
├─────────────────────────────────────────────────────┤
│          EVENTOS DE AUTENTICAÇÃO (NOVO)             │
├──────────────────────────────────────────────────────┤
friend_request_notification    Novo pedido de amizade
friend_request_accepted        Pedido aceito
chat_invitation_notification   Novo convite de chat
chat_invitation_accepted       Convite aceito
chat_invitation_declined       Convite recusado
├─────────────────────────────────────────────────────┤
│            EVENTOS DE PARTICIPAÇÃO (NOVO)           │
├──────────────────────────────────────────────────────┤
user_joined        Usuário entrou na sala
user_left          Usuário saiu da sala
├─────────────────────────────────────────────────────┤
│                 CALLBACKS PADRÃO                     │
├──────────────────────────────────────────────────────┤
generate_session_key     Gerar chave de sessão
receive_session_key      Receber chave de sessão
receive_message          Receber mensagem
└─────────────────────────────────────────────────────┘
```

### 3. **Criptografia**

#### Arquivo: `server/utils.py`

```python
# ========== RSA (2048 bits) ==========
generate_keypair()                      # Gera par RSA
encrypt_with_public_key(data, pub_key) # Criptografa com RSA
decrypt_with_private_key(data, priv_key) # Descriptografa com RSA

# ========== ChaCha20 ==========
encrypt_chacha20_message(key, message)  # Criptografa ChaCha20
decrypt_chacha20_message(key, encrypted) # Descriptografa ChaCha20

# ========== Derivação de Chave ==========
derive_key(password, salt)              # PBKDF2 (100k iterações)

# ========== AES-256-GCM ==========
encrypt_private_key(key, password)      # Criptografa chave privada
decrypt_private_key(encrypted, password) # Descriptografa chave privada

# ========== Persistência ==========
save_private_key(data, username)        # Salva chave privada
recover_private_key(username)           # Recupera chave privada

# ========== DESCONTINUADAS ==========
encrypt_session_key()      ❌ Removido (simplificação)
decrypt_session_key()      ❌ Removido (simplificação)
save_session_key()         ❌ Removido (simplificação)
recover_session_key()      ❌ Removido (simplificação)
```

### 4. **Interface (Frontend - Streamlit)**

#### Estrutura

```
pages/
├── loginScreen.py                 # Login
├── registrationScreen.py           # Registro
├── mainMenu.py                     # Menu principal (atualizado)
├── friendRequestsScreen.py         # Gerenciar pedidos (NOVO)
├── chatInvitationsScreen.py        # Gerenciar convites (NOVO)
├── addFriendScreen.py              # Adicionar amigo (atualizado)
├── chatWithFriendMenuScreen.py      # Iniciar chat (atualizado)
├── chatScreen.py                   # Conversa (simplificado)
├── chatGroupScreen.py              # Chat em grupo
└── groupChatMenuScreen.py           # Menu de grupo
```

#### Fluxo de Navegação

```
Home.py (Tela Inicial)
    ├─ Login Button → loginScreen.py
    │   └─ Sucesso → mainMenu.py
    │
    └─ Register Button → registrationScreen.py
        └─ Sucesso → loginScreen.py

mainMenu.py (Menu Principal)
    ├─ ➕ Add Friend → addFriendScreen.py
    │   └─ Envia pedido
    │       └─ Outro vê: friendRequestsScreen.py
    │
    ├─ 💬 Chat → chatWithFriendMenuScreen.py
    │   └─ Envia convite
    │       └─ Outro vê: chatInvitationsScreen.py
    │           └─ Aceita → chatScreen.py
    │
    ├─ 👥 Group → groupChatMenuScreen.py
    │   └─ Chat em grupo
    │
    └─ Ver Notificações
        ├─ friendRequestsScreen.py
        └─ chatInvitationsScreen.py
```

---

## 🔐 Fluxo de Criptografia

### 1. Registro

```
CLIENTE                          SERVIDOR
  │                                │
  │─ Gera RSA 2048 ──────────────►│
  │  ├─ private_key (secreto)     │
  │  └─ public_key (enviado)      │
  │                                │
  │─ Criptografa private_key      │
  │  ├─ Com: PBKDF2(senha)        │
  │  ├─ Algoritmo: AES-256-GCM    │
  │  └─ Salva localmente          │
  │                                │
  │─ POST /register              ─►│
  │  └─ public_key               │ Armazena: public_key
  │                                │
```

### 2. Login

```
CLIENTE                          SERVIDOR
  │                                │
  │─ Carrega private_key (disco)   │
  │                                │
  │─ Descriptografa               │
  │  ├─ Com: PBKDF2(senha)        │
  │  ├─ Algoritmo: AES-256-GCM    │
  │  └─ Em memória                │
  │                                │
  │─ POST /login              ───►│
  │                             Valida hash
  │◄─── OK                      │
  │                                │
```

### 3. Primeira Pessoa Entra em Chat

```
ALICE                          SERVIDOR                         BOB
  │                                │                              │
  │─ emit join ──────────────────► │                              │
  │  {"room": room_alice_bob}      │                              │
  │                                │ Verifica: Session existe?    │
  │                                │ NÃO (primeira pessoa)        │
  │◄─── emit generate_session_key ─│                              │
  │                                │                              │
  │─ Gera: session_key = rand(32)  │                              │
  │                                │                              │
  │─ Requisita chave pública de BOB                               │
  │─ GET /public_key/bob ────────► │                              │
  │◄─── public_key ─────────────────│                              │
  │                                │                              │
  │─ Criptografa com RSA           │                              │
  │  session_key_encrypted =        │                              │
  │    RSA_ENCRYPT(                │                              │
  │      session_key,              │                              │
  │      bob_public_key            │                              │
  │    )                           │                              │
  │                                │                              │
  │─ emit send_session_key ───────►│                              │
  │                                │─ Armazena no BD              │
  │                                │  Session.session_key =       │
  │                                │    session_key_encrypted     │
```

### 4. Segunda Pessoa Entra em Chat

```
BOB                            SERVIDOR                         ALICE
  │                                │                              │
  │─ emit join ──────────────────► │                              │
  │  {"room": room_alice_bob}      │                              │
  │                                │ Verifica: Session existe?    │
  │                                │ SIM!                         │
  │◄─── emit receive_session_key ──│                              │
  │  {encrypted_session_key}       │                              │
  │                                │                              │
  │─ Descriptografa com RSA        │                              │
  │  session_key =                 │                              │
  │    RSA_DECRYPT(                │                              │
  │      encrypted_session_key,    │                              │
  │      bob_private_key           │                              │
  │    )                           │                              │
  │                                │                              │
  │ Agora BOB tem: session_key     │                              │
  │ Ambos têm a mesma chave!      │                              │
```

### 5. Enviar Mensagem

```
ALICE                          SERVIDOR                         BOB
  │                                │                              │
  │─ "Olá Bob!"                    │                              │
  │                                │                              │
  │─ Criptografa com ChaCha20      │                              │
  │  encrypted_msg =               │                              │
  │    ChaCha20_ENCRYPT(           │                              │
  │      "Olá Bob!",               │                              │
  │      session_key               │                              │
  │    )                           │                              │
  │                                │                              │
  │─ emit send_message ───────────►│                              │
  │                                │─ Armazena                    │
  │                                │  Message.content =           │
  │                                │    encrypted_msg             │
  │                                │                              │
  │                                │─ emit receive_message ──────►
  │                                │                              │
  │                                │        BOB descriptografa    │
  │                                │        com ChaCha20          │
  │                                │        (mesma session_key)   │
  │                                │                              │
  │                                │        Vê: "Olá Bob!" ✅     │
```

### 6. Sair da Sala

```
CARLOS                         SERVIDOR
  │                                │
  │─ emit leave ──────────────────►│
  │  {"room": room_alice_bob_carlos}
  │                                │
  │                          Remove CARLOS
  │                          dos participantes
  │                                │
  │                          Marca Session
  │                          como is_active=False
  │                                │
  │◄─── Session_key INVALIDADA    │
  │                                │
  │ CARLOS não consegue mais       │
  │ descriptografar mensagens      │
  │ que foram criptografadas       │
  │ depois da sua saída! ✅        │
```

---

## 📊 Fluxo de Dados

### Amizade

```
ALICE envia pedido
    ↓
POST /friend_request/send
    ↓
Cria FriendRequest(sender=alice, receiver=bob, status='pending')
    ↓
emit 'friend_request_notification' para BOB
    ↓
BOB vê notificação em friendRequestsScreen.py
    ↓
BOB clica "Accept"
    ↓
POST /friend_request/1/accept
    ↓
FriendRequest.status = 'accepted'
    ↓
Adiciona BOB na friendlist de ALICE
Adiciona ALICE na friendlist de BOB
    ↓
emit 'friend_request_accepted' para ALICE
    ↓
ALICE e BOB são AMIGOS ✅
```

### Convite de Chat

```
ALICE envia convite
    ↓
POST /chat_invitation/send
    ↓
Cria ChatInvitation(inviter=alice, invitee=bob, room=room_alice_bob, status='pending')
    ↓
emit 'chat_invitation_notification' para BOB
    ↓
BOB vê notificação em chatInvitationsScreen.py
    ↓
BOB clica "Accept"
    ↓
POST /chat_invitation/1/accept
    ↓
ChatInvitation.status = 'accepted'
    ↓
emit 'chat_invitation_accepted' para ALICE
    ↓
Ambos entram em chatScreen.py
    ↓
Session key é negociada (RSA)
    ↓
Conversam com ChaCha20 ✅
```

---

## 🎯 Resumo de Melhorias

| Aspecto               | Antes           | Depois         |
| --------------------- | --------------- | -------------- |
| **Segurança ao sair** | Mantinha acesso | Invalida chave |
| **Criptografia**      | 3 camadas       | 2 camadas      |
| **Amizade**           | Unilateral      | Bilateral      |
| **Notificações**      | Não             | Sim (SocketIO) |
| **Convites**          | Não             | Sim            |
| **Código**            | Complexo        | Limpo          |
| **Manutenibilidade**  | Difícil         | Fácil          |

---

**Documentação Arquitetural v2.0**
