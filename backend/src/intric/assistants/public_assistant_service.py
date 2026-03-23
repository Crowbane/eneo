from uuid import UUID

import sqlalchemy as sa

from intric.database.database import AsyncSession
from intric.database.tables.assistant_table import Assistants
from intric.main.exceptions import NotFoundException


class PublicAssistantService:
    """Service for unauthenticated access to publicly shared assistants.

    Uses direct DB queries to avoid dependencies on user-scoped repos.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_public_assistant_info(self, token: UUID):
        """Get minimal info for a publicly shared assistant (name, description, icon)."""
        query = (
            sa.select(
                Assistants.name,
                Assistants.description,
                Assistants.icon_id,
            )
            .where(Assistants.public_sharing_token == token)
            .where(Assistants.public_sharing_enabled.is_(True))
            .where(Assistants.published.is_(True))
        )

        result = await self.session.execute(query)
        row = result.first()

        if row is None:
            raise NotFoundException("Public assistant not found or not available.")

        return {
            "name": row.name,
            "description": row.description,
            "icon_id": row.icon_id,
        }

    async def get_assistant_owner_and_id(self, token: UUID):
        """Get the assistant ID and owner user_id for a publicly shared assistant.

        Used to set up the container with the correct user context for the ask flow.
        """
        query = (
            sa.select(
                Assistants.id,
                Assistants.user_id,
            )
            .where(Assistants.public_sharing_token == token)
            .where(Assistants.public_sharing_enabled.is_(True))
            .where(Assistants.published.is_(True))
        )

        result = await self.session.execute(query)
        row = result.first()

        if row is None:
            raise NotFoundException("Public assistant not found or not available.")

        return row.id, row.user_id
