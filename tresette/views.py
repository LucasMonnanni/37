import os, flask, random, datetime
from flask_socketio import emit, join_room, leave_room
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, logout_user
from operator import itemgetter
from tresette import app, socketio
from tresette.models import *
from bson.objectid import ObjectId

@app.before_first_request
def before_first_request():
    global lobby
    lobby = []
    print('before')

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
        login_user(user, remember= True)
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
    join_room('lobby')
    lobby.append(current_user.username)
    games = Game.find({'end': None})
    emit('games_update', {'games':[game.dump() for game in games], 'lobby': lobby})
    emit('lobby_update', {'lobby': lobby}, broadcast = True)
@socketio.on('disconnect')
def disconnect():
    if current_user.username in lobby:
        lobby.remove(current_user.username)

@socketio.on('make_game')
def make_game(data):
        game = Game()
        game.name = data['name']
        if data['two']== 'true':
            game.two = True
        game.init_teams()
        game.commit()
        leave_room('lobby')
        lobby.remove(current_user.username)
        join_room(str(game.id))
        emit('players_update', game.dump())
        socketio.sleep(0)
        games = Game.find({'end': None})
        emit('games_update', {'games':[game.dump() for game in games], 'lobby':lobby}, room='lobby')

@socketio.on('join_game')
def join_game(data):
    game = Game.find_one({'id':ObjectId(data['id'])})
    player_data = game.find_player(current_user.username)
    leave_room('lobby')
    lobby.remove(current_user.username)
    join_room(data['id'])
    if game.start != None:
        if player_data != None:
            emit('player_data', player_data)
            socketio.sleep(0)
            emit('game_starts', game.dump())
            for card in game.open_round:
                socketio.sleep(0)
                if game.two:
                    card_data = {'username': game.teams[card[2]]['username'], 'card': [card[0], card[1]]}
                else:
                    card_data = {'username': game.teams[card[2]][card[3]]['username'], 'card': [card[0], card[1]]}
                data = game.dump()
                data.update({'card_data':card_data})
                emit('card_played', data)
        else:
            leave_room(data['id'])
            join_room('lobby')
            lobby.append(current_user.username)
            games = Game.find({'end': None})
            flask.flash('Si estás registrado, flasheaste, si no, registrate')
            emit('games_update', {'games':[game.dump() for game in games], 'lobby':lobby})
            emit('lobby_update', {'lobby': lobby}, broadcast = True)
    else:
        if player_data != None:
            emit('player_data', player_data)
            socketio.sleep(0)
        emit('players_update', game.dump())

@socketio.on('leave_game')
def leave_game(data):
    leave_room(data['id'])
    join_room('lobby')
    lobby.append(current_user.username)
    games = Game.find({'end': None})
    emit('games_update', {'games':[game.dump() for game in games], 'lobby': lobby})
    emit('lobby_update', {'lobby': lobby}, broadcast = True)

@socketio.on('message_sent')
def message(data):
    emit('message', {'username':current_user.username, 'message': data['message']}, room=data['id'])

@socketio.on('player_enter')
def player_enter(data):
    game = Game.find_one({'id':ObjectId(data['id'])})
    player_data = game.add_player(current_user.username, data['team'])
    if player_data == None:
        leave_room(data['id'])
        join_room('lobby')
        lobby.append(current_user.username)
        games = Game.find({'end': None})
        emit('games_update', {'games':[game.dump() for game in games], 'lobby': lobby})
    else:
        emit('player_data', player_data)
        socketio.sleep(0)
        if game.full:
            game.deal()
            if game.two:
                current_player = {'player': random.choice(['player1', 'player2'])}
                current_player['team'] = current_player['player']
                current_player['username'] = game.teams[current_player['player']]['username']
            else:
                current_player = {'team': random.choice(['teamA', 'teamB']), 'player': random.choice(['player1', 'player2'])}
                current_player['username'] = game.teams[current_player['team']][current_player['player']]['username']
            game.first_player = current_player
            current_player['n'] = 1
            game.current_player = current_player
            game.start = datetime.datetime.now()
            game.commit()
            emit('game_starts', game.dump(), room = str(game.id))
        else:
            game.commit()
            emit('players_update', game.dump(), room = str(game.id))

@socketio.on('player_left')
def player_left(player_data):
    game = Game.find_one({'id':ObjectId(player_data['id'])})
    game.del_player(player_data['team'], player_data['player'])
    game.commit()
    emit('players_update', game.dump(), room = player_data['id'])

@socketio.on('play_card')
def card_played(data):
    game = Game.find_one({'id':ObjectId(data['id'])})
    card_data = game.get_card(data)
    # card_data = {username:"", card: []}
    if game.round_over():
        if game.hand_over():
            hand_score = game.score_round()
            if game.game_over():
                data = game.dump()
                data.update({'card_data':card_data, 'hand_score':hand_score})
                emit('game_over', data, room = str(game.id))
                game.commit()
            else:
                game.deal()
                game.next_first_player()
                game.current_round = 1
                data = game.dump()
                data.update({'card_data':card_data, 'hand_score':hand_score})
                emit('hand_over', data, room = str(game.id))
                game.commit()
        else:
            game.score_round()
            drawn = game.draw()
            game.current_round += 1
            data = game.dump()
            data.update({'card_data':card_data, 'drawn':drawn})
            emit('new_round', data, room = str(game.id))
            game.commit()
    else:
        game.next_player()
        data = game.dump()
        data.update({'card_data':card_data})
        emit('card_played', data, room = str(game.id))
        game.commit()
