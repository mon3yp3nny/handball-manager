"""Add user_roles table for multi-role support

Revision ID: add_user_roles
Revises: 
Create Date: 2026-03-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_roles'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create user_roles association table
    op.create_table('user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role')
    )
    
    # Copy existing roles from users.role to user_roles
    op.execute("""
        INSERT INTO user_roles (user_id, role)
        SELECT id, role FROM users
    """)
    
    # Rename role column to primary_role for backward compatibility
    op.alter_column('users', 'role', new_column_name='primary_role')


def downgrade():
    # Restore role column name
    op.alter_column('users', 'primary_role', new_column_name='role')
    
    # Drop user_roles table
    op.drop_table('user_roles')
