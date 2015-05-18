import os
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_DATABASE_URI = 'mysql://it:ivanpass@localhost/pandaweb'
#SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'web', 'db_repository_mysql')

UPLOAD_FOLDER = '/Users/it/tmp'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024