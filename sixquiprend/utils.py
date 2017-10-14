from passlib.hash import bcrypt
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sixquiprend.models.card import Card
from sixquiprend.models.user import User
from sixquiprend.sixquiprend import app, db
import psycopg2

def create_db():
    try:
        con = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
    except:
        print('Database missing, creating it.')
        # Not needed on heroku as database comes with a table
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
    add_cards()
    add_admin()
    add_bots()

def add_cards():
    if Card.query.count() == 0:
        for i in range(1, app.config['MAX_CARD_NUMBER'] + 1):
            cow_value = 0
            if i % 10 == 5:
                cow_value += 2
            if i % 10 == 0:
                cow_value += 3
            if i % 11 == 0:
                cow_value += 5
            if cow_value == 0:
                cow_value = 1
            card = Card(number=i, cow_value=cow_value)
            db.session.add(card)
        db.session.commit()
        print('Added cards')

def add_admin():
    if not User.query.filter(User.username == app.config['ADMIN_USERNAME']).first():
        admin = User(username=app.config['ADMIN_USERNAME'],
                password=bcrypt.hash(app.config['ADMIN_PASSWORD']),
                urole=User.ADMIN_ROLE, active=True)
        db.session.add(admin)
        db.session.commit()
        print('Added admin user')

def add_bots():
    for bot_name in app.config['BOT_NAMES']:
        if not User.query.filter(User.username == bot_name).first():
            # password is irrelevant, as bots cannot login
            admin = User(username=bot_name,
                    password=bcrypt.hash(bot_name),
                    urole=User.BOT_ROLE, active=True)
            db.session.add(admin)
            db.session.commit()
            print('Added bot', bot_name)

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
    db.reflect()
    db.drop_all()
    print('Dropped the tables.')


