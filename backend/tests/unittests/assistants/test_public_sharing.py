"""Tests for public assistant sharing feature.

Covers:
- Domain entity: public_sharing_enabled / public_sharing_token in update()
- Service: toggle_public_sharing() guards and behavior
- Public service: get_public_assistant_info() and get_assistant_owner_and_id()
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import sqlalchemy as sa

from intric.ai_models.completion_models.completion_model import ModelKwargs
from intric.assistants.assistant import Assistant
from intric.assistants.assistant_service import AssistantService
from intric.assistants.public_assistant_service import PublicAssistantService
from intric.main.exceptions import BadRequestException, NotFoundException, UnauthorizedException
from intric.main.models import NOT_PROVIDED


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def assistant():
    return Assistant(
        id=uuid4(),
        user=MagicMock(),
        name="Test Assistant",
        space_id=uuid4(),
        prompt=None,
        completion_model=None,
        completion_model_kwargs=ModelKwargs(),
        logging_enabled=False,
        websites=[],
        collections=[],
        attachments=[],
        published=False,
    )


@pytest.fixture
def service():
    space_repo = AsyncMock()
    mock_assistant = MagicMock()
    mock_assistant.published = True
    mock_assistant.public_sharing_enabled = False
    mock_assistant.public_sharing_token = None
    mock_assistant.id = uuid4()

    mock_space = MagicMock()
    mock_space.get_assistant.return_value = mock_assistant
    mock_space.is_personal.return_value = False

    space_repo.get_space_by_assistant.return_value = mock_space

    refreshed_space = MagicMock()
    refreshed_assistant = MagicMock()
    refreshed_space.get_assistant.return_value = refreshed_assistant
    space_repo.update.return_value = refreshed_space

    actor = MagicMock()
    actor.can_publish_assistants.return_value = True
    actor.get_assistant_permissions.return_value = []

    actor_manager = MagicMock()
    actor_manager.get_space_actor_from_space.return_value = actor

    svc = AssistantService(
        repo=AsyncMock(),
        space_repo=space_repo,
        user=MagicMock(),
        auth_service=MagicMock(),
        service_repo=AsyncMock(),
        step_repo=AsyncMock(),
        completion_model_crud_service=AsyncMock(),
        space_service=AsyncMock(),
        factory=MagicMock(),
        prompt_service=AsyncMock(),
        file_service=AsyncMock(),
        assistant_template_service=AsyncMock(),
        session_service=AsyncMock(),
        actor_manager=actor_manager,
        integration_knowledge_repo=AsyncMock(),
        completion_service=AsyncMock(),
        references_service=AsyncMock(),
        icon_repo=AsyncMock(),
    )

    return svc, mock_space, mock_assistant, actor


# ---------------------------------------------------------------------------
# Domain entity tests
# ---------------------------------------------------------------------------


class TestAssistantPublicSharingFields:
    def test_default_public_sharing_disabled(self, assistant):
        assert assistant.public_sharing_enabled is False
        assert assistant.public_sharing_token is None

    def test_update_public_sharing_enabled(self, assistant):
        assistant.update(public_sharing_enabled=True)
        assert assistant.public_sharing_enabled is True

    def test_update_public_sharing_disabled(self, assistant):
        assistant.update(public_sharing_enabled=True)
        assistant.update(public_sharing_enabled=False)
        assert assistant.public_sharing_enabled is False

    def test_update_public_sharing_token(self, assistant):
        token = uuid4()
        assistant.update(public_sharing_token=token)
        assert assistant.public_sharing_token == token

    def test_update_public_sharing_token_to_none(self, assistant):
        token = uuid4()
        assistant.update(public_sharing_token=token)
        assistant.update(public_sharing_token=None)
        assert assistant.public_sharing_token is None

    def test_update_public_sharing_token_not_provided_keeps_value(self, assistant):
        token = uuid4()
        assistant.update(public_sharing_token=token)
        assistant.update(public_sharing_token=NOT_PROVIDED)
        assert assistant.public_sharing_token == token

    def test_update_public_sharing_enabled_none_keeps_value(self, assistant):
        assistant.update(public_sharing_enabled=True)
        assistant.update(public_sharing_enabled=None)
        assert assistant.public_sharing_enabled is True

    def test_init_with_public_sharing(self):
        token = uuid4()
        a = Assistant(
            id=uuid4(),
            user=MagicMock(),
            name="test",
            space_id=uuid4(),
            prompt=None,
            completion_model=None,
            completion_model_kwargs=ModelKwargs(),
            logging_enabled=False,
            websites=[],
            collections=[],
            attachments=[],
            published=True,
            public_sharing_enabled=True,
            public_sharing_token=token,
        )
        assert a.public_sharing_enabled is True
        assert a.public_sharing_token == token


# ---------------------------------------------------------------------------
# Service: toggle_public_sharing tests
# ---------------------------------------------------------------------------


class TestTogglePublicSharing:
    @pytest.mark.asyncio
    async def test_enable_generates_token(self, service):
        svc, mock_space, mock_assistant, actor = service
        mock_assistant.published = True
        mock_assistant.public_sharing_token = None

        await svc.toggle_public_sharing(assistant_id=mock_assistant.id, enable=True)

        # Should have called update with public_sharing_enabled=True and a new token
        mock_assistant.update.assert_called_once()
        call_kwargs = mock_assistant.update.call_args.kwargs
        assert call_kwargs["public_sharing_enabled"] is True
        assert call_kwargs["public_sharing_token"] is not None

    @pytest.mark.asyncio
    async def test_enable_reuses_existing_token(self, service):
        svc, mock_space, mock_assistant, actor = service
        mock_assistant.published = True
        existing_token = uuid4()
        mock_assistant.public_sharing_token = existing_token

        await svc.toggle_public_sharing(assistant_id=mock_assistant.id, enable=True)

        call_kwargs = mock_assistant.update.call_args.kwargs
        assert call_kwargs["public_sharing_enabled"] is True
        # Should not set a new token
        assert "public_sharing_token" not in call_kwargs

    @pytest.mark.asyncio
    async def test_disable_keeps_token(self, service):
        svc, mock_space, mock_assistant, actor = service

        await svc.toggle_public_sharing(assistant_id=mock_assistant.id, enable=False)

        call_kwargs = mock_assistant.update.call_args.kwargs
        assert call_kwargs["public_sharing_enabled"] is False
        # Token should not be cleared
        assert "public_sharing_token" not in call_kwargs

    @pytest.mark.asyncio
    async def test_rejects_unpublished_assistant(self, service):
        svc, mock_space, mock_assistant, actor = service
        mock_assistant.published = False

        with pytest.raises(BadRequestException, match="published"):
            await svc.toggle_public_sharing(assistant_id=mock_assistant.id, enable=True)

    @pytest.mark.asyncio
    async def test_rejects_personal_space(self, service):
        svc, mock_space, mock_assistant, actor = service
        mock_space.is_personal.return_value = True

        with pytest.raises(BadRequestException, match="shared spaces"):
            await svc.toggle_public_sharing(assistant_id=mock_assistant.id, enable=True)

    @pytest.mark.asyncio
    async def test_rejects_without_publish_permission(self, service):
        svc, mock_space, mock_assistant, actor = service
        actor.can_publish_assistants.return_value = False

        with pytest.raises(UnauthorizedException):
            await svc.toggle_public_sharing(assistant_id=mock_assistant.id, enable=True)

    @pytest.mark.asyncio
    async def test_disable_allowed_for_unpublished(self, service):
        """Disabling should work even if assistant is unpublished."""
        svc, mock_space, mock_assistant, actor = service
        mock_assistant.published = False

        # Should not raise
        await svc.toggle_public_sharing(assistant_id=mock_assistant.id, enable=False)

    @pytest.mark.asyncio
    async def test_persists_via_space_repo(self, service):
        svc, mock_space, mock_assistant, actor = service
        mock_assistant.published = True

        await svc.toggle_public_sharing(assistant_id=mock_assistant.id, enable=True)

        svc.space_repo.update.assert_called_once_with(mock_space)


# ---------------------------------------------------------------------------
# Public assistant service tests
# ---------------------------------------------------------------------------


class TestPublicAssistantService:
    @pytest.mark.asyncio
    async def test_get_info_returns_name_description_icon(self):
        session = AsyncMock()
        token = uuid4()
        icon_id = uuid4()

        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.name = "My Assistant"
        mock_row.description = "Helps with things"
        mock_row.icon_id = icon_id
        mock_result.first.return_value = mock_row
        session.execute.return_value = mock_result

        svc = PublicAssistantService(session=session)
        info = await svc.get_public_assistant_info(token)

        assert info["name"] == "My Assistant"
        assert info["description"] == "Helps with things"
        assert info["icon_id"] == icon_id

    @pytest.mark.asyncio
    async def test_get_info_raises_not_found(self):
        session = AsyncMock()
        token = uuid4()

        mock_result = MagicMock()
        mock_result.first.return_value = None
        session.execute.return_value = mock_result

        svc = PublicAssistantService(session=session)

        with pytest.raises(NotFoundException):
            await svc.get_public_assistant_info(token)

    @pytest.mark.asyncio
    async def test_get_owner_and_id_returns_ids(self):
        session = AsyncMock()
        token = uuid4()
        assistant_id = uuid4()
        user_id = uuid4()

        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.id = assistant_id
        mock_row.user_id = user_id
        mock_result.first.return_value = mock_row
        session.execute.return_value = mock_result

        svc = PublicAssistantService(session=session)
        aid, uid = await svc.get_assistant_owner_and_id(token)

        assert aid == assistant_id
        assert uid == user_id

    @pytest.mark.asyncio
    async def test_get_owner_and_id_raises_not_found(self):
        session = AsyncMock()
        token = uuid4()

        mock_result = MagicMock()
        mock_result.first.return_value = None
        session.execute.return_value = mock_result

        svc = PublicAssistantService(session=session)

        with pytest.raises(NotFoundException):
            await svc.get_assistant_owner_and_id(token)
