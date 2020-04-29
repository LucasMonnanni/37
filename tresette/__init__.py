import flask
from pymongo import MongoClient
from umongo import Instance
from flask_socketio import SocketIO
from flask_login import LoginManager

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'vivaperoncarajo'
socketio = SocketIO(app)
login = LoginManager(app)
db = MongoClient().tresette
instance = Instance(db)

import tresette.views
import tresette.models
