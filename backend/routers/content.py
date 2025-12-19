from fastapi import APIRouter

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/header")
async def get_header():
    # Placeholder for header generation
    return {"image_url": "placeholder", "description": "placeholder"}


@router.get("/readme")
async def get_readme():
    # Placeholder for readme generation
    return {"content": "# Readme"}


@router.get("/architecture")
async def get_architecture():
    # Placeholder for architecture generation
    return {"image_url": "placeholder"}
