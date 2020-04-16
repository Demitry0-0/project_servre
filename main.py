from flask import Flask, render_template, request, abort, make_response, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import redirect
from data.loginform import LoginForm
from data.registrform import RegisterForm
from data.records import Records
from data.news import News
from data.newsform import NewsForm
from data.users import User
from data.maps import Maps
from data import db_session
from data import records_api
from data import user_api
from data import maps_api
from data import alisa
import datetime

db_session.global_init("db/users.sqlite")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@app.route("/")
def index():
    session = db_session.create_session()
    news = session.query(News)[::-1]
    return render_template('index.html', news=news)


@app.route('/downoload')
def downoload():
    return app.send_static_file('project.py')


@app.route('/downoload_map/<int:id>', methods=['GET', 'POST'])
def downoload_map(id):
    session = db_session.create_session()
    map = session.query(Maps).filter(Maps.id == id).first()
    return app.send_static_file(map.downoload_map)


@app.route("/maps")
def maps():
    session = db_session.create_session()
    maps = session.query(Maps)
    return render_template('maps.html', maps=maps)


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        current_user.news.append(news)
        session.merge(current_user)
        session.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости',
                           form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          News.user == current_user).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          News.user == current_user).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html', title='Редактирование новости', form=form)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == id,
                                      News.user == current_user).first()
    if news:
        session.delete(news)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/records')
@app.route('/records/<name>', methods=['GET', 'POST'])
def records(name=None):
    session = db_session.create_session()
    maps = session.query(Maps)
    if name:
        count = "Все рекорды на карте " + name
        records = [sorted(session.query(Records).filter(Records.map_name == name),
                          key=lambda x: x.points)[::-1]]
    else:
        count = 'Все рекорды'
        records = []
        for i in session.query(Maps):
            lst = session.query(Records).filter(Records.map_name == i.name_map)
            if lst:
                records.append(sorted(lst, key=lambda x: x.points, reverse=True)[:10])
            else:
                break

        # records = sorted(session.query(Records), key=lambda x: x.map_name)[::-1]
    return render_template('records.html', title='Рекорды', maps=maps, records=records, count=count)


@app.route('/get_one_records', methods=['GET', 'POST'])
def get_one_records():
    records = request.form.get('records')
    session = db_session.create_session()
    maps = session.query(Maps).filter(Maps.name_map == records).first()
    url = f'/records/{maps.name_map}' if maps else '/records'
    return redirect(url)


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
    session = db_session.create_session()
    app.register_blueprint(records_api.blueprint)
    app.register_blueprint(user_api.blueprint)
    app.register_blueprint(maps_api.blueprint)
    # alisa.alisa_run('https://965bbd14.ngrok.io')#input('Введите адрес или ничего')
    app.register_blueprint(alisa.blueprint)
    app.run()


if __name__ == '__main__':
    main()
