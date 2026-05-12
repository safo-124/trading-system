from fastapi import APIRouter

from app.api.deps import SessionDep
from app.models.schemas import PipelineRunResponse
from app.services.pipeline import PipelineService

router = APIRouter()


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(session: SessionDep) -> PipelineRunResponse:
    return await PipelineService(session).run()
