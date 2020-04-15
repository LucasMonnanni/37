import os, flask, random
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
    players = fields.ListField(fields.StrField())
    hands = fields.DictField()
    winner = fields.StrField()
    start = fields.DateTimeField()
    end = fields.DateTimeField()
    full = fields.BoolField(default=False)
    def add_player(self, player):
        if player in open_players:
            pass
        else:
            open_players.append(player)
            self.players = open_players
            self.hands[player]=[]
        if len(self.players) == n_players:
            self.full = True
        else:
            self.full = False
    def del_player(self, player):
        self.players.remove(player)
        self.full = False

@login.user_loader
def load_user(username):
    return User.find_one({'username': username})

@app.before_first_request
def before_first_request_func():
    global n_players
    n_players = 2
    global open_players
    open_players = []
    global open_game
    open_game = Game()
    open_game.players = open_players
    global deck
    deck = []
    for i in range(10):
        for p in ['basto', 'copa', 'espada', 'oro']:
            deck.append((i,p))
    print('Before')

def assign_game(player):
    if open_game.full:
        return None
    else:
        open_game.add_player(player)
        open_game.commit()
        return open_game


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
        login_user(user, remember=form.remember_me.data)
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
    if current_user.username in open_players:
        pass
    else:
        game = assign_game(current_user.username)
        if game == None:
            emit('game_full')
        else:
            emit('players_update', game.dump(), broadcast=True)
            socketio.sleep(0)
            if game.full:
                open_deck = deck
                for player in open_players:
                    for i in range(10):
                        card = random.choice(open_deck)
                        open_deck.remove(card)
                        game.hands[player].append(card)
                        game.commit()
                emit('game_starts', game.dump(), broadcast=True)

@socketio.on('player_left')
def player_left(data):
    game = Game.find_one({'id':data.game_id})
    game.del_player(current_user.username)
    emit('players_update', game.dump(), broadcast=True)
