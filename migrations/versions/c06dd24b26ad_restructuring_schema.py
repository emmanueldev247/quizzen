"""restructuring schema

Revision ID: c06dd24b26ad
Revises: 1bcbe7a5ea49
Create Date: 2025-01-02 21:04:58.809506

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c06dd24b26ad'
down_revision = '1bcbe7a5ea49'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('answer_choice',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(length=255), nullable=False),
    sa.Column('is_correct', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_multiple_response', sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column('points', sa.Integer(), nullable=False))
        batch_op.alter_column('question_type',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.Enum('multiple_choice', 'short_answer', name='question_type'),
               nullable=False)
        batch_op.drop_column('answer_choices')
        batch_op.drop_column('correct_answer')

    with op.batch_alter_table('quiz', schema=None) as batch_op:
        batch_op.add_column(sa.Column('max_score', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('quiz', schema=None) as batch_op:
        batch_op.drop_column('max_score')

    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.add_column(sa.Column('correct_answer', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('answer_choices', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False))
        batch_op.alter_column('question_type',
               existing_type=sa.Enum('multiple_choice', 'short_answer', name='question_type'),
               type_=sa.VARCHAR(length=50),
               nullable=True)
        batch_op.drop_column('points')
        batch_op.drop_column('is_multiple_response')

    op.drop_table('answer_choice')
    # ### end Alembic commands ###
