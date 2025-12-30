"""backfill availability windows

Revision ID: 2b51405a0ae3
Revises: 1fb5d1dd7e28
Create Date: 2025-12-28 12:10:31.129123

"""
from typing import Sequence, Union
import datetime as dt

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b51405a0ae3'
down_revision: Union[str, None] = '1fb5d1dd7e28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Get database connection
    connection = op.get_bind()

    # Define tables
    users = sa.table('users', sa.column('id', sa.Integer))
    
    weekly_availability = sa.table('weekly_availability',
        sa.column('id', sa.Integer),
        sa.column('user_id', sa.Integer),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime)
    )
    
    daily_windows = sa.table('daily_windows',
        sa.column('id', sa.Integer),
        sa.column('weekly_availability_id', sa.Integer),
        sa.column('day_of_week', sa.Integer),
        sa.column('start_time', sa.Time),
        sa.column('end_time', sa.Time)
    )

    # Find users who don't have an availability record
    # query: SELECT users.id FROM users LEFT JOIN weekly_availability ON users.id = weekly_availability.user_id WHERE weekly_availability.id IS NULL
    
    query = sa.select(users.c.id).select_from(
        users.outerjoin(
            weekly_availability, users.c.id == weekly_availability.c.user_id
        )
    ).where(weekly_availability.c.id == None) # noqa
    
    results = connection.execute(query).fetchall()
    
    now = dt.datetime.now(dt.timezone.utc)
    start_time = dt.time(7, 0)
    end_time = dt.time(17, 0)

    for row in results:
        user_id = row[0]
        
        # Insert WeeklyAvailability
        result = connection.execute(
            weekly_availability.insert().values(
                user_id=user_id,
                created_at=now,
                updated_at=now
            )
        )
        
        # Retrieve the generated ID
        new_avail_id = result.inserted_primary_key[0] if result.inserted_primary_key else None
        
        if not new_avail_id:
             new_avail_id = connection.execute(
                sa.select(weekly_availability.c.id).where(weekly_availability.c.user_id == user_id)
            ).scalar()

        # Insert DailyWindows (Mon-Sun: 0-6)
        windows_data = [
            {
                'weekly_availability_id': new_avail_id,
                'day_of_week': day,
                'start_time': start_time,
                'end_time': end_time
            }
            for day in range(7)
        ]
        
        if windows_data:
            connection.execute(daily_windows.insert(), windows_data)


def downgrade() -> None:
    """Downgrade schema."""
    pass
