"""add public sharing to assistants
Revision ID: 9a086854b272
Revises: 20260319_add_nickname
Create Date: 2026-03-23 22:00:47.912510
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic
revision = '9a086854b272'
down_revision = '20260319_add_nickname'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'assistants',
        sa.Column('public_sharing_enabled', sa.Boolean(), server_default='false', nullable=False),
    )
    op.add_column(
        'assistants',
        sa.Column('public_sharing_token', UUID(as_uuid=True), nullable=True),
    )
    op.create_unique_constraint(
        'uq_assistants_public_sharing_token', 'assistants', ['public_sharing_token']
    )


def downgrade() -> None:
    op.drop_constraint('uq_assistants_public_sharing_token', 'assistants', type_='unique')
    op.drop_column('assistants', 'public_sharing_token')
    op.drop_column('assistants', 'public_sharing_enabled')