#!/home/ubuntu/quizzen/venv/bin/python
"""Entry point"""

import os
from app import create_app
from app.routes import logger

app = create_app()

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    logger.info("----- Quizzen app initialized -----")
    print(app.url_map)
    app.run(host=host, port=port)
