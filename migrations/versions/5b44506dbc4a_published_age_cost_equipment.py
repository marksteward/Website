"""published age, cost, equipment

Revision ID: 5b44506dbc4a
Revises: b9197788436d
Create Date: 2018-07-17 20:20:13.283273

"""

# revision identifiers, used by Alembic.
revision = '5b44506dbc4a'
down_revision = 'b9197788436d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('proposal', sa.Column('published_age_range', sa.String(), nullable=True))
    op.add_column('proposal', sa.Column('published_cost', sa.String(), nullable=True))
    op.add_column('proposal', sa.Column('published_participant_equipment', sa.String(), nullable=True))
    op.add_column('proposal_version', sa.Column('published_age_range', sa.String(), autoincrement=False, nullable=True))
    op.add_column('proposal_version', sa.Column('published_cost', sa.String(), autoincrement=False, nullable=True))
    op.add_column('proposal_version', sa.Column('published_participant_equipment', sa.String(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('proposal_version', 'published_participant_equipment')
    op.drop_column('proposal_version', 'published_cost')
    op.drop_column('proposal_version', 'published_age_range')
    op.drop_column('proposal', 'published_participant_equipment')
    op.drop_column('proposal', 'published_cost')
    op.drop_column('proposal', 'published_age_range')
    # ### end Alembic commands ###
