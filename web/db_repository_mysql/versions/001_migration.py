from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
distr = Table('distr', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=64)),
    Column('version', String(length=64)),
    Column('release', Integer),
)

jobs = Table('jobs', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('pandaid', Integer),
    Column('distr_id', Integer),
    Column('params', String(length=1000)),
    Column('ifiles', String(length=1000)),
    Column('ofiles', String(length=1000)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['distr'].create()
    post_meta.tables['jobs'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['distr'].drop()
    post_meta.tables['jobs'].drop()
