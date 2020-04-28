import os, flask, random, datetime, math
from pymongo import MongoClient
from umongo import Instance, Document, fields, validate
from flask_socketio import SocketIO, emit
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from operator import itemgetter

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
      'teamB': {'player1': {'username': None, 'hand': []}, \
                'player2': {'username': None, 'hand': []}, \
                'full': False, 'score': 0, 'winner': False}})
    current_player = fields.DictField(default={'team': None, 'player': None, 'username':None, 'n': None})
    full = fields.BoolField(default=False)
    start = fields.DateTimeField()
    end = fields.DateTimeField()
    current_round = fields.IntegerField(default=1)


    def get_players(self):
        players = []
        for t in ['teamA','teamB']:
            for p in ['player1', 'player2']:
                players.append(self.teams[t][p]['username'])
        return players

    players = property(get_players)

    def find_player(self, username):
            for team in ['teamA', 'teamB']:
                for player in ['player1', 'player2']:
                    if self.teams[team][player]['username'] == username:
                        return {'team': team, 'player': player}

    def add_player(self, username, team):
        if username in self.players:
            find_player(self, username)
        else:
            if self.full:
                return None
            else:
                if self.teams[team]['player1']['username'] == None:
                    teams = self.teams
                    teams[team]['player1']['username'] = username
                    self.teams = teams
                    self.commit()
                    return {'team': team, 'player': 'player1'}
                else:
                    teams = self.teams
                    teams[team]['player2']['username'] = username
                    teams[team]['full'] = True
                    self.teams = teams
                    self.commit()
                    if self.teams['teamA']['full'] and self.teams['teamB']['full']:
                        self.full = True
                    self.commit()
                    return {'team': team, 'player': 'player2'}

    def del_player(self, team, player):
        teams = self.teams
        if player == 'player1':
            self.teams[team][player]['username'] = self.teams[team]['player2']['username']
            self.teams[team]['full'] = False
        teams[team]['player2']['username'] = None
        self.teams = teams
        self.commit()

    def deal(self):
        open_deck = deck
        teams = self.teams
        for t in ['teamA','teamB']:
            for p in ['player1', 'player2']:
                hand = []
                for i in range(10):
                    card = random.choice(open_deck)
                    open_deck.remove(card)
                    hand.append(card)
                hand.sort(key=lambda c: order.index(c[0]))
                hand.sort(key=lambda c: c[1])
                teams[t][p]['hand'] = hand
        self.teams = teams
        self.commit()

    def next_player(self):
        next = {}
        l = ['player1', 'player2']
        if self.current_player['team'] == 'teamA':
            next['team'] = 'teamB'
            next['player'] = self.current_player['player']
        else:
            next['team'] = 'teamA'
            next['player'] = l[l.index(self.current_player['player'])-1]
        next['username'] = self.teams[next['team']][next['player']]['username']
        next['n'] = self.current_player['n']+1
        self.current_player = next

@login.user_loader
def load_user(username):
    return User.find_one({'username': username})

@app.before_first_request
def before_first_request_func():
    global order
    order = ['3', '2', '1', '10', '9', '8', '7', '6', '5', '4']
    global value
    value = {'1':3, '2':1, '3':1, '10':1, '9':1, '8':1, '7':0, '6':0, '5':0, '4':0}
    global game
    game = Game()
    game.commit()
    global open_round
    open_round = []
    global deck
    deck = []
    for n in range(10):
        for p in ['basto', 'copa', 'espada', 'oro']:
            deck.append([str(n+1) , p])
    global current_player
    global players_order
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

@socketio.on('connected')
def connect():
    global game
    if game.end != None:
        game = Game()
        game.commit()
    player_data = game.find_player(current_user.username)
    if player_data != None:
        emit('player_data', player_data)
        socketio.sleep(0)
    if game.start != None:
            emit('game_starts', game.dump())
    else:
            emit('players_update', game.dump())

@socketio.on('player_enter')
def player_enter(data):
    player_data = game.add_player(current_user.username, data['team'])
    if player_data == None:
        emit('game_full')
    else:
        emit('player_data', player_data)
        socketio.sleep(0)
        print('Seguimos..')
        if game.full:
            game.deal()
            current_player = {'team': random.choice(['teamA', 'teamB']), 'player': random.choice(['player1', 'player2']), 'n': 1}
            current_player['username'] = game.teams[current_player['team']][current_player['player']]['username']
            game.current_player = current_player
            game.start = datetime.datetime.now()
            game.commit()
            emit('game_starts', game.dump(), broadcast=True)
        else:
            emit('players_update', game.dump(), broadcast=True)

@socketio.on('player_left')
def player_left(player_data):
    game.del_player(player_data['team'], player_data['player'])
    game.commit()
    emit('players_update', game.dump(), broadcast=True)

@socketio.on('play_card')
def card_played(data):
    global open_round
    global game
    open_round.append([data['number'], data['suit'], data['team'], data['player']])
    card_data = {'username': game.teams[data['team']][data['player']]['username'], 'card': [data['number'], data['suit']]}
    if len(open_round) == 4:
        champ = open_round[0]
        score = value[champ[0]]
        for i in range(3):
            chall = open_round[i+1]
            score += value[chall[0]]
            if chall[1]==champ[1] and order.index(chall[0])<order.index(champ[0]):
                champ = chall
        open_round = []
        teams = game.teams
        teams[champ[2]]['score'] += score
        game.teams = teams
        game.commit()
        if game.current_round == 10:
            teams = game.teams
            teams[champ[2]]['score'] += 3
            if teams['teamA']['score']>teams['teamB']['score']:
                teams['teamA']['winner'] = True
                card_data['winner'] = {'team': 'teamA', 'players': [teams['teamA']['player1']['username'], teams['teamA']['player2']['username']], 'score':[math.floor(teams['teamA']['score']/3), math.floor(teams['teamB']['score']/3)]}
            else:
                teams['teamB']['winner'] = True
                card_data['winner'] = {'team': 'teamB', 'players': [teams['teamB']['player1']['username'], teams['teamB']['player2']['username']], 'score':[math.floor(teams['teamB']['score']/3), math.floor(teams['teamA']['score']/3)]}
            emit('game_over', card_data, broadcast=True)
            game.teams = teams
            game.end = datetime.datetime.now()
            game.commit()
        else:
            game.current_round += 1
            game.current_player = {'team': champ[2], 'player': champ[3], 'username': game.teams[champ[2]][champ[3]]['username'], 'n': 1}
            game.commit()
            card_data['current_player'] = game.current_player
            emit('new_round', card_data, broadcast = True)
    else:
        game.next_player()
        game.commit()
        card_data['current_player'] = game.current_player
        emit('card_played', card_data, broadcast = True)
