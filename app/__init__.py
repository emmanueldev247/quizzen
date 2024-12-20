import os
import redis
import secrets
from datetime import timedelta
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session

app = Flask(__name__, static_folder='static',
             static_url_path='/quizzen/assets',
             template_folder='templates'
            )
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))

# PostgreSQL Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:3264@localhost/quizzen'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Redis Configuration for Sessions
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'quizzen_'
app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379, db=0)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

#Initialize DB
db = SQLAlchemy(app)
Session(app)

from app import routes
