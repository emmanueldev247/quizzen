* SETUP & INSTALLATION GUIDE

** To install Postgre SQL
```
sudo apt update
sudo apt upgrade -y
sudo apt install postgresql postgresql-contrib -y
sudo service postgresql status
```

** To install Redis
```
sudo apt install redis
```

** To install dependencies
> pip install flask flask-sqlalchemy flask-restful flask-jwt-extended flask-mail redis psycopg2-binary

## To run the app in development or production mode, set the FLASK_ENV environment variable:
> export FLASK_ENV=development
# or
> export FLASK_ENV=production