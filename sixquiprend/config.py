from sixquiprend.sixquiprend import app
import os

# Load default config and override config from an environment variable
app.config.update(dict(
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    DATABASE_USER='sixquiprend',
    DATABASE_PASSWORD='sixquiprend',
    DATABASE_HOST='localhost',
    DATABASE_NAME='sixquiprend',
    SECRET_KEY='development key',
    ADMIN_USERNAME=os.environ.get('ADMIN_USER', 'admin'),
    ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD', 'admin'),
    ALLOW_REGISTER_USERS=os.environ.get('ALLOW_REGISTER_USERS', 'True') == 'True',
    ACTIVATE_ALL_USERS=os.environ.get('ACTIVATE_ALL_USERS', 'True') == 'True',
    BOT_NAMES=['Azrael','Valdamar','Lüdwig','Seelöwe','Gallù'],
    HAND_SIZE=10,
    BOARD_SIZE=4,
    MAX_PLAYER_NUMBER=6,
    COLUMN_CARD_SIZE=5,
    MAX_CARD_NUMBER=104
))
app.config.from_envvar('SIXQUIPREND_SETTINGS', silent=True)
db_path = app.config['DATABASE_USER'] + ':' + app.config['DATABASE_PASSWORD']
db_path += '@' + app.config['DATABASE_HOST'] + '/' + app.config['DATABASE_NAME']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://' + db_path)
