from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from models import User, AnonymousUser

lm.anonymous_user = AnonymousUser
@lm.user_loader
def load_user(id):
    if id == 0:
        return AnonymousUser()
    return User.query.filter_by(id=id).first()


from app import views
from app import apis

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('../log/panda-web-client.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('microblog startup')

if __name__ == '__main__':
    #app.run()
    pass
