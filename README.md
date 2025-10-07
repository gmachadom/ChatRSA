# ChatRSA

# First of all, clone the repo and navigate to it
```bash
 git clone
 cd ChatRSA
```
# Then, create a virtual environment and activate it
```bash
 python -m venv venv
```
# On windows:
```bash
 .\venv\Scripts\activate
```

# On linux/macOS:
```bash
 source venv/bin/activate
```
# Add the following to a .env file. 
```bash
 FLASK_APP=server/server.py
 DATABASE_FILENAME = site.db
```
# Server init
```bash
 pip install -r requirements.txt
 flask db init
 flask db migrate -m "message"
 flask db upgrade
 python .\server\server.py
```
# Run for every chat instance
```bash
 python .\client\client.py
```

