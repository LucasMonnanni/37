from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from umongo import Document, fields, validate
from wtforms.validators import DataRequired
from flask_login import UserMixin
from tresette import instance, login
import random

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
        deck = []
        order = ['3', '2', '1', '10', '9', '8', '7', '6', '5', '4']
        for n in range(10):
            for p in ['basto', 'copa', 'espada', 'oro']:
                deck.append([str(n+1) , p])
        teams = self.teams
        for t in ['teamA','teamB']:
            for p in ['player1', 'player2']:
                hand = []
                for i in range(10):
                    card = random.choice(deck)
                    deck.remove(card)
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
