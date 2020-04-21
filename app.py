import os, flask, random, datetime
from pymongo import MongoClient
from umongo import Instance, Document, fields, validate
from flask_socketio import SocketIO, emit
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'vivaperoncarajo'
socketio = SocketIO(app)
login = LoginManager(app)
db = MongoClient().tresette
instance = Instance(db)

class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Mandale cumbia')
    def validate_username(self, username):
        user = User.find_one({'username':username.data})
        if user is not None:
            raise ValidationError('Te primerearon')

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Acordate')
    submit = SubmitField('Mandale cumbia')

@instance.register
class User(UserMixin, Document):
    username = fields.StrField(required=True, attribute='_id')
    password_hash = fields.StrField(required=True)
    def get_id(self):
        return self.username

@instance.register
class Game(Document):
    id = fields.ObjectIdField()
    teams = fields.DictField(default=\
    { 'teamA': {'player1': {'username': None, 'hand': []}, \
                'player2': {'username': None, 'hand': []}, \
                'full': False, 'score': 0, 'winner': False}, \
      'teamA': {'player1': {'username': None, 'hand': []}, \
                'player2': {'username': None, 'hand': []}, \
                'full': False, 'score': 0, 'winner': False}})
    full = fields.BoolField(default=False)
    start = fields.DateTimeField()
    end = fields.DateTimeField()
    players = property(get_players)

    def get_players(self):
        players = []
        for t in ['teamA','teamB']:
            for p in ['player1', 'player2']:
                players.append(self.teams[t][p]['username'])
        return players



    def add_player(self, username, team):
        if username in self.get_players():
            find_player(self, username)
        else:
            if self.full:
                return None
            else:
                if self.teams[team]['player1']['username'] == None:
                    self.teams[team]['player1']['username'] = username
                    return {'team': team, 'player': 'player1'}
                else:
                    self.teams[team]['player2']['username'] = username
                    return {'team': team, 'player': 'player2'}
                    self.teams[team]['full'] = True
                    if self.teams['teamA']['full'] and self['teams']['teamB']['full']:
                        self['full'] = True

    def del_player(self, team, player):
        if player == 'player1':
            self.teams[team][player]['username'] = self.teams[team]['player2']['username']
            self.teams[team]['full'] = False
        self.teams[team]['player2']['username'] = None

    def find_player(self, username):
        if username in self.players:
            for team in ['teamA', 'teamB']:
                for player in ['player1', 'player2']:
                    if self.teams[team][player]['username'] == username:
                        return {'team': team, 'player': player}
                        break

    def deal(self):
        open_deck = deck
        for t in ['teamA','teamB']:
            for p in ['player1', 'player2']:
                for i in range(10):
                    card = random.choice(open_deck)
                    open_deck.remove(card)
                    self.teams[t][p]['hand'].append(card))

@login.user_loader
def load_user(username):
    return User.find_one({'username': username})

@app.before_first_request
def before_first_request_func():
    global open_game
    open_game = Game()
    open_game.commit()
    global deck
    deck = []
    for n in range(10):
        for p in ['basto', 'copa', 'espada', 'oro']:
            deck.append([n+1 , p])
    print('Before')


@app.route("/test")
def gametest():
    return flask.render_template('gametest.html')

@app.route("/", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return flask.redirect(flask.url_for('main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_one({'username': form.username.data.capitalize()})
        if user is None or not check_password_hash(user['password_hash'], form.password.data):
            flask.flash('Si estás registrado, flasheaste, si no, registrate')
            return flask.redirect(flask.url_for('login'))
        login_user(user, remember= False)
        return flask.redirect(flask.url_for('main'))
    return flask.render_template('login.html', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return flask.redirect(flask.url_for('login'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(flask.url_for('main'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.find_one({'username':form.username.data.capitalize()}) is not None:
            flask.flash('Te primerearon el nombre')
            return flask.render_template('register.html', form=form)
        user = User()
        user.username = form.username.data.capitalize()
        user.password_hash = generate_password_hash(form.password.data)
        user.commit()
        return flask.redirect(flask.url_for('login'))
    return flask.render_template('register.html', form=form)

@app.route('/juego')
def main():
    if current_user.is_anonymous:
        return flask.redirect(flask.url_for('login'))
    else:
        return flask.render_template('main.html')

@socketio.on('connect')
def connect():
    player_data = open_game.find_player(current_user.username)
    if player_data != None:
        emit('player_data', player_data)
        socketio.sleep(0)
    emit('players_update', open_game.dump())

@socketio.on('player_enter')
def player_enter(data):
    player_data = open_game.add_player(current_user.username, data.team)
    open_game.commit()
    if data == None:
        emit('game_full')
    else:
        emit('player_data', player_data)
        socketio.sleep(0)
        if open_game.full:
            open_game.deal()
            open_game.commit()
            emit('game_starts', open_game.dump(), broadcast=True)
        else:
            emit('players_update', open_game.dump(), broadcast=True)

@socketio.on('player_left')
def player_left(player_data):
    open_game.del_player(player_data.team, player_data.player)
    open_game.commit()
    emit('players_update', open_game.dump(), broadcast=True)
