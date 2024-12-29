"""
This is the initialization module for the Quizzen Flask application.

The module sets up the Flask app instance, configures application settings,
and initializes essential extensions, including SQLAlchemy, Flask-Login,
Flask-Bcrypt and Flask-Session. It also registers blueprints for routing.

Key Features:
- Configuration of PostgreSQL as the database backend.
- Integration with Redis for session management.
- Custom application root and static file handling.
- Centralized initialization of extensions and blueprints.

Modules Imported:
- `os`, `secrets`: For environment variables and secure random key generation.
- `redis`: For managing session storage via a Redis backend.
- `datetime.timedelta`: For setting session expiration times.
- `flask.Flask`: To create the core Flask application instance.
- `flask_login.LoginManager`: To manage user authentication & session handling.
- `app.routes.full_bp`: The main application blueprint for routing.
- `app.extensions`: Custom application extensions for database (`db`),
  password hashing (`bcrypt`), session management (`session`) and migration Object (`migrate`)

Note:
Sensitive values such as secret keys and database credentials are managed
through environment variables for security.
"""

import os
import redis
import secrets
from datetime import timedelta
from flask import Flask
from flask_login import LoginManager
from app.extensions import db, bcrypt, session, migrate, mail, limiter
from app import routes


app = Flask(__name__, static_folder='static',
            static_url_path='/quizzen/assets',
            template_folder='templates'
            )
app.url_map.strict_slashes = False
app.config['SECRET_KEY'] = os.getenv(
                                    'JWT_SECRET_KEY',
                                    secrets.token_urlsafe(32)
                                    )
"""app.config['SERVER_NAME'] = 'emmanueldev247.tech'"""
app.config['APPLICATION_ROOT'] = '/quizzen'

uri = 'postgresql://admin:3264@localhost/quizzen'
# PostgreSQL Config
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Redis Configuration for Sessions
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'quizzen_'
app.config['SESSION_REDIS'] = redis.StrictRedis(
                                                host='localhost',
                                                port=6379,
                                                db=0
                                               )
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

app.config['MAIL_SERVER'] = 'us2.smtp.mailhostbox.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False 
app.config['MAIL_USERNAME'] = 'quizzen-support@emmanueldev247.tech'
app.config['MAIL_PASSWORD'] = 'F)ifRaj5'
app.config['MAIL_DEFAULT_SENDER'] = 'quizzen-support@emmanueldev247.tech'

# Initialize DB
db.init_app(app)
bcrypt.init_app(app)
session.init_app(app)
migrate.init_app(app, db)
mail.init_app(app)
limiter.init_app(app)

app.register_blueprint(routes.full_bp)