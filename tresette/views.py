import os, flask, random, datetime, math
from flask_socketio import emit
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, logout_user
from operator import itemgetter
from tresette import app, socketio
from tresette.models import *

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

@app.route('/user')
def user():
    won = Game.count_documents({
        '$or': [
            {'$or': [
                {'teams.teamA.player1.username':current_user.username},
                {'teams.teamA.player2.username':current_user.username}
            ],
            'teams.teamA.winner':True},
            {'$or': [
                {'teams.teamB.player1.username':current_user.username},
                {'teams.teamB.player2.username':current_user.username}
            ],
            'teams.teamB.winner':True}
        ]
    })
    lost = Game.count_documents({
        '$or': [
            {'$or': [
                {'teams.teamA.player1.username':current_user.username},
                {'teams.teamA.player2.username':current_user.username}
            ],
            'teams.teamB.winner':True},
            {'$or': [
                {'teams.teamB.player1.username':current_user.username},
                {'teams.teamB.player2.username':current_user.username}
            ],
            'teams.teamA.winner':True}
        ]
    })
    games = Game.find({'$or': [
        {'teams.teamA.player1.username':current_user.username},
        {'teams.teamA.player2.username':current_user.username},
        {'teams.teamB.player1.username':current_user.username},
        {'teams.teamB.player2.username':current_user.username}
        ]})

    data = {'played':games.count(), 'won':won, 'lost':lost, 'games': games}
    return flask.render_template('user.html', data=data)

@app.route('/juego')
def main():
    if current_user.is_anonymous:
        return flask.redirect(flask.url_for('login'))
    else:
        return flask.render_template('main.html')

@socketio.on('connected')
def connect():
    player_data = game.find_player(current_user.username)
    if player_data != None:
        emit('player_data', player_data)
        socketio.sleep(0)
    if game.start != None:
        emit('game_starts', game.dump())
        for card in open_round:
            socketio.sleep(0)
            card_data = {'username': game.teams[card[2]][card[3]]['username'], 'card': [card[0], card[1]], 'current_player': game.current_player}
            emit('card_played', card_data)
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
    teams = game.teams
    open_round.append([data['number'], data['suit'], data['team'], data['player']])
    card_data = {'username': teams[data['team']][data['player']]['username'], 'card': [data['number'], data['suit']]}
    teams[data['team']][data['player']]['hand'].remove([data['number'], data['suit']])
    game.teams = teams
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
            teams['teamA']['score'] = math.floor(teams['teamA']['score']/3)
            teams['teamB']['score'] = math.floor(teams['teamB']['score']/3)
            if teams['teamA']['score']>teams['teamB']['score']:
                teams['teamA']['winner'] = True
                card_data['winner'] = {'team': 'teamA', 'players': [teams['teamA']['player1']['username'], teams['teamA']['player2']['username']], 'score':[teams['teamA']['score'], teams['teamB']['score']]}
            else:
                teams['teamB']['winner'] = True
                card_data['winner'] = {'team': 'teamB', 'players': [teams['teamB']['player1']['username'], teams['teamB']['player2']['username']], 'score':[teams['teamB']['score'], teams['teamA']['score']]}
            game.teams = teams
            game.current_player = None
            game.end = datetime.datetime.now()
            game.commit()
            emit('game_over', card_data, broadcast=True)
            del teams
            game = Game()

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
