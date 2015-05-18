from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
jobs = Table('jobs', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('pandaid', Integer),
    Column('owner_id', Integer),
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
    post_meta.tables['jobs'].columns['owner_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['jobs'].columns['owner_id'].drop()
