# all the imports
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter

app = Flask(__name__)
app.config.from_object(__name__) # load config from this file , sixquiprend.py
USERNAME = 'admin'
PASSWORD = 'admin'

# Load default config and override config from an environment variable
app.config.update(dict(
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    DATABASE_USER='sixquiprend',
    DATABASE_PASSWORD='sixquiprend',
    DATABASE_HOST='localhost',
    DATABASE_NAME='sixquiprend',
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    USER_ENABLE_EMAIL=False,
    USER_ENABLE_CONFIRM_EMAIL=False,
))
app.config.from_envvar('SIXQUIPREND_SETTINGS', silent=True)
db_path = app.config['DATABASE_USER'] + ':' + app.config['DATABASE_PASSWORD']
db_path += '@' + app.config['DATABASE_HOST'] + '/' + app.config['DATABASE_NAME']
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + db_path

db = SQLAlchemy(app)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    text = db.Column(db.String(250), nullable=False)

    def __init__(self, title, text):
        self.title = title
        self.text = text

    def __repr__(self):
        return '<Entry %r>' % self.title

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    # User authentication information
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')

    def is_active(self):
        return True

# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app)     # Initialize Flask-User

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

@app.cli.command('create_db')
def create_db_command():
    create_db()
    print('Created the database.')

@app.cli.command('init_db')
def init_db_command():
    db.create_all()
    if not User.query.filter(User.username == USERNAME).first():
        user = User(username=USERNAME,
                password=app.user_manager.password_crypt_context.hash(PASSWORD))
        db.session.add(user)
        db.session.commit()
    print('Initialized the database.')

@app.cli.command('drop_tables')
def drop_tables_command():
    db.drop_all()
    print('Dropped the tables.')

@app.route('/')
def show_entries():
    entries = Entry.query.all()
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
@login_required
def add_entry():
    print('Add')
    new_entry = Entry(request.form['title'], request.form['text'])
    db.session.add(new_entry)
    db.session.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))
