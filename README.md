# ChatRSA - Secure Chat with RSA Encryption

A secure end-to-end encrypted chat application where the server cannot read any messages. Each conversation has a unique cryptographic key known only to the participants.

## 🔐 Quick Security Overview

- **RSA 2048-bit:** User identity and secure key exchange
- **ChaCha20:** Message encryption (fast and secure)
- **Session Keys:** Unique per conversation, never reused
- **Server:** Zero-knowledge (cannot read messages)
- **End-to-End:** Only you and the recipient can read your messages

**👉 For complete security documentation, see [`README_SEGURANCA.md`](README_SEGURANCA.md)**

---

## 📦 Setup

### Clone and Setup Environment

```bash
source venv/bin/activate
git clone
cd ChatRSA
nv file.
# Create virtual environment
python -m venv venvbash
rver/server.py
# Activate (Windows)SE_FILENAME = site.db
.\venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate
```













































































































































This means **even the server cannot read your messages** because it never has access to the unencrypted session key!5. Never reused (new conversation = new key)4. Destroyed when conversation ends3. Never stored in plaintext on server2. Encrypted with RSA (only recipient can decrypt)1. Generated fresh for each conversationThe magic is in the **Session Key**:## 💡 Key Insight---- **Moment-by-Moment Breakdown:** Crucial security points- **Complete Test Procedure:** Manual testing guide- **4-Layer Security:** Client, Server, Database, New Session- **What Happens When Someone Leaves:** Security invalidation- **Key Exchange:** How Bob and Alice share the session key- **When Session is Created:** Exactly when and why- **Step-by-Step Flow:** From registration to chat- **The 3 Types of Keys:** RSA Private, RSA Public, Session KeySee **[README_SEGURANCA.md](README_SEGURANCA.md)** for:## 📖 Complete Documentation---- ✅ Beautiful Streamlit UI- ✅ Complete audit logs- ✅ Session invalidation- ✅ Message history (encrypted at rest)- ✅ Real-time delivery- ✅ End-to-end encrypted messaging- ✅ Chat invitation system- ✅ Friend request system- ✅ User registration with RSA keypair## 🚀 Features---```└── requirements.txt├── Home.py                    # Streamlit entry├── README_SEGURANCA.md        # 📖 COMPLETE DOCUMENTATION├── migrations/                # DB migrations├── users_key/                 # Local RSA private keys│   └── ...│   ├── registrationScreen.py│   ├── loginScreen.py│   ├── chatInvitationsScreen.py│   ├── chatScreen.py          # Main chat with sidebar├── pages/│   └── client.py              # SocketIO client├── client/│   └── utils.py               # Encryption functions│   ├── server.py              # Flask + SocketIO backend├── server/ChatRSA/```## 📂 Project Structure---- ✅ All operations logged and auditable- ✅ Each conversation = unique session key- ✅ Old messages unrecoverable without session key- ✅ Sessions invalidated when someone leaves- ✅ Messages encrypted end-to-end (not interceptable)- ✅ Messages cannot be read by the server## 🔒 Security Guarantees---```# Both: Send encrypted messages!# Alice: See "bob ✅" in sidebar → Click it# Bob: Accept invite# Alice: Send chat invite to bob# Bob: Register → Login → Accept friend request from "alice"# Alice: Register → Login → Send friend request to "bob"# Then in browser:streamlit run Home.py# Terminal 2: Start Streamlit UIpython .\server\server.py# Terminal 1: Start server```bash## 🧪 Quick Test---9. **Someone leaves** → Session invalidated, no reuse8. **Server stores** → Only ciphertexts (unreadable)7. **Messages encrypted** → Each with ChaCha20 + Session Key6. **Both have same Session Key** → In memory only5. **Alice enters** → Receives encrypted key, decrypts with private key4. **Bob encrypts it** → Uses Alice's RSA public key3. **Bob enters** → Generates random Session Key2. **Bob accepts** → Server creates Session1. **Alice sends invite** → Bob gets notified## 🔑 How It Works (30 seconds)---| `LOGS.md` | Available logging events || `ARQUITETURA.md` | System architecture and data models || **[README_SEGURANCA.md](README_SEGURANCA.md)** | 📖 **Complete guide** to security, encryption, key exchange, and system flow ||----------|---------|| Document | Purpose |## 📚 Documentation---```streamlit run Home.py```bash### Start Client (Streamlit UI)```python .\server\server.py```bash### Start Server```flask db upgradeflask db migrate -m "Initial schema"flask db initpip install -r requirements.txt```bash### Initialize DatabaseFLASK_APP=server/server.py
DATABASE_FILENAME=site.dbthon .\server\server.py
````

# Run for every chat instance

```bash
 python .\client\client.py
```
