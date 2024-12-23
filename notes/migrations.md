* How to Set Up Flask-Migrate
Run the following commands to initialize Flask-Migrate and create migration files:

1. Export the Flask app environment variable:
```export FLASK_APP=app
```

2. Initialize migrations:

```
flask db init
```

3. Create a migration script for the current state of your models:

```flask db migrate -m "Initial migration"
```

4. Apply the migrations to the database:
```flask db upgrade
```

** Verify the Database
Check that the migrations created/altered the tables as needed