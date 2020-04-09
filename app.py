import os, flask
from requests import *
from flask_session import Session
from flask_socketio import SocketIO, emit

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

players = []
full = False
mazo = []
for i in range(10):
    for k in ['b', 'c', 'e', 'o']:
        mazo.append(str(i+1)+'k')


@app.route("/")
def index():
    return flask.render_template('index.html')

@socketio.on('connect')
def connect():
    players_dct = {k:v for k,v in enumerate(players)}
    emit('players_update', {'players':players_dct, 'full':full})

@socketio.on('add_player')
def add_player(data):
    if data['new_player'].capitalize() in players:
        emit('name_taken')
        socketio.sleep(0)
    else:
        new_player = data['new_player'].capitalize()
        players.append(new_player)
        full = (len(players)==4)
        players_dct = {k:v for k,v in enumerate(players)}
        emit('welcome', {'player':new_player}, broadcast=False)
        socketio.sleep(0)
        emit('players_update', {'players':players_dct, 'full':full}, broadcast=True)

@socketio.on('player_left')
def player_left(data):
    players.remove(data['player'])
    full = (len(players)==4)
    players_dct = {k:v for k,v in enumerate(players)}
    emit('players_update', {'players':players_dct, 'full':full}, broadcast=True)
