# Quizzen - Unleash Your Inner Genius

Quizzen is an Interactive Quiz Application designed to make learning engaging and fun. With features like customizable quizzes, secure user authentication, and real-time quiz tracking, Quizzen caters to students, teachers, and anyone looking to expand their knowledge interactively.

Quizzen is live at
[Quizzen](https://emmanueldev247.publicvm.com/quizzen)

## Table of Contents

1. [Features](#features)
2. [Technologies Used](#technologies-used)
3. [Architecture Overview](#architecture-overview)
4. [Setup Instructions](#setup-instructions)
5. [Usage Guidelines](#usage-guidelines)
6. [API Endpoints](#api-endpoints)
7. [Contributing](#contributing)
8. [License](#license)

---

## Features

- **User Authentication**: Secure signup/login using JWT and OAuth.
- **Quizzes**: Create, edit, delete, and take quizzes.
- **Quiz Questions**: Manage multiple question types (MCQs, Short answer).
- **Timed Quizzes**: Includes a timer that auto-submits answers when time runs out.
- **Responsive Design**: Mobile-friendly and accessible UI.
- **REST API**: Fully documented endpoints for CRUD operations.

---

## Technologies Used

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **Database**: PostgreSQL (for structured data), Redis (for session management and caching)
- **Authentication**: JWT (stateless) and session-based authentication
- **Hosting**: AWS
- **Version Control**: Git & GitHub

---

## Architecture Overview

The application follows a modular MVC (Model-View-Controller) architecture:

1. **Frontend**:

   - Dynamic HTML/CSS and JavaScript handle the user interface.
   - Consistent UI/UX with a purple theme.

2. **Backend**:

   - Flask manages API routing and business logic.
   - JWT ensures secure communication for REST API authentication.

3. **Database**:

   - PostgreSQL stores structured data (users, quizzes, questions, and results).
   - Redis handles session caching for performance optimization.

4. **APIs**:
   - RESTful APIs expose quiz and user data functionalities.

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis Server
- Git

### Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/emmanueldev247/quizzen.git
   cd quizzen
   ```

2. **Set up a Virtual Environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory with the following:

   ```env
   FLASK_ENV=development
   JWT_SECRET_KEY=your_secret_key
   SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost/quizzen
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   REDIS_DB1=1

   MAIL_SERVER=your-mail-server
   MAIL_PORT=mail-port
   MAIL_USE_TLS=True
   MAIL_USE_SSL=False
   MAIL_USERNAME=mail-username
   MAIL_PASSWORD=mail-password
   MAIL_DEFAULT_SENDER=mail-username
   RECEIVER_EMAIL=mail-receiver

   GOOGLE_CLIENT_ID=google-client-id
   GOOGLE_CLIENT_SECRETgoogle-client-secret

   UPLOAD_FOLDER=./uploads
   ```

5. **Initialize the Database**:
```bash
flask db upgrade
````

6. **Start Redis Server**:

   ```bash
   redis-server
   ```

7. **Run the Application**:
   ```bash
   flask run
   ```

---

## Usage Guidelines

1. **Accessing the App**:

   - Visit `http://127.0.0.1:5000` in your browser.

2. **User Roles**:

   - **Students**: Take quizzes and track progress.
   - **Teachers**: Create and manage quizzes.

3. **Creating Quizzes**:

   - Login with your teacher account.
   - Navigate to the "Create Quiz" section.
   - Add questions and set time limits.

4. **Taking Quizzes**:
   - Select a quiz from the dashboard.
   - Complete within the allotted time to save progress.

---

## API Endpoints

### Authentication

- **POST /api/auth/signup**: Create a new user.
- **POST /api/auth/login**: Authenticate a user and return a JWT.

### Quizzes

- **GET /api/quizzes**: Get all quizzes.
- **GET /api/quizzes/:id**: Retrieve a specific quiz (if public).
- **POST /api/quizzes**: Create a new quiz (Teacher only).
- **PUT /api/quizzes/:id**: Update a quiz (Teacher only).
- **DELETE /api/quizzes/:id**: Delete a quiz (Teacher only).

### Questions

- **GET /api/quizzes/:id/questions**: Get all questions in a quiz.
- **POST /api/quizzes/:id/questions**: Add a question to a quiz (Teacher only).
- **DELETE /api/questions/:id**: Delete a question (Teacher only).

---

## Contributing

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add new feature"
   ```
4. Push to your branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

Happy Quizzing! 🎉
