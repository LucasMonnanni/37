from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from umongo import Document, fields, validate
from wtforms.validators import DataRequired
from flask_login import UserMixin
from tresette import instance, login
import random, datetime

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
    two = fields.BoolField(default=False)
    id = fields.ObjectIdField()
    name = fields.StrField()
    teams = fields.DictField()
    maker = fields.StrField()
    first_player = fields.DictField(default={'team': None, 'player': None, 'username':None})
    current_player = fields.DictField(default={'team': None, 'player': None, 'username':None, 'n': None})
    full = fields.BoolField(default=False)
    start = fields.DateTimeField()
    end = fields.DateTimeField()
    current_round = fields.IntegerField(default=1)
    open_round = fields.ListField(fields.ListField(fields.StrField), default=[])

    def get_players(self):
        if self.two:
            return [self.teams['player1']['username'],self.teams['player2']['username']]
        else:
            players = []
            for t in ['teamA','teamB']:
                for p in ['player1', 'player2']:
                    players.append(self.teams[t][p]['username'])
            return players
    players = property(get_players)

    def init_teams(self):
        if self.two:
            self.teams = {'player1': {\
                            'username': None, 'hand': [],\
                            'hand_score': 0, 'score': 0, 'winner': False}, \
                        'player2': {\
                            'username': None, 'hand': [],\
                            'hand_score': 0, 'score': 0, 'winner': False},\
                        'rest':[]}
        else:
            self.teams = {'teamA': {'player1': {'username': None, 'hand': []}, \
                        'player2': {'username': None, 'hand': []}, \
                        'full': False, 'hand_score': 0, 'score': 0, 'winner': False}, \
              'teamB': {'player1': {'username': None, 'hand': []}, \
                        'player2': {'username': None, 'hand': []}, \
                        'full': False, 'hand_score': 0, 'score': 0, 'winner': False}}

    def find_player(self, username):
        if self.two:
            for player in ['player1', 'player2']:
                if self.teams[player]['username'] == username:
                    return {'team': player, 'player': player}
        else:
            for team in ['teamA', 'teamB']:
                for player in ['player1', 'player2']:
                    if self.teams[team][player]['username'] == username:
                        return {'team': team, 'player': player}

    def add_player(self, username, team):
        """Add player to chosen team (in 4)"""
        if username in self.players:
            return self.find_player(username)
        else:
            if self.full:
                return None
            else:
                if self.two:
                    if self.teams['player1']['username'] == None:
                        teams = self.teams
                        teams['player1']['username'] = username
                        self.teams = teams
                        return {'team': 'player1', 'player': 'player1'}
                    if self.teams['player2']['username'] == None:
                        teams = self.teams
                        teams['player2']['username'] = username
                        self.teams = teams
                        self.full = True
                        return {'team': 'player2','player': 'player2'}
                else:
                    if self.teams[team]['player1']['username'] == None:
                        teams = self.teams
                        teams[team]['player1']['username'] = username
                        self.teams = teams
                        return {'team': team, 'player': 'player1'}
                    if self.teams[team]['player2']['username'] == None:
                        teams = self.teams
                        teams[team]['player2']['username'] = username
                        teams[team]['full'] = True
                        self.teams = teams
                        if self.teams['teamA']['full'] and self.teams['teamB']['full']:
                            self.full = True
                        return {'team': team, 'player': 'player2'}

    def del_player(self, team, player):
        if self.two:
            if player == 'player1':
                self.teams['player1']['username'] = None
            else:
                self.teams['player2']['username'] = None
        else:
            teams = self.teams
            if player == 'player1':
                self.teams[team][player]['username'] = self.teams[team]['player2']['username']
                self.teams[team]['full'] = False
            teams[team]['player2']['username'] = None
            self.teams = teams

    def deal(self):
        deck = []
        order = ['3', '2', '1', '10', '9', '8', '7', '6', '5', '4']
        for n in range(10):
            for p in ['basto', 'copa', 'espada', 'oro']:
                deck.append([str(n+1) , p])
        teams = self.teams
        if self.two:
            rest = []
            for p in ['player1', 'player2']:
                hand = []
                for i in range(10):
                    card = random.choice(deck)
                    deck.remove(card)
                    hand.append(card)
                    card = random.choice(deck)
                    deck.remove(card)
                    rest.append(card)
                hand.sort(key=lambda c: order.index(c[0]))
                hand.sort(key=lambda c: c[1])
                teams[p]['hand'] = hand
            teams['rest'] = rest
            self.teams = teams
        else:
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

    def draw(self):
        """Draw a card each and return {player: card x2} or None"""
        if self.two:
            teams = self.teams
            order = ['3', '2', '1', '10', '9', '8', '7', '6', '5', '4']
            if len(teams['rest'])>0:
                drawn = {}
                for p in ['player1', 'player2']:
                    card = random.choice(teams['rest'])
                    teams['rest'].remove(card)
                    teams[p]['hand'].append(card)
                    drawn[p] = card
                    teams[p]['hand'].sort(key=lambda c: order.index(c[0]))
                    teams[p]['hand'].sort(key=lambda c: c[1])
                self.teams = teams
                return drawn
        return None

    def next_player(self):
        next = {}
        l = ['player1', 'player2']
        if self.two:
            next['player'] = l[l.index(self.current_player['player'])-1]
            next['team'] = next['player']
            next['username'] = self.teams[next['player']]['username']
            next['n'] = self.current_player['n']+1
            self.current_player = next
        else:
            if self.current_player['team'] == 'teamA':
                next['team'] = 'teamB'
                next['player'] = self.current_player['player']
            else:
                next['team'] = 'teamA'
                next['player'] = l[l.index(self.current_player['player'])-1]
            next['username'] = self.teams[next['team']][next['player']]['username']
            next['n'] = self.current_player['n']+1
            self.current_player = next

    def next_first_player(self):
        next = {}
        l = ['player1', 'player2']
        if self.two:
            next['player'] = l[l.index(self.first_player['player'])-1]
            next['team'] = next['player']
            next['username'] = self.teams[next['player']]['username']
            self.first_player = next
            next['n'] = 1
            self.current_player = next
        else:
            if self.first_player['team'] == 'teamA':
                next['team'] = 'teamB'
                next['player'] = self.first_player['player']
            else:
                next['team'] = 'teamA'
                next['player'] = l[l.index(self.first_player['player'])-1]
            next['username'] = self.teams[next['team']][next['player']]['username']
            self.first_player = next
            next['n'] = 1
            self.current_player = next

    def get_card(self, data):
        """Add card to open_round and return card_data = {username:str, card:[number, suit]}"""
        teams = self.teams
        open_round = self.open_round
        if self.two:
            open_round.append([data['number'], data['suit'], data['player']])
            card_data = {'username': teams[data['player']]['username'], 'card': [data['number'], data['suit']]}
            teams[data['player']]['hand'].remove([data['number'], data['suit']])
        else:
            open_round.append([data['number'], data['suit'], data['team'], data['player']])
            card_data = {'username': teams[data['team']][data['player']]['username'], 'card': [data['number'], data['suit']]}
            teams[data['team']][data['player']]['hand'].remove([data['number'], data['suit']])
        self.open_round = open_round
        self.teams = teams
        return card_data

    def round_over(self):
        """"Check if round is over"""
        if self.two:
            if self.current_player['n']==2:
                return True
        else:
            if self.current_player['n']==4:
                return True
        return False

    def hand_over(self):
        """Check if hand is over.
            Return Boolean"""
        if self.two:
            if self.current_round == 20:
                return True
        else:
            if self.current_round == 10:
                return True
        return False

    def game_over(self):
        """Check if game is over, if so, update winner var of team/player
        and return Boolean"""
        if self.two:
            if self.teams['player1']['score'] != self.teams['player2']['score'] and \
                (self.teams['player1']['score']>=21 or self.teams['player2']['score']>= 21):
                teams = self.teams
                if teams['player1']['score']>teams['player2']['score']:
                    teams['player1']['winner'] = True
                else:
                    teams['player2']['winner'] = True
                self.teams = teams
                self.end = datetime.datetime.now()
                return True
        else:
            if self.teams['teamA']['score'] != self.teams['teamB']['score'] and \
                (self.teams['teamA']['score']>=21 or self.teams['teamA']['score']>= 21):
                teams = self.teams
                if teams['teamA']['score']>teams['teamB']['score']:
                    teams['teamA']['winner'] = True
                else:
                    teams['teamB']['winner'] = True
                self.teams = teams
                self.end = datetime.datetime.now()
                return True
        return False

    def score_round(self):
        """Figure out who won, add score and change current_player.
        Return hand_score = {team:score x2, winner: team/player} or None """
        value = {'1':3, '2':1, '3':1, '10':1, '9':1, '8':1, '7':0, '6':0, '5':0, '4':0}
        order = ['3', '2', '1', '10', '9', '8', '7', '6', '5', '4']
        champ = self.open_round[0]
        score = value[champ[0]]
        for card in self.open_round[1:]:
            score += value[card[0]]
            if card[1]==champ[1] and order.index(card[0])<order.index(champ[0]):
                champ = card
        self.open_round = []
        teams = self.teams
        teams[champ[2]]['hand_score'] += score
        if self.hand_over():
            hand_score= {}
            teams[champ[2]]['hand_score'] += 3
            if self.two:
                if teams['player1']['hand_score']>teams['player2']['hand_score']:
                    hand_score['winner'] = 'player1'
                else:
                    hand_score['winner'] = 'player2'
                for key in ['player1', 'player2']:
                    teams[key]['hand_score'] = teams[key]['hand_score'] // 3
                    teams[key]['score'] += teams[key]['hand_score']
                    hand_score[key] = teams[key]['hand_score']
                    teams[key]['hand_score'] = 0
            else:
                if teams['teamA']['hand_score']>teams['teamB']['hand_score']:
                    hand_score['winner'] = 'teamA'
                else:
                    hand_score['winner'] = 'teamB'
                for key in ['teamA', 'teamB']:
                    teams[key]['hand_score'] = teams[key]['hand_score'] // 3
                    teams[key]['score'] += teams[key]['hand_score']
                    hand_score[key] = teams[key]['hand_score']
                    teams[key]['hand_score'] = 0
            self.teams = teams
            return hand_score
        else:
            if self.two:
                self.current_player = {'team': champ[2], 'player': champ[2], 'username': self.teams[champ[2]]['username'], 'n': 1}
            else:
                self.current_player = {'team': champ[2], 'player': champ[3], 'username': self.teams[champ[2]][champ[3]]['username'], 'n': 1}
            self.teams = teams

@login.user_loader
def load_user(username):
    return User.find_one({'username': username})
