"""backfill default user settings

Revision ID: 3a90ccad7af9
Revises: 89cc7b8cb451
Create Date: 2025-12-27 12:12:50.353677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.core.default_settings import DEFAULT_USER_SETTINGS


# revision identifiers, used by Alembic.
revision: str = '3a90ccad7af9'
down_revision: Union[str, None] = '89cc7b8cb451'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    # Get all user IDs
    result = connection.execute(sa.text("SELECT id FROM users"))
    user_ids = [row[0] for row in result]
    
    # For each user, insert default settings that don't already exist
    for user_id in user_ids:
        for key, value in DEFAULT_USER_SETTINGS.items():
            # Check if setting already exists
            existing = connection.execute(
                sa.text("""
                    SELECT id FROM user_settings 
                    WHERE user_id = :user_id AND key = :key
                """),
                {"user_id": user_id, "key": key}
            ).first()
            
            # Only insert if it doesn't exist
            if not existing:
                connection.execute(
                    sa.text("""
                        INSERT INTO user_settings (user_id, key, value)
                        VALUES (:user_id, :key, :value)
                    """),
                    {"user_id": user_id, "key": key, "value": value}
                )
    
    connection.commit()


def downgrade() -> None:
    """Downgrade schema."""
    pass
