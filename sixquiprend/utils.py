import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from passlib.hash import bcrypt
from sixquiprend.sixquiprend import app, db
from sixquiprend.models import User, Card

def create_db():
    try:
        con = psycopg2.connect(dbname=app.config['DATABASE_NAME'],
                user=app.config['DATABASE_USER'],
                password=app.config['DATABASE_PASSWORD'],
                host=app.config['DATABASE_HOST'])
    except:
        print('Database missing, creating it.')
        con = psycopg2.connect(dbname='postgres',
                user=app.config['DATABASE_USER'],
                password=app.config['DATABASE_PASSWORD'],
                host=app.config['DATABASE_HOST'])
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        cur.execute('CREATE DATABASE ' + app.config['DATABASE_NAME'])
        cur.close()
        con.close()

def populate_db():
    if not User.query.filter(User.username == app.config['USERNAME']).first():
        user = User(username=app.config['USERNAME'],
                password=bcrypt.encrypt(app.config['PASSWORD']))
        db.session.add(user)
        db.session.commit()
        print('Added admin user')
    if Card.query.count() == 0:
        for i in range(1, 105):
            card = Card(number=i, cow_value=2*i)
            db.session.add(card)
        db.session.commit()
        print('Added cards')

@app.cli.command('create_db')
def create_db_command():
    create_db()
    print('Created the database.')

@app.cli.command('populate_db')
def populate_db_command():
    populate_db()
    print('Created the database.')

@app.cli.command('init_db')
def init_db_command():
    db.create_all()
    populate_db()
    print('Initialized the database.')

@app.cli.command('drop_tables')
def drop_tables_command():
    db.drop_all()
    print('Dropped the tables.')


