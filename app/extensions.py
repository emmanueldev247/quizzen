"""Extensions to prevent circular import error"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_migrate import Migrate
from flask_mail import Mail
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
session = Session()
migrate = Migrate()
mail = Mail()
limiter = Limiter()