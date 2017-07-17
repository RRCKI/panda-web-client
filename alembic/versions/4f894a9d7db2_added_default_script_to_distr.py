"""added default script to distr

Revision ID: 4f894a9d7db2
Revises: eef5682e45eb
Create Date: 2017-05-02 12:15:44.281738

"""

# revision identifiers, used by Alembic.
revision = '4f894a9d7db2'
down_revision = 'eef5682e45eb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('distr', sa.Column('command', sa.String(length=1024), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('distr', 'command')
    ### end Alembic commands ###