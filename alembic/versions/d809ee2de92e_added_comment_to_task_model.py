"""added comment to Task model

Revision ID: d809ee2de92e
Revises: e808ff772420
Create Date: 2016-07-01 12:08:22.840850

"""

# revision identifiers, used by Alembic.
revision = 'd809ee2de92e'
down_revision = 'e808ff772420'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('comment', sa.String(length=1024), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tasks', 'comment')
    ### end Alembic commands ###