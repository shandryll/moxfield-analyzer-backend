import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Request
from src.application.use_cases.validate_deck import ValidateDeckUseCase
from src.infrastructure.http.rate_limit import limiter
from src.shared.exceptions import NotFoundMoxfieldError
from src.infrastructure.utils.metrics import measure_time
from src.shared.models import DeckDetails

router = APIRouter(prefix="/api")
use_case = ValidateDeckUseCase()


@router.get(
    "/deck/validate",
    response_model=DeckDetails,
    summary="Valida e analisa um deck do Moxfield",
    description="Busca um deck público do Moxfield e retorna análise completa",
    responses={
        400: {"description": "Parâmetros inválidos"},
        404: {"description": "Deck não encontrado"},
        429: {"description": "Muitas requisições (rate limit)"},
        500: {"description": "Erro interno do servidor"},
    },
)
@limiter.limit("10/minute")
@measure_time
async def validate_deck(
    request: Request,
    url: str = Query(..., description="URL completa do deck no Moxfield ou apenas o ID do deck"),
    kindred: str = Query(..., min_length=1, description="Tipo tribal para análise"),
):
    try:
        return await use_case.execute(url=url, kindred=kindred)
    except NotFoundMoxfieldError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/health",
    summary="Health check",
    description="Verifica se a API está respondendo corretamente",
)
async def health():
    return {
        "status": "OK",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "documentation": "/docs",
    }
