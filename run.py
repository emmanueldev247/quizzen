"""Entry point"""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port=int(os.getenv('FLASK_RUN_PORT', 5000))
    host=int(os.getenv('FLASK_RUN_HOST', '127.0.0.1'))
    app.run(host=host, port=port)