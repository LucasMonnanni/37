import os, flask
# from flask_socketio import SocketIO, emit
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'vivaperoncarajo'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
# socketio = SocketIO(app)

db = SQLAlchemy(app)

login = LoginManager(app)

class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Mandale cumbia')
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Te primerearon')

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Acordate')
    submit = SubmitField('Mandale cumbia')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
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
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
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
