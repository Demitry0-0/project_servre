from flask import Flask, render_template, request, make_response, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import reqparse, abort, Api, Resource
from werkzeug.utils import redirect
from data import db_session
from data.loginform import LoginForm
from data.registrform import RegisterForm
from data.users import User
from data.records import Records
import datetime

db_session.global_init("db/users.sqlite")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

'''api = Api(app)
# для списка объектов
api.add_resource(NewsListResource, '/api/v2/news')
api.add_resource(UsersListResource, '/api/v2/users')
api.add_resource(JobsListResource, '/api/v2/jobs')

# для одного объекта
api.add_resource(NewsResource, '/api/v2/news/<int:news_id>')
api.add_resource(UsersResource, '/api/v2/users/<int:user_id>')
api.add_resource(JobsResource, '/api/v2/jobs/<int:job_id>')
'''
login_manager = LoginManager()
login_manager.init_app(app)


@app.route("/")
def index():
    return '<h1>Вроде робит</h1>'
    # return render_template()


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой адрес почты уже занят")
        if session.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такое имя уже занято")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


def main():
    # session = db_session.create_session()
    app.run()


if __name__ == '__main__':
    main()
