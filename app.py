import os, flask
from flask_pymongo import PyMongo
# from flask_socketio import SocketIO, emit
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'vivaperoncarajo'
# socketio = SocketIO(app)
login = LoginManager(app)
db = PyMongo(app, "mongodb://localhost:27017/tresette").db


class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Mandale cumbia')
    def validate_username(self, username):
        user = db.users.find_one({'username':username.data})
        if user is not None:
            raise ValidationError('Te primerearon')

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Acordate')
    submit = SubmitField('Mandale cumbia')

# players = []
# full = False
# mazo = []
# for i in range(10):
#     for k in ['b', 'c', 'e', 'o']:
#         mazo.append(str(i+1)+'k')

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route("/", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.users.find_one({'username': form.username.data})
        if user is None or not check_password_hash(user['password_hash'], form.password.data):
            flash('Si estás registrado, flasheaste, si no, registrate')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main'))
    return flask.render_template('login.html', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = {'username': form.username.data, 'password_hash': generate_password_hash(form.password.data)}
        db.users.insert_one(user)
        return flask.redirect(url_for('login'))
    return flask.render_template('register.html', form=form)

@app.route('/juego')
def main():
    if current_user.is_anonymous:
        return redirect(url_for('login'))
    else:
        return "Adentro!"


# @socketio.on('connect')
# def connect():
#     players_dct = {k:v for k,v in enumerate(players)}
#     emit('players_update', {'players':players_dct, 'full':full})
#
# @socketio.on('add_player')
# def add_player(data):
#     if data['new_player'].capitalize() in players:
#         emit('name_taken')
#         socketio.sleep(0)
#     else:
#         new_player = data['new_player'].capitalize()
#         players.append(new_player)
#         full = (len(players)==4)
#         players_dct = {k:v for k,v in enumerate(players)}
#         emit('welcome', {'player':new_player}, broadcast=False)
#         socketio.sleep(0)
#         emit('players_update', {'players':players_dct, 'full':full}, broadcast=True)
#
# @socketio.on('player_left')
# def player_left(data):
#     players.remove(data['player'])
#     full = (len(players)==4)
#     players_dct = {k:v for k,v in enumerate(players)}
#     emit('players_update', {'players':players_dct, 'full':full}, broadcast=True)
