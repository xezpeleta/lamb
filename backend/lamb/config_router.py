from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Any, Dict
from .database_manager import LambDatabaseManager
from utils.pipelines.auth import get_current_user
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
db_manager = LambDatabaseManager()

# Initialize templates
templates = Jinja2Templates(directory="lamb/templates")

@router.get("", include_in_schema=False)  # Root path for /v1/config
async def read_config(request: Request):
    """Serve the config management page"""
    return templates.TemplateResponse("config.html", {"request": request, "api_key": API_KEY})

@router.get("/data")  # This will be /v1/config/data
async def get_config(str = Depends(get_current_user)) -> Dict[str, Any]:
    """Get the full config"""
    config = db_manager.get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

@router.get("/{key}")
async def get_config_key(key: str, str = Depends(get_current_user)) -> Any:
    """Get a specific config key"""
    value = db_manager.get_config_key(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Config key '{key}' not found")
    return {key: value}

@router.put("")
async def update_config(config: Dict[str, Any], str = Depends(get_current_user)) -> Dict[str, str]:
    """Update the entire config"""
    if db_manager.update_config(config):
        return {"message": "Config updated successfully"}
    raise HTTPException(status_code=500, detail="Failed to update config")

@router.put("/{key}")
async def set_config_key(key: str, value: Any, str = Depends(get_current_user)) -> Dict[str, str]:
    """Set a specific config key"""
    if db_manager.set_config_key(key, value):
        return {"message": f"Config key '{key}' updated successfully"}
    raise HTTPException(status_code=500, detail=f"Failed to update config key '{key}'")

@router.delete("/{key}")
async def delete_config_key(key: str, str = Depends(get_current_user)) -> Dict[str, str]:
    """Delete a specific config key"""
    if db_manager.delete_config_key(key):
        return {"message": f"Config key '{key}' deleted successfully"}
    raise HTTPException(status_code=404, detail=f"Config key '{key}' not found") 