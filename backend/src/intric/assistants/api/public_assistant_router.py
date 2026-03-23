from uuid import UUID

from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse, ServerSentEvent

from intric.assistants.api.assistant_models import PublicAskRequest, PublicAssistantView
from intric.database.database import AsyncSession, get_session_with_transaction
from intric.database.transaction import gen_transaction
from intric.main.container.container import Container
from intric.main.container.container_overrides import override_user
from intric.server.dependencies.container import get_container
from intric.server.protocol import responses

router = APIRouter()


@router.get(
    "/{token}/",
    response_model=PublicAssistantView,
    responses=responses.get_responses([404]),
)
async def get_public_assistant(
    token: UUID,
    container: Container = Depends(get_container()),
):
    service = container.public_assistant_service()
    info = await service.get_public_assistant_info(token)
    return PublicAssistantView(**info)


@router.post(
    "/{token}/ask/",
    responses=responses.get_responses([404]),
)
async def ask_public_assistant(
    token: UUID,
    ask: PublicAskRequest,
    container: Container = Depends(get_container()),
    db_session: AsyncSession = Depends(get_session_with_transaction),
):
    """Ask a publicly shared assistant. Streams the response as SSE if stream is true."""
    # First, look up the assistant + owner without needing user context
    public_service = container.public_assistant_service()
    assistant_id, owner_user_id = await public_service.get_assistant_owner_and_id(token)

    # Override the container with the assistant owner's user context
    # so that repos and services that depend on user can resolve
    user_repo = container.user_repo()
    owner_user = await user_repo.get_user_by_id(id=owner_user_id)
    override_user(container=container, user=owner_user)

    # Now use the full assistant service to process the question
    assistant_service = container.assistant_service()
    space = await container.space_repo().get_space_by_assistant(assistant_id=assistant_id)
    assistant = space.get_assistant(assistant_id=assistant_id)

    completion_service = container.completion_service()
    references_service = container.references_service()

    response, datastore_result = await assistant.ask(
        question=ask.question,
        completion_service=completion_service,
        references_service=references_service,
        session=None,
        files=[],
        stream=ask.stream,
        version=2,
    )

    if ask.stream:

        @gen_transaction(db_session)
        async def event_stream():
            async for chunk in response.completion:
                if chunk.text is not None:
                    yield ServerSentEvent(
                        data=chunk.text,
                        event="text",
                    )
            yield ServerSentEvent(data="", event="done")

        return EventSourceResponse(event_stream())

    return {"answer": response.completion}
