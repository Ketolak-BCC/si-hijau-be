"""add google auth fields to users table

Revision ID: 20261007_0001
Revises:
Create Date: 2026-10-07 17:30:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '20261007_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # alter hashed_password to nullable=True
    op.alter_column(
        'users',
        'hashed_password',
        existing_type=sa.String(length=255),
        nullable=True,
    )
    # add avatar_url
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500), nullable=True))
    # add google_id
    op.add_column('users', sa.Column('google_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)
    # add auth_provider
    op.add_column(
        'users',
        sa.Column('auth_provider', sa.String(length=50), nullable=False, server_default='local'),
    )


def downgrade() -> None:
    op.drop_column('users', 'auth_provider')
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'avatar_url')
    op.alter_column(
        'users',
        'hashed_password',
        existing_type=sa.String(length=255),
        nullable=False,
    )
