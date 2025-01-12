from flask import Blueprint

from . import auth, quizzes, questions

api_v1 = Blueprint('api_v1', __name__, url_prefix='/quizzen/api/v1')
