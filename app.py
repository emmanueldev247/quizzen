from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_caching import Cache
from redis import Redis


app = Flask(__name__, static_url_path='/quizzen/static')
"""
app.config.from_object('config')

db = SQLAlchemy(app)
jwt = JWTManager(app)
mail = Mail(app)
cache = Cache(app)
redis = Redis.from_url(app.config['REDIS_URL'])

@app.route('/', strict_slashes=False)
def index():
    return render_template('index.html')

@app.route('/dashboard', strict_slashes=False)
def dashboard():
    return render_template('dashboard.html', strict_slashes=False)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
