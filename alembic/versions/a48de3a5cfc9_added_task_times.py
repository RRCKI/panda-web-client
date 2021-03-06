"""added task times

Revision ID: a48de3a5cfc9
Revises: 8a5182ebd03c
Create Date: 2016-05-31 18:38:35.950740

"""

# revision identifiers, used by Alembic.
revision = 'a48de3a5cfc9'
down_revision = '8a5182ebd03c'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('creation_time', sa.DateTime(), nullable=True))
    op.add_column('tasks', sa.Column('modification_time', sa.DateTime(), nullable=True))
    op.drop_column('tasks', 'percentage')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('percentage', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_column('tasks', 'modification_time')
    op.drop_column('tasks', 'creation_time')
    ### end Alembic commands ###