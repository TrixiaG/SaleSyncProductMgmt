from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'SaleSyncAdmin'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'login.userLogin'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(str(user_id))
    

    from .views import views
    from .login import login
    from .registration import registration
    from .cashierops import cashierops
    from .inventory import inventory
    from .transactions import transactions
    from .usermanagement import usermanagement
    from .models import User, prodInventory, Transaction, IndivTransaction

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(login, url_prefix='/')
    app.register_blueprint(registration, url_prefix='/')
    app.register_blueprint(cashierops, url_prefix='/')
    app.register_blueprint(inventory, url_prefix='/')
    app.register_blueprint(transactions, url_prefix='/')
    app.register_blueprint(usermanagement, url_prefix='/')

    with app.app_context():
        db.create_all()

    return app

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
