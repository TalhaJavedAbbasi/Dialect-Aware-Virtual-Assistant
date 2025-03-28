"""Add CustomCommand model

Revision ID: 6b8c279ff31e
Revises: be6f2b77d7a1
Create Date: 2025-03-21 15:01:33.883093

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b8c279ff31e'
down_revision = 'be6f2b77d7a1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('custom_command',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('command_name', sa.String(length=100), nullable=False),
    sa.Column('trigger_phrase', sa.String(length=255), nullable=False),
    sa.Column('action_type', sa.String(length=50), nullable=False),
    sa.Column('parameters', sa.JSON(), nullable=True),
    sa.Column('status', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('trigger_phrase')
    )
    with op.batch_alter_table('user_moods', schema=None) as batch_op:
        batch_op.alter_column('mood',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_moods', schema=None) as batch_op:
        batch_op.alter_column('mood',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)

    op.drop_table('custom_command')
    # ### end Alembic commands ###
