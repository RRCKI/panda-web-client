"""initial setup

Revision ID: 8a5182ebd03c
Revises: None
Create Date: 2016-05-31 16:42:03.753096

"""

# revision identifiers, used by Alembic.
revision = '8a5182ebd03c'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('celery_taskmeta',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('result', sa.BLOB(), nullable=True),
    sa.Column('date_done', sa.DateTime(), nullable=True),
    sa.Column('traceback', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('celery_tasksetmeta',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('taskset_id', sa.String(length=255), nullable=True),
    sa.Column('result', sa.BLOB(), nullable=True),
    sa.Column('date_done', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('containers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('guid', sa.String(length=100), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('distr',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('version', sa.String(length=64), nullable=True),
    sa.Column('release', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scope', sa.String(length=64), nullable=True),
    sa.Column('attemptn', sa.Integer(), nullable=True),
    sa.Column('guid', sa.String(length=100), nullable=True),
    sa.Column('type', sa.String(length=20), nullable=True),
    sa.Column('lfn', sa.String(length=200), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('transfertask', sa.String(length=40), nullable=True),
    sa.Column('fsize', sa.BigInteger(), nullable=True),
    sa.Column('md5sum', sa.String(length=36), nullable=True),
    sa.Column('checksum', sa.String(length=36), nullable=True),
    sa.Column('modification_time', sa.DateTime(), nullable=True),
    sa.Column('downloaded', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('se', sa.String(length=64), nullable=True),
    sa.Column('ce', sa.String(length=64), nullable=True),
    sa.Column('plugin', sa.String(length=20), nullable=True),
    sa.Column('active', sa.Integer(), nullable=True),
    sa.Column('datadir', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('active', sa.Integer(), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('role', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_table('catalog',
    sa.Column('container_id', sa.Integer(), nullable=True),
    sa.Column('file_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['container_id'], ['containers.id'], ),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], )
    )
    op.create_table('clients',
    sa.Column('name', sa.String(length=40), nullable=True),
    sa.Column('description', sa.String(length=400), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('client_id', sa.String(length=40), nullable=False),
    sa.Column('client_secret', sa.String(length=55), nullable=False),
    sa.Column('is_confidential', sa.Boolean(), nullable=True),
    sa.Column('_redirect_uris', sa.Text(), nullable=True),
    sa.Column('_default_scopes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('client_id')
    )
    op.create_index(op.f('ix_clients_client_secret'), 'clients', ['client_secret'], unique=True)
    op.create_table('jobs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pandaid', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.Column('distr_id', sa.Integer(), nullable=True),
    sa.Column('params', sa.String(length=1000), nullable=True),
    sa.Column('container_id', sa.Integer(), nullable=True),
    sa.Column('creation_time', sa.DateTime(), nullable=True),
    sa.Column('modification_time', sa.DateTime(), nullable=True),
    sa.Column('ninputfiles', sa.Integer(), nullable=True),
    sa.Column('noutputfiles', sa.Integer(), nullable=True),
    sa.Column('registered', sa.Integer(), nullable=True),
    sa.Column('registation_time', sa.DateTime(), nullable=True),
    sa.Column('ce', sa.String(length=40), nullable=True),
    sa.Column('corecount', sa.Integer(), nullable=True),
    sa.Column('tags', sa.String(length=256), nullable=True),
    sa.Column('attemptnr', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['container_id'], ['containers.id'], ),
    sa.ForeignKeyConstraint(['distr_id'], ['distr.id'], ),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('replicas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('original_id', sa.Integer(), nullable=True),
    sa.Column('se', sa.String(length=20), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('lfn', sa.String(length=200), nullable=True),
    sa.Column('token', sa.String(length=200), nullable=True),
    sa.ForeignKeyConstraint(['original_id'], ['files.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.Column('tag', sa.String(length=256), nullable=True),
    sa.Column('status', sa.String(length=64), nullable=True),
    sa.Column('percentage', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('grants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('client_id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=255), nullable=False),
    sa.Column('redirect_uri', sa.String(length=255), nullable=True),
    sa.Column('expires', sa.DateTime(), nullable=True),
    sa.Column('_scopes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_grants_code'), 'grants', ['code'], unique=False)
    op.create_table('tasks_jobs',
    sa.Column('task_id', sa.Integer(), nullable=True),
    sa.Column('job_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], )
    )
    op.create_table('tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.String(length=40), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('token_type', sa.String(length=40), nullable=True),
    sa.Column('access_token', sa.String(length=255), nullable=True),
    sa.Column('refresh_token', sa.String(length=255), nullable=True),
    sa.Column('expires', sa.DateTime(), nullable=True),
    sa.Column('_scopes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('access_token'),
    sa.UniqueConstraint('refresh_token')
    )
    op.create_table('transfertasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('replica_id', sa.Integer(), nullable=True),
    sa.Column('se', sa.String(length=40), nullable=True),
    sa.Column('task_id', sa.String(length=40), nullable=True),
    sa.Column('task_status', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['replica_id'], ['replicas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transfertasks')
    op.drop_table('tokens')
    op.drop_table('tasks_jobs')
    op.drop_index(op.f('ix_grants_code'), table_name='grants')
    op.drop_table('grants')
    op.drop_table('tasks')
    op.drop_table('replicas')
    op.drop_table('jobs')
    op.drop_index(op.f('ix_clients_client_secret'), table_name='clients')
    op.drop_table('clients')
    op.drop_table('catalog')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
    op.drop_table('sites')
    op.drop_table('files')
    op.drop_table('distr')
    op.drop_table('containers')
    op.drop_table('celery_tasksetmeta')
    op.drop_table('celery_taskmeta')
    ### end Alembic commands ###