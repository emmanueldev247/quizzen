from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_session import Session

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
session = Session()