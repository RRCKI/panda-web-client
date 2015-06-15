from flask.ext.login import current_user
from app import adm, db
from flask.ext.admin.contrib.sqla import ModelView

from models import *


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.role == ROLE_ADMIN

adm.add_view(MyModelView(User, db.session))
adm.add_view(MyModelView(Distributive, db.session))
adm.add_view(MyModelView(Site, db.session))
adm.add_view(MyModelView(Job, db.session))
adm.add_view(MyModelView(Container, db.session))
adm.add_view(MyModelView(File, db.session))
adm.add_view(MyModelView(Replica, db.session))
adm.add_view(MyModelView(TransferTask, db.session))