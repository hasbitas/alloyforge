from importlib.util import find_spec

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import settings
from .orchestrator import AlloyDesignOrchestrator
from .schemas import DesignRequest, DesignResponse, HealthResponse

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Alloy design orchestrator powered by PyTorch PPO",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
orchestrator = AlloyDesignOrchestrator()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        framework="pytorch",
        torch_version=torch.__version__,
        cuda_available=torch.cuda.is_available(),
        chgnet_available=find_spec("chgnet") is not None,
    )


@app.post(f"{settings.api_prefix}/design", response_model=DesignResponse)
def design_alloy(request: DesignRequest) -> DesignResponse:
    try:
        return orchestrator.design(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get(f"{settings.api_prefix}/artifacts/{{design_id}}/{{file_name}}")
def download_artifact(design_id: str, file_name: str) -> FileResponse:
    if not design_id.isalnum() or file_name not in {"alloy.cif", "simulation.mat", "report.pdf"}:
        raise HTTPException(status_code=404, detail="File not found.")
    path = (settings.artifact_dir / design_id / file_name).resolve()
    artifact_root = settings.artifact_dir.resolve()
    if artifact_root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path, filename=file_name)

