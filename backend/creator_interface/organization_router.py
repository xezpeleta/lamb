"""
Organization management router for creator interface
Provides admin endpoints to manage organizations through the creator interface
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import httpx
import logging
import json
import time
from .assistant_router import get_creator_user_from_token, is_admin_user
import config
from lamb.database_manager import LambDatabaseManager
from lamb.owi_bridge.owi_users import OwiUserManager

# Initialize router
router = APIRouter()
security = HTTPBearer()

# Initialize database manager
db_manager = LambDatabaseManager()

# Configure logging
logger = logging.getLogger(__name__)

# Get configuration
# Use LAMB_BACKEND_HOST for internal server-to-server requests
PIPELINES_HOST = config.LAMB_BACKEND_HOST or "http://localhost:9099"
LAMB_BEARER_TOKEN = config.LAMB_BEARER_TOKEN or "0p3n-w3bu!"

# Organization Admin Authorization Helpers
def get_user_organization_admin_info(auth_header: str) -> Optional[Dict[str, Any]]:
    """
    Get user information and check if they are an organization admin
    Returns user info with organization admin details if authorized, None otherwise
    """
    try:
        creator_user = get_creator_user_from_token(auth_header)
        if not creator_user:
            return None
        
        user_id = creator_user.get('id')
        if not user_id:
            return None
        
        # Get user's organization and role
        user_details = db_manager.get_creator_user_by_id(user_id)
        if not user_details or not user_details.get('organization_id'):
            return None
        
        org_id = user_details['organization_id']
        org_role = db_manager.get_user_organization_role(user_id, org_id)
        
        if org_role != "admin":
            return None
        
        # Get organization details
        organization = db_manager.get_organization_by_id(org_id)
        if not organization:
            return None
        
        return {
            'user_id': user_id,
            'user_email': user_details['user_email'],
            'user_name': user_details['user_name'],
            'organization_id': org_id,
            'organization': organization,
            'role': 'admin'
        }
    except Exception as e:
        logger.error(f"Error checking organization admin authorization: {e}")
        return None

def is_organization_admin(auth_header: str, organization_id: Optional[int] = None) -> bool:
    """
    Check if user is an admin of their organization (or specific organization if provided)
    """
    admin_info = get_user_organization_admin_info(auth_header)
    if not admin_info:
        return False
    
    if organization_id and admin_info['organization_id'] != organization_id:
        return False
    
    return True

async def verify_organization_admin_access(request: Request, organization_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Verify that the user has organization admin access
    Returns admin info if authorized, raises HTTPException otherwise
    """
    try:
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        # First, check if user is a system administrator
        from .assistant_router import is_admin_user
        if is_admin_user(auth_header):
            # System admin can access any organization
            creator_user = get_creator_user_from_token(auth_header)
            if not creator_user:
                raise HTTPException(status_code=403, detail="Invalid authentication token")
            
            # If organization_id is specified, get that organization, otherwise use system org
            target_org_id = organization_id if organization_id else 1  # Default to system org
            organization = db_manager.get_organization_by_id(target_org_id)
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")
            
            return {
                'user_id': creator_user.get('id'),
                'user_email': creator_user.get('email'),
                'user_name': creator_user.get('name'),
                'organization_id': target_org_id,
                'organization': organization,
                'role': 'system_admin'  # Indicate this is a system admin
            }
        
        # If not system admin, check for regular organization admin
        admin_info = get_user_organization_admin_info(auth_header)
        if not admin_info:
            raise HTTPException(status_code=403, detail="Organization admin privileges required")
        
        if organization_id and admin_info['organization_id'] != organization_id:
            raise HTTPException(status_code=403, detail="Access denied for this organization")
        
        return admin_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying organization admin access: {e}")
        raise HTTPException(status_code=500, detail="Authorization check failed")

# Pydantic models for API requests/responses
class OrganizationCreate(BaseModel):
    slug: str = Field(..., description="URL-friendly unique identifier")
    name: str = Field(..., description="Organization display name")
    config: Optional[Dict[str, Any]] = Field(None, description="Organization configuration")

class OrganizationCreateEnhanced(BaseModel):
    slug: str = Field(..., description="URL-friendly unique identifier")
    name: str = Field(..., description="Organization display name")
    admin_user_id: int = Field(..., description="ID of user from system org to become org admin")
    signup_enabled: bool = Field(False, description="Whether signup is enabled for this organization")
    signup_key: Optional[str] = Field(None, description="Unique signup key for organization-specific signup")
    use_system_baseline: bool = Field(True, description="Whether to copy system org config as baseline")
    config: Optional[Dict[str, Any]] = Field(None, description="Custom configuration (overrides system baseline)")

class SystemOrgUser(BaseModel):
    id: int
    email: str
    name: str
    role: str
    joined_at: int

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Organization display name")
    status: Optional[str] = Field(None, description="Organization status")
    config: Optional[Dict[str, Any]] = Field(None, description="Organization configuration")

class OrganizationResponse(BaseModel):
    id: int
    slug: str
    name: str
    is_system: bool
    status: str
    config: Dict[str, Any]
    created_at: int
    updated_at: int

class UserWithRole(BaseModel):
    id: int
    email: str
    name: str
    role: str
    joined_at: int

class OrganizationUsage(BaseModel):
    limits: Dict[str, Any]
    current: Dict[str, Any]
    organization: Dict[str, Any]

class ErrorResponse(BaseModel):
    detail: str

# Helper function to verify admin privileges
async def verify_admin_access(request: Request) -> str:
    """Verify that the current user has admin access"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    creator_user = get_creator_user_from_token(auth_header)
    if not creator_user:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    if not is_admin_user(creator_user):
        raise HTTPException(status_code=403, detail="Administrator privileges required")
    
    return auth_header

# Organization CRUD endpoints

@router.get(
    "/organizations/list",
    tags=["Organization Management"],
    summary="List Organizations for User Assignment (Admin Only)",
    description="""Retrieves a simplified list of organizations for user assignment dropdowns. Requires admin privileges.""",
    dependencies=[Depends(security)],
    responses={
        200: {"description": "Successfully retrieved organizations list."},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"}
    }
)
async def list_organizations_for_users(request: Request):
    """List organizations for user assignment (admin only)"""
    try:
        await verify_admin_access(request)
        
        organizations = db_manager.list_organizations()
        
        # Format for dropdown use
        org_list = []
        for org in organizations:
            org_list.append({
                "id": org["id"],
                "name": org["name"],
                "slug": org["slug"],
                "is_system": org.get("is_system", False)
            })
        
        return {
            "success": True,
            "data": org_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing organizations for users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/organizations/system/users",
    tags=["Organization Management"],
    summary="List System Organization Users (Admin Only)",
    description="""List all users from the system organization ('lamb') for admin assignment to new organizations.
    
Example Request:
```bash
curl -X GET 'http://localhost:8000/creator/admin/organizations/system/users' \\
-H 'Authorization: Bearer <admin_token>'
```

Example Success Response:
```json
[
  {
    "id": 1,
    "email": "admin@lamb.com",
    "name": "System Admin",
    "role": "admin",
    "joined_at": 1678886400
  },
  {
    "id": 2,
    "email": "user@lamb.com", 
    "name": "John Doe",
    "role": "member",
    "joined_at": 1678886500
  }
]
```
    """,
    response_model=List[SystemOrgUser],
    dependencies=[Depends(security)],
    responses={
        200: {"model": List[SystemOrgUser], "description": "List of system organization users"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_system_org_users(request: Request):
    """List all users from the system organization for admin assignment"""
    try:
        await verify_admin_access(request)
        
        users = db_manager.get_system_org_users()
        return [
            SystemOrgUser(
                id=user['id'],
                email=user['email'],
                name=user['name'],
                role=user['role'],
                joined_at=user['joined_at']
            )
            for user in users
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing system org users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/organizations",
    tags=["Organization Management"],
    summary="List All Organizations (Admin Only)",
    description="""List all organizations in the system. Requires admin privileges.

Example Request:
```bash
curl -X GET 'http://localhost:8000/creator/admin/organizations' \\
-H 'Authorization: Bearer <admin_token>'
```

Example Success Response:
```json
[
  {
    "id": 1,
    "slug": "lamb",
    "name": "LAMB System Organization",
    "is_system": true,
    "status": "active",
    "config": {
      "version": "1.0",
      "setups": {
        "default": {
          "name": "System Default",
          "providers": {...}
        }
      }
    },
    "created_at": 1678886400,
    "updated_at": 1678886400
  }
]
```
    """,
    response_model=List[OrganizationResponse],
    dependencies=[Depends(security)],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_organizations(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status")
):
    """List all organizations (admin only)"""
    try:
        await verify_admin_access(request)
        
        # Forward request to core organization router
        async with httpx.AsyncClient() as client:
            url = f"{PIPELINES_HOST}/lamb/v1/organizations"
            params = {}
            if status:
                params["status"] = status
                
            response = await client.get(
                url,
                params=params,
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch organizations: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch organizations: {response.text}"
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing organizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/organizations",
    tags=["Organization Management"],
    summary="Create Organization (Admin Only)",
    description="""Create a new organization. Requires admin privileges.

Example Request:
```bash
curl -X POST 'http://localhost:8000/creator/admin/organizations' \\
-H 'Authorization: Bearer <admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "slug": "engineering",
  "name": "Engineering Department",
  "config": {
    "version": "1.0",
    "setups": {
      "default": {
        "name": "Default Setup",
        "providers": {}
      }
    },
    "features": {
      "rag_enabled": true
    }
  }
}'
```

Example Success Response:
```json
{
  "id": 2,
  "slug": "engineering",
  "name": "Engineering Department",
  "is_system": false,
  "status": "active",
  "config": {...},
  "created_at": 1678886400,
  "updated_at": 1678886400
}
```
    """,
    response_model=OrganizationResponse,
    dependencies=[Depends(security)],
    responses={
        201: {"model": OrganizationResponse, "description": "Organization created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid input or organization already exists"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_organization(
    request: Request,
    org_data: OrganizationCreate
):
    """Create a new organization (admin only)"""
    try:
        await verify_admin_access(request)
        
        # Forward request to core organization router
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PIPELINES_HOST}/lamb/v1/organizations",
                json=org_data.dict(),
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Failed to create organization: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Failed to create organization")
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/organizations/enhanced",
    tags=["Organization Management"],
    summary="Create Organization with Admin Assignment (Admin Only)",
    description="""Create a new organization with admin user assignment and signup configuration.
    This endpoint copies the system organization configuration as baseline and assigns a user from 
    the system organization as the new organization's admin.

Example Request:
```bash
curl -X POST 'http://localhost:8000/creator/admin/organizations/enhanced' \\
-H 'Authorization: Bearer <admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "slug": "engineering",
  "name": "Engineering Department", 
  "admin_user_id": 2,
  "signup_enabled": true,
  "signup_key": "eng-dept-2024",
  "use_system_baseline": true
}'
```

Example Success Response:
```json
{
  "id": 3,
  "slug": "engineering",
  "name": "Engineering Department",
  "is_system": false,
  "status": "active",
  "config": {
    "version": "1.0",
    "metadata": {
      "admin_user_id": 2,
      "admin_user_email": "john@lamb.com",
      "created_by_system_admin": true
    },
    "features": {
      "signup_enabled": true,
      "signup_key": "eng-dept-2024"
    }
  },
  "created_at": 1678886400,
  "updated_at": 1678886400
}
```
    """,
    response_model=OrganizationResponse,
    dependencies=[Depends(security)],
    responses={
        201: {"model": OrganizationResponse, "description": "Organization created successfully with admin assigned"},
        400: {"model": ErrorResponse, "description": "Invalid input, signup key exists, or user not in system org"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_organization_enhanced(
    request: Request,
    org_data: OrganizationCreateEnhanced
):
    """Create a new organization with admin user assignment and signup configuration"""
    try:
        await verify_admin_access(request)
        
        # Validate signup key if provided
        if org_data.signup_key:
            is_valid, error_msg = db_manager.validate_signup_key_format(org_data.signup_key)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid signup key: {error_msg}")
            
            if not db_manager.validate_signup_key_uniqueness(org_data.signup_key):
                raise HTTPException(status_code=400, detail=f"Signup key '{org_data.signup_key}' already exists")
        
        # Check if organization slug already exists
        existing = db_manager.get_organization_by_slug(org_data.slug)
        if existing:
            raise HTTPException(status_code=400, detail=f"Organization with slug '{org_data.slug}' already exists")
        
        # Check if the selected user is a system admin (not eligible)
        admin_user = db_manager.get_creator_user_by_id(org_data.admin_user_id)
        if admin_user:
            system_org = db_manager.get_organization_by_slug("lamb")
            if system_org:
                current_role = db_manager.get_user_organization_role(org_data.admin_user_id, system_org['id'])
                if current_role == "admin":
                    raise HTTPException(
                        status_code=400, 
                        detail="System administrators cannot be assigned to new organizations. They must remain in the system organization to manage it."
                    )
        
        # Create organization with admin assignment
        org_id = db_manager.create_organization_with_admin(
            slug=org_data.slug,
            name=org_data.name,
            admin_user_id=org_data.admin_user_id,
            signup_enabled=org_data.signup_enabled,
            signup_key=org_data.signup_key,
            use_system_baseline=org_data.use_system_baseline,
            config=org_data.config
        )
        
        if not org_id:
            raise HTTPException(status_code=500, detail="Failed to create organization")
        
        # Get created organization and return
        org = db_manager.get_organization_by_id(org_id)
        if not org:
            raise HTTPException(status_code=500, detail="Organization created but could not retrieve details")
        
        return OrganizationResponse(
            id=org['id'],
            slug=org['slug'],
            name=org['name'],
            is_system=org['is_system'],
            status=org['status'],
            config=org['config'],
            created_at=org['created_at'],
            updated_at=org['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating enhanced organization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/organizations/{slug}",
    tags=["Organization Management"],
    summary="Get Organization Details",
    description="""Get details of a specific organization by slug.

Example Request:
```bash
curl -X GET 'http://localhost:8000/creator/admin/organizations/engineering' \\
-H 'Authorization: Bearer <admin_token>'
```

Example Success Response:
```json
{
  "id": 2,
  "slug": "engineering",
  "name": "Engineering Department",
  "is_system": false,
  "status": "active",
  "config": {
    "version": "1.0",
    "setups": {...},
    "features": {...},
    "limits": {...}
  },
  "created_at": 1678886400,
  "updated_at": 1678886400
}
```
    """,
    response_model=OrganizationResponse,
    dependencies=[Depends(security)],
    responses={
        200: {"model": OrganizationResponse, "description": "Organization details retrieved"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_organization(
    request: Request,
    slug: str
):
    """Get organization details by slug"""
    try:
        await verify_admin_access(request)
        
        # Forward request to core organization router
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PIPELINES_HOST}/lamb/v1/organizations/{slug}",
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get organization: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", f"Organization '{slug}' not found")
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put(
    "/organizations/{slug}",
    tags=["Organization Management"],
    summary="Update Organization",
    description="""Update an organization's details. Requires admin privileges.

Example Request:
```bash
curl -X PUT 'http://localhost:8000/creator/admin/organizations/engineering' \\
-H 'Authorization: Bearer <admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "name": "Updated Engineering Department",
  "status": "active"
}'
```

Example Success Response:
```json
{
  "id": 2,
  "slug": "engineering",
  "name": "Updated Engineering Department",
  "is_system": false,
  "status": "active",
  "config": {...},
  "created_at": 1678886400,
  "updated_at": 1678887000
}
```
    """,
    response_model=OrganizationResponse,
    dependencies=[Depends(security)],
    responses={
        200: {"model": OrganizationResponse, "description": "Organization updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_organization(
    request: Request,
    slug: str,
    update_data: OrganizationUpdate
):
    """Update organization details (admin only)"""
    try:
        await verify_admin_access(request)
        
        # Forward request to core organization router
        async with httpx.AsyncClient() as client:
            # Only send non-None fields
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            
            response = await client.put(
                f"{PIPELINES_HOST}/lamb/v1/organizations/{slug}",
                json=update_dict,
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to update organization: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Failed to update organization")
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/organizations/{slug}",
    tags=["Organization Management"],
    summary="Delete Organization",
    description="""Delete an organization. Cannot delete system organization. Requires admin privileges.

Example Request:
```bash
curl -X DELETE 'http://localhost:8000/creator/admin/organizations/engineering' \\
-H 'Authorization: Bearer <admin_token>'
```

Example Success Response:
```json
{
  "message": "Organization 'engineering' deleted successfully"
}
```
    """,
    dependencies=[Depends(security)],
    responses={
        200: {"description": "Organization deleted successfully"},
        400: {"model": ErrorResponse, "description": "Cannot delete system organization"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_organization(
    request: Request,
    slug: str
):
    """Delete organization (admin only, cannot delete system org)"""
    try:
        await verify_admin_access(request)
        
        # Forward request to core organization router
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{PIPELINES_HOST}/lamb/v1/organizations/{slug}",
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to delete organization: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Failed to delete organization")
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration management endpoints

@router.get(
    "/organizations/{slug}/config",
    tags=["Organization Management"],
    summary="Get Organization Configuration",
    description="""Get the full configuration of an organization.

Example Request:
```bash
curl -X GET 'http://localhost:8000/creator/admin/organizations/engineering/config' \\
-H 'Authorization: Bearer <admin_token>'
```

Example Success Response:
```json
{
  "version": "1.0",
  "setups": {
    "default": {
      "name": "Production Setup",
      "providers": {
        "openai": {
          "api_key": "encrypted:...",
          "models": ["gpt-4o-mini"]
        }
      }
    }
  },
  "features": {
    "rag_enabled": true,
    "mcp_enabled": true
  },
  "limits": {
    "usage": {
      "tokens_per_month": 1000000
    }
  }
}
```
    """,
    dependencies=[Depends(security)],
    responses={
        200: {"description": "Organization configuration retrieved"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_organization_config(
    request: Request,
    slug: str
):
    """Get organization configuration"""
    try:
        await verify_admin_access(request)
        
        # Forward request to core organization router
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PIPELINES_HOST}/lamb/v1/organizations/{slug}/config",
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get organization config: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Failed to get organization configuration")
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put(
    "/organizations/{slug}/config",
    tags=["Organization Management"],
    summary="Update Organization Configuration",
    description="""Update the full configuration of an organization.

Example Request:
```bash
curl -X PUT 'http://localhost:8000/creator/admin/organizations/engineering/config' \\
-H 'Authorization: Bearer <admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "config": {
    "version": "1.0",
    "setups": {
      "default": {
        "name": "Updated Setup",
        "providers": {
          "openai": {
            "api_key": "sk-new-key",
            "models": ["gpt-4o-mini", "gpt-4o"]
          }
        }
      }
    }
  }
}'
```

Example Success Response:
```json
{
  "message": "Configuration updated successfully",
  "config": {...}
}
```
    """,
    dependencies=[Depends(security)],
    responses={
        200: {"description": "Configuration updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid configuration"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_organization_config(
    request: Request,
    slug: str,
    config_data: Dict[str, Any]
):
    """Update organization configuration"""
    try:
        await verify_admin_access(request)
        
        # Forward request to core organization router
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{PIPELINES_HOST}/lamb/v1/organizations/{slug}/config",
                json=config_data,
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to update organization config: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Failed to update organization configuration")
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Usage and export endpoints

@router.get(
    "/organizations/{slug}/usage",
    tags=["Organization Management"],
    summary="Get Organization Usage",
    description="""Get current usage statistics for an organization.

Example Request:
```bash
curl -X GET 'http://localhost:8000/creator/admin/organizations/engineering/usage' \\
-H 'Authorization: Bearer <admin_token>'
```

Example Success Response:
```json
{
  "limits": {
    "tokens_per_month": 1000000,
    "max_assistants": 100,
    "storage_gb": 10
  },
  "current": {
    "tokens_this_month": 150000,
    "storage_used_gb": 2.5,
    "last_reset": "2024-01-01T00:00:00Z"
  },
  "organization": {
    "id": 2,
    "slug": "engineering",
    "name": "Engineering Department"
  }
}
```
    """,
    response_model=OrganizationUsage,
    dependencies=[Depends(security)],
    responses={
        200: {"model": OrganizationUsage, "description": "Usage statistics retrieved"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_organization_usage(
    request: Request,
    slug: str
):
    """Get organization usage statistics"""
    try:
        await verify_admin_access(request)
        
        # Forward request to core organization router
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PIPELINES_HOST}/lamb/v1/organizations/{slug}/usage",
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get organization usage: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Failed to get organization usage")
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/organizations/{slug}/export",
    tags=["Organization Management"],
    summary="Export Organization Configuration",
    description="""Export organization configuration as JSON.

Example Request:
```bash
curl -X GET 'http://localhost:8000/creator/admin/organizations/engineering/export' \\
-H 'Authorization: Bearer <admin_token>'
```

Example Success Response:
```json
{
  "export_version": "1.0",
  "export_date": "2024-01-15T10:00:00Z",
  "organization": {
    "slug": "engineering",
    "name": "Engineering Department",
    "config": {...}
  },
  "statistics": {
    "users_count": 25,
    "assistants_count": 150,
    "collections_count": 30
  }
}
```
    """,
    dependencies=[Depends(security)],
    responses={
        200: {"description": "Organization configuration exported"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def export_organization(
    request: Request,
    slug: str
):
    """Export organization configuration"""
    try:
        await verify_admin_access(request)
        
        # Forward request to core organization router
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PIPELINES_HOST}/lamb/v1/organizations/{slug}/export",
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to export organization: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Failed to export organization")
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting organization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/organizations/system/sync",
    tags=["Organization Management"],
    summary="Sync System Organization",
    description="""Sync the system organization ('lamb') with environment variables.

Example Request:
```bash
curl -X POST 'http://localhost:8000/creator/admin/organizations/system/sync' \\
-H 'Authorization: Bearer <admin_token>'
```

Example Success Response:
```json
{
  "message": "System organization synced successfully",
  "organization": {
    "id": 1,
    "slug": "lamb",
    "name": "LAMB System Organization",
    "config": {...}
  }
}
```
    """,
    dependencies=[Depends(security)],
    responses={
        200: {"description": "System organization synced successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "System organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def sync_system_organization(
    request: Request
):
    """Sync system organization with environment variables"""
    try:
        await verify_admin_access(request)
        
        # Forward request to core organization router
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PIPELINES_HOST}/lamb/v1/organizations/system/sync",
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to sync system organization: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Failed to sync system organization")
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing system organization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ORGANIZATION ADMIN ENDPOINTS
# These endpoints are for organization admins to manage their own organizations
# ============================================================================

# Pydantic models for organization admin endpoints
class OrgAdminUserCreate(BaseModel):
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User display name")
    password: str = Field(..., description="User password")
    enabled: bool = Field(True, description="Whether user is enabled")
    user_type: str = Field('creator', description="User type: 'creator' or 'end_user'")

class OrgAdminUserUpdate(BaseModel):
    name: Optional[str] = Field(None, description="User display name")
    enabled: Optional[bool] = Field(None, description="Whether user is enabled")

class OrgAdminPasswordChange(BaseModel):
    new_password: str = Field(..., description="New password for the user")

class OrgAdminSignupSettings(BaseModel):
    signup_enabled: bool = Field(..., description="Whether organization signup is enabled")
    signup_key: Optional[str] = Field(None, description="Organization signup key (required if signup_enabled is True)")

class OrgAdminApiSettings(BaseModel):
    model_config = {"protected_namespaces": ()}

    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_base_url: Optional[str] = Field(None, description="OpenAI API base URL (default: https://api.openai.com/v1)")
    ollama_base_url: Optional[str] = Field(None, description="Ollama server base URL (default: http://localhost:11434)")
    available_models: Optional[List[str]] = Field(None, description="List of available models (deprecated)")
    model_limits: Optional[Dict[str, Any]] = Field(None, description="Model usage limits")
    selected_models: Optional[Dict[str, List[str]]] = Field(None, description="Selected models per provider")
    default_models: Optional[Dict[str, str]] = Field(None, description="Default model per provider")

class OrgUserResponse(BaseModel):
    id: int
    email: str
    name: str
    enabled: bool
    created_at: int
    role: str = "member"

# Organization Admin Dashboard endpoint
@router.get(
    "/org-admin/dashboard",
    tags=["Organization Admin"],
    summary="Get Organization Dashboard Info",
    description="""Get dashboard information for organization admin including organization details, user count, and settings summary.

Example Request:
```bash
curl -X GET 'http://localhost:8000/creator/admin/org-admin/dashboard' \\
-H 'Authorization: Bearer <org_admin_token>'
```

Example Success Response:
```json
{
  "organization": {
    "id": 2,
    "name": "Engineering Department", 
    "slug": "engineering",
    "status": "active"
  },
  "stats": {
    "total_users": 15,
    "active_users": 12,
    "disabled_users": 3
  },
  "settings": {
    "signup_enabled": true,
    "api_configured": true,
    "total_assistants": 8
  }
}
```
    """,
    dependencies=[Depends(security)]
)
async def get_organization_dashboard(request: Request, org: Optional[str] = None):
    """Get organization admin dashboard information"""
    try:
        # If org parameter is provided, get organization by slug
        target_org_id = None
        if org:
            target_organization = db_manager.get_organization_by_slug(org)
            if not target_organization:
                raise HTTPException(status_code=404, detail=f"Organization '{org}' not found")
            target_org_id = target_organization['id']
        
        admin_info = await verify_organization_admin_access(request, target_org_id)
        org_id = admin_info['organization_id']
        organization = admin_info['organization']
        
        # Get organization statistics
        org_users = db_manager.get_organization_users(org_id)
        
        active_users = len([u for u in org_users if u.get('enabled', True)])
        disabled_users = len(org_users) - active_users
        
        # Get organization configuration
        config = organization.get('config', {})
        features = config.get('features', {})
        
        # Check API status
        from .api_status_checker import check_organization_api_status
        try:
            api_status = await check_organization_api_status(config)
        except Exception as e:
            logger.error(f"Error checking API status: {e}")
            api_status = {
                "overall_status": "error",
                "providers": {},
                "summary": {"configured_count": 0, "working_count": 0, "total_models": 0}
            }

        # Get enabled models for each provider
        setups = config.get('setups', {})
        default_setup = setups.get('default', {})
        providers = default_setup.get('providers', {})

        for provider_name in api_status.get("providers", {}):
            if provider_name in providers:
                provider_config = providers[provider_name]
                enabled_models = provider_config.get('models', [])
                api_status["providers"][provider_name]["enabled_models"] = enabled_models
                api_status["providers"][provider_name]["default_model"] = provider_config.get('default_model', '')
        
        dashboard_info = {
            "organization": {
                "id": organization['id'],
                "name": organization['name'],
                "slug": organization['slug'],
                "status": organization['status']
            },
            "stats": {
                "total_users": len(org_users),
                "active_users": active_users,
                "disabled_users": disabled_users
            },
            "settings": {
                "signup_enabled": features.get('signup_enabled', False),
                "api_configured": api_status["overall_status"] in ["working", "partial"],
                "signup_key_set": bool(features.get('signup_key'))
            },
            "api_status": api_status
        }
        
        return dashboard_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Organization User Management endpoints
@router.get(
    "/org-admin/users",
    tags=["Organization Admin - User Management"], 
    summary="List Organization Users",
    description="""List all users in the organization. Only accessible by organization admins.

Example Request:
```bash
curl -X GET 'http://localhost:8000/creator/admin/org-admin/users' \\
-H 'Authorization: Bearer <org_admin_token>'
```
    """,
    dependencies=[Depends(security)],
    response_model=List[OrgUserResponse]
)
async def list_organization_users(request: Request, org: Optional[str] = None):
    """List all users in the organization"""
    try:
        # If org parameter is provided, get organization by slug
        target_org_id = None
        if org:
            target_organization = db_manager.get_organization_by_slug(org)
            if not target_organization:
                raise HTTPException(status_code=404, detail=f"Organization '{org}' not found")
            target_org_id = target_organization['id']
        
        admin_info = await verify_organization_admin_access(request, target_org_id)
        org_id = admin_info['organization_id']
        
        users = db_manager.get_organization_users(org_id)
        owi_manager = OwiUserManager()
        
        # Get enabled status for each user from OWI auth system
        user_responses = []
        for user in users:
            enabled_status = owi_manager.get_user_status(user['email'])
            if enabled_status is None:
                enabled_status = True  # Default to enabled if status can't be determined
                logger.warning(f"Could not determine enabled status for user {user['email']}, defaulting to enabled")
            
            user_responses.append(OrgUserResponse(
                id=user['id'],
                email=user['email'],
                name=user['name'],
                enabled=enabled_status,
                created_at=user.get('joined_at', 0),
                role=user.get('role', 'member')
            ))
        
        return user_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing organization users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/org-admin/users",
    tags=["Organization Admin - User Management"],
    summary="Create Organization User",
    description="""Create a new user in the organization. Only accessible by organization admins.

Example Request:
```bash
curl -X POST 'http://localhost:8000/creator/admin/org-admin/users' \\
-H 'Authorization: Bearer <org_admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "email": "newuser@example.com",
  "name": "New User",
  "password": "securepassword123",
  "enabled": true
}'
```
    """,
    dependencies=[Depends(security)],
    response_model=OrgUserResponse
)
async def create_organization_user(request: Request, user_data: OrgAdminUserCreate):
    """Create a new user in the organization"""
    try:
        admin_info = await verify_organization_admin_access(request)
        org_id = admin_info['organization_id']
        
        # Create user with organization assignment
        user_id = db_manager.create_creator_user(
            user_email=user_data.email,
            user_name=user_data.name,
            password=user_data.password,
            organization_id=org_id,
            user_type=user_data.user_type
        )
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Assign member role
        if not db_manager.assign_organization_role(org_id, user_id, "member"):
            logger.warning(f"Failed to assign member role to user {user_id}")
        
        # Set enabled status if needed
        if not user_data.enabled:
            # Disable the user in OWI auth system
            owi_manager = OwiUserManager()
            if not owi_manager.update_user_status(user_data.email, False):
                logger.warning(f"Failed to disable user {user_data.email} after creation")
                # Note: We don't fail the entire operation since the user was created successfully
        
        return OrgUserResponse(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            enabled=user_data.enabled,
            created_at=int(time.time()),
            role="member"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put(
    "/org-admin/users/{user_id}",
    tags=["Organization Admin - User Management"],
    summary="Update Organization User",
    description="""Update a user in the organization. Only accessible by organization admins.

Example Request:
```bash
curl -X PUT 'http://localhost:8000/creator/admin/org-admin/users/123' \\
-H 'Authorization: Bearer <org_admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "name": "Updated Name",
  "enabled": false
}'
```
    """,
    dependencies=[Depends(security)]
)
async def update_organization_user(request: Request, user_id: int, user_data: OrgAdminUserUpdate):
    """Update a user in the organization"""
    try:
        admin_info = await verify_organization_admin_access(request)
        org_id = admin_info['organization_id']
        
        # Verify user belongs to this organization
        user = db_manager.get_creator_user_by_id(user_id)
        if not user or user.get('organization_id') != org_id:
            raise HTTPException(status_code=404, detail="User not found in this organization")
        
        # Update user name if provided
        if user_data.name:
            # TODO: Implement update_creator_user_name method
            pass
        
        # Update enabled status if provided
        if user_data.enabled is not None:
            # Prevent users from disabling themselves
            current_user_email = admin_info.get('email')
            if user.get('user_email') == current_user_email and not user_data.enabled:
                raise HTTPException(
                    status_code=403, 
                    detail="You cannot disable your own account. Please ask another administrator to disable your account if needed."
                )
            
            # Update user status in OWI auth system
            owi_manager = OwiUserManager()
            if not owi_manager.update_user_status(user.get('user_email'), user_data.enabled):
                logger.error(f"Failed to update enabled status for user {user.get('user_email')}")
                raise HTTPException(status_code=500, detail="Failed to update user status")
        
        return {"message": "User updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/org-admin/users/{user_id}/password",
    tags=["Organization Admin - User Management"],
    summary="Change User Password",
    description="""Change password for a user in the organization. Only accessible by organization admins.

Example Request:
```bash
curl -X POST 'http://localhost:8000/creator/admin/org-admin/users/123/password' \\
-H 'Authorization: Bearer <org_admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "new_password": "newsecurepassword123"
}'
```
    """,
    dependencies=[Depends(security)]
)
async def change_user_password(request: Request, user_id: int, password_data: OrgAdminPasswordChange):
    """Change password for a user in the organization"""
    try:
        admin_info = await verify_organization_admin_access(request)
        org_id = admin_info['organization_id']
        
        # Verify user belongs to this organization
        user = db_manager.get_creator_user_by_id(user_id)
        if not user or user.get('organization_id') != org_id:
            raise HTTPException(status_code=404, detail="User not found in this organization")
        
        # Change password using UserCreatorManager (same as system admin)
        from .user_creator import UserCreatorManager
        user_creator = UserCreatorManager()
        user_email = user.get('user_email')  # Fix: use 'user_email' key from database
        result = await user_creator.update_user_password(user_email, password_data.new_password)
        
        if not result["success"]:
            logger.error(f"Failed to update password for user {user_email}: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to update user password'))
        
        logger.info(f"Organization admin {admin_info.get('email')} changed password for user {user_email}")
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing user password: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/org-admin/users/{user_id}",
    tags=["Organization Admin - User Management"],
    summary="Delete Organization User",
    description="""Delete a user from the organization. Only accessible by organization admins.
    
    This permanently removes the user from both the LAMB database and the authentication system.
    The user cannot be an organization admin/owner, and admins cannot delete themselves.

Example Request:
```bash
curl -X DELETE 'http://localhost:8000/creator/admin/org-admin/users/123' \\
-H 'Authorization: Bearer <org_admin_token>'
```
    """,
    dependencies=[Depends(security)]
)
async def delete_organization_user(request: Request, user_id: int, org: Optional[str] = None):
    """Delete a user from the organization"""
    try:
        # If org parameter is provided, get organization by slug
        target_org_id = None
        if org:
            target_organization = db_manager.get_organization_by_slug(org)
            if not target_organization:
                raise HTTPException(status_code=404, detail=f"Organization '{org}' not found")
            target_org_id = target_organization['id']
        
        admin_info = await verify_organization_admin_access(request, target_org_id)
        org_id = admin_info['organization_id']
        
        # Verify user belongs to this organization
        user = db_manager.get_creator_user_by_id(user_id)
        if not user or user.get('organization_id') != org_id:
            raise HTTPException(status_code=404, detail="User not found in this organization")
        
        user_email = user.get('user_email')
        
        # Prevent users from deleting themselves
        current_user_email = admin_info.get('email')
        if user_email == current_user_email:
            raise HTTPException(
                status_code=403, 
                detail="You cannot delete your own account. Please ask another administrator to delete your account if needed."
            )
        
        # Check if the user is an admin/owner of this organization
        user_role = db_manager.get_user_organization_role(user_id, org_id)
        if user_role in ['owner', 'admin']:
            raise HTTPException(
                status_code=403,
                detail="Cannot delete an organization admin or owner. Please remove their admin privileges first."
            )
        
        # Delete user from OWI auth system (if exists)
        owi_manager = OwiUserManager()
        owi_deleted = owi_manager.delete_user(user_email)
        if not owi_deleted:
            logger.warning(f"User {user_email} was not found in OWI auth system (may only exist in LAMB)")
        
        # Delete user from LAMB database
        if not db_manager.delete_creator_user(user_id):
            logger.error(f"Failed to delete user {user_email} from LAMB database")
            raise HTTPException(status_code=500, detail="Failed to delete user from LAMB database")
        
        logger.info(f"Organization admin {current_user_email} deleted user {user_email} (ID: {user_id}) from organization {org_id}")
        return {"message": f"User {user_email} has been permanently deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Organization Settings Management
@router.get(
    "/org-admin/settings/signup", 
    tags=["Organization Admin - Settings"],
    summary="Get Signup Settings",
    description="Get current signup settings for the organization",
    dependencies=[Depends(security)]
)
async def get_signup_settings(request: Request, org: Optional[str] = None):
    """Get organization signup settings"""
    try:
        # If org parameter is provided, get organization by slug
        target_org_id = None
        if org:
            target_organization = db_manager.get_organization_by_slug(org)
            if not target_organization:
                raise HTTPException(status_code=404, detail=f"Organization '{org}' not found")
            target_org_id = target_organization['id']
        
        admin_info = await verify_organization_admin_access(request, target_org_id)
        organization = admin_info['organization']
        
        config = organization.get('config', {})
        features = config.get('features', {})
        
        return {
            "signup_enabled": features.get('signup_enabled', False),
            "signup_key": features.get('signup_key', ''),
            "signup_key_masked": bool(features.get('signup_key'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting signup settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put(
    "/org-admin/settings/signup",
    tags=["Organization Admin - Settings"],
    summary="Update Signup Settings", 
    description="""Update signup settings for the organization.

Example Request:
```bash
curl -X PUT 'http://localhost:8000/creator/admin/org-admin/settings/signup' \\
-H 'Authorization: Bearer <org_admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "signup_enabled": true,
  "signup_key": "my-org-signup-key-2024"
}'
```
    """,
    dependencies=[Depends(security)]
)
async def update_signup_settings(request: Request, settings: OrgAdminSignupSettings, org: Optional[str] = None):
    """Update organization signup settings"""
    try:
        # If org parameter is provided, get organization by slug
        target_org_id = None
        if org:
            target_organization = db_manager.get_organization_by_slug(org)
            if not target_organization:
                raise HTTPException(status_code=404, detail=f"Organization '{org}' not found")
            target_org_id = target_organization['id']
        
        admin_info = await verify_organization_admin_access(request, target_org_id)
        org_id = admin_info['organization_id']
        organization = admin_info['organization']
        
        # Validate signup key if signup is enabled
        if settings.signup_enabled:
            if not settings.signup_key or len(settings.signup_key.strip()) == 0:
                raise HTTPException(status_code=400, detail="Signup key is required when signup is enabled")
            
            # Validate signup key format
            is_valid, error_msg = db_manager.validate_signup_key_format(settings.signup_key)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid signup key: {error_msg}")
            
            # Check uniqueness (excluding current organization)
            if not db_manager.validate_signup_key_uniqueness(settings.signup_key, exclude_org_id=org_id):
                raise HTTPException(status_code=400, detail="Signup key already exists in another organization")
        
        # Update organization configuration
        config = organization.get('config', {})
        if 'features' not in config:
            config['features'] = {}
        
        config['features']['signup_enabled'] = settings.signup_enabled
        if settings.signup_enabled and settings.signup_key:
            config['features']['signup_key'] = settings.signup_key.strip()
        elif 'signup_key' in config['features']:
            del config['features']['signup_key']
        
        # Save configuration
        if not db_manager.update_organization_config(org_id, config):
            raise HTTPException(status_code=500, detail="Failed to update signup settings")
        
        return {"message": "Signup settings updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating signup settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/org-admin/settings/api",
    tags=["Organization Admin - Settings"], 
    summary="Get API Settings",
    description="Get current API configuration for the organization",
    dependencies=[Depends(security)]
)
async def get_api_settings(request: Request, org: Optional[str] = None):
    """Get organization API settings"""
    try:
        # If org parameter is provided, get organization by slug
        target_org_id = None
        if org:
            target_organization = db_manager.get_organization_by_slug(org)
            if not target_organization:
                raise HTTPException(status_code=404, detail=f"Organization '{org}' not found")
            target_org_id = target_organization['id']
        
        admin_info = await verify_organization_admin_access(request, target_org_id)
        organization = admin_info['organization']
        
        config = organization.get('config', {})
        setups = config.get('setups', {})
        default_setup = setups.get('default', {})
        providers = default_setup.get('providers', {})
        
        # Get API status to show available models
        from .api_status_checker import check_organization_api_status
        try:
            api_status = await check_organization_api_status(config)
        except Exception as e:
            logger.error(f"Error checking API status for settings: {e}")
            api_status = {"providers": {}}
        
        # Get currently selected models and default models for each provider
        selected_models = {}
        default_models = {}
        available_models = {}

        for provider_name, provider_status in api_status.get("providers", {}).items():
            if provider_status.get("status") == "working":
                available_models[provider_name] = provider_status.get("models", [])

                # Get selected models from provider config
                provider_config = providers.get(provider_name, {})
                selected_models[provider_name] = provider_config.get("models", [])

                # If no models are explicitly selected, default to all available
                if not selected_models[provider_name] and available_models[provider_name]:
                    selected_models[provider_name] = available_models[provider_name].copy()

                # Get default model from provider config
                default_models[provider_name] = provider_config.get("default_model", "")
        
        return {
            "openai_api_key_set": bool(providers.get('openai', {}).get('api_key')),
            "openai_base_url": providers.get('openai', {}).get('base_url', 'https://api.openai.com/v1'),
            "ollama_base_url": providers.get('ollama', {}).get('base_url', 'http://localhost:11434'),
            "available_models": available_models,
            "selected_models": selected_models,
            "default_models": default_models,
            "api_status": api_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put(
    "/org-admin/settings/api",
    tags=["Organization Admin - Settings"],
    summary="Update API Settings",
    description="""Update API configuration for the organization.

Example Request:
```bash
curl -X PUT 'http://localhost:8000/creator/admin/org-admin/settings/api' \\
-H 'Authorization: Bearer <org_admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "openai_api_key": "sk-...",
  "available_models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
  "model_limits": {
    "gpt-4": {"daily_limit": 100, "per_user_limit": 10},
    "gpt-3.5-turbo": {"daily_limit": 1000, "per_user_limit": 50}
  }
}'
```
    """,
    dependencies=[Depends(security)]
)
async def update_api_settings(request: Request, settings: OrgAdminApiSettings, org: Optional[str] = None):
    """Update organization API settings"""
    try:
        # If org parameter is provided, get organization by slug
        target_org_id = None
        if org:
            target_organization = db_manager.get_organization_by_slug(org)
            if not target_organization:
                raise HTTPException(status_code=404, detail=f"Organization '{org}' not found")
            target_org_id = target_organization['id']
        
        admin_info = await verify_organization_admin_access(request, target_org_id)
        org_id = admin_info['organization_id']
        organization = admin_info['organization']
        
        # Update organization configuration
        config = organization.get('config', {})
        
        # Ensure setups structure exists
        if 'setups' not in config:
            config['setups'] = {}
        if 'default' not in config['setups']:
            config['setups']['default'] = {}
        if 'providers' not in config['setups']['default']:
            config['setups']['default']['providers'] = {}
        
        providers = config['setups']['default']['providers']
        
        # Update OpenAI configuration
        if settings.openai_api_key:
            if 'openai' not in providers:
                providers['openai'] = {}
            providers['openai']['api_key'] = settings.openai_api_key
        
        if settings.openai_base_url:
            if 'openai' not in providers:
                providers['openai'] = {}
            providers['openai']['base_url'] = settings.openai_base_url.rstrip('/')
            logger.info(f"Updated OpenAI base URL to: {settings.openai_base_url}")
        
        # Update Ollama configuration
        if settings.ollama_base_url:
            if 'ollama' not in providers:
                providers['ollama'] = {}
            providers['ollama']['base_url'] = settings.ollama_base_url.rstrip('/')
            logger.info(f"Updated Ollama base URL to: {settings.ollama_base_url}")
        
        # Update selected models per provider
        if settings.selected_models is not None:
            for provider_name, model_list in settings.selected_models.items():
                if provider_name not in providers:
                    providers[provider_name] = {}
                providers[provider_name]['models'] = model_list
                logger.info(f"Updated {provider_name} enabled models: {len(model_list)} models selected")

        # Update default models per provider
        if settings.default_models is not None:
            for provider_name, default_model in settings.default_models.items():
                if provider_name not in providers:
                    providers[provider_name] = {}
                providers[provider_name]['default_model'] = default_model
                logger.info(f"Updated {provider_name} default model: {default_model}")

            # Auto-manage default models: ensure default model is in enabled models list
            for provider_name, default_model in settings.default_models.items():
                if default_model and provider_name in settings.selected_models:
                    enabled_models = settings.selected_models[provider_name]
                    if default_model not in enabled_models:
                        if enabled_models:
                            # Auto-select first enabled model as default
                            new_default = enabled_models[0]
                            providers[provider_name]['default_model'] = new_default
                            settings.default_models[provider_name] = new_default
                            logger.info(f"Auto-corrected {provider_name} default model from '{default_model}' to '{new_default}' (not in enabled models)")
                        else:
                            # No models enabled, clear default
                            providers[provider_name]['default_model'] = ""
                            settings.default_models[provider_name] = ""
                            logger.info(f"Cleared {provider_name} default model (no models enabled)")

            # Auto-update assistant_defaults if current default model is not in enabled list
            if 'assistant_defaults' not in config:
                config['assistant_defaults'] = {}

            assistant_defaults = config['assistant_defaults']
            current_connector = assistant_defaults.get('connector')
            current_llm = assistant_defaults.get('llm')

            # Check if current connector's default model is still valid
            if current_connector and current_connector in settings.selected_models:
                enabled_models_for_connector = settings.selected_models[current_connector]

                # If current llm is not in the newly enabled models list
                if current_llm and current_llm not in enabled_models_for_connector:
                    if enabled_models_for_connector:  # If there are models enabled
                        # Update to first enabled model
                        new_default_llm = enabled_models_for_connector[0]
                        assistant_defaults['llm'] = new_default_llm
                        config['assistant_defaults'] = assistant_defaults
                        logger.info(f"Auto-updated assistant_defaults.llm from '{current_llm}' to '{new_default_llm}' (not in enabled models for {current_connector})")
                    else:
                        # No models enabled for this connector - clear the default
                        logger.warning(f"No models enabled for connector '{current_connector}', clearing assistant_defaults.llm")
                        assistant_defaults['llm'] = ''
                        config['assistant_defaults'] = assistant_defaults
        
        # Legacy support: Update available models (deprecated)
        if settings.available_models is not None:
            if 'models' not in config:
                config['models'] = {}
            config['models']['available'] = settings.available_models
        
        # Update model limits
        if settings.model_limits is not None:
            if 'models' not in config:
                config['models'] = {}
            config['models']['limits'] = settings.model_limits
        
        # Save configuration
        if not db_manager.update_organization_config(org_id, config):
            raise HTTPException(status_code=500, detail="Failed to update API settings")
        
        return {"message": "API settings updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating API settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ORGANIZATION ADMIN ASSISTANT MANAGEMENT ENDPOINTS
# These endpoints allow organization admins to view and manage access to 
# assistants within their organization
# ============================================================================

class AssistantAccessUpdate(BaseModel):
    user_emails: List[str] = Field(..., description="List of user emails to grant/revoke access")
    action: str = Field(..., description="Action to perform: 'grant' or 'revoke'")

class AssistantListItem(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner: str
    published: bool
    group_id: Optional[str]
    created_at: int

class AssistantAccessInfo(BaseModel):
    assistant: AssistantListItem
    users_with_access: List[str]  # emails
    organization_users: List[Dict[str, Any]]  # all org users for selection

@router.get(
    "/org-admin/assistants",
    tags=["Organization Admin - Assistant Management"],
    summary="List All Organization Assistants",
    description="""List all assistants in the organization admin's organization.
    
Example Request:
```bash
curl -X GET 'http://localhost:8000/creator/admin/org-admin/assistants' \\
-H 'Authorization: Bearer <org_admin_token>'
```

Example Response:
```json
{
  "assistants": [
    {
      "id": 1,
      "name": "Math_Tutor",
      "description": "Helps with math problems",
      "owner": "prof@university.edu",
      "published": true,
      "group_id": "assistant_1",
      "created_at": 1678886400
    }
  ]
}
```
    """,
    dependencies=[Depends(security)]
)
async def list_organization_assistants(request: Request, org: Optional[str] = None):
    """List all assistants in the organization"""
    try:
        # If org parameter is provided, get organization by slug
        target_org_id = None
        if org:
            target_organization = db_manager.get_organization_by_slug(org)
            if not target_organization:
                raise HTTPException(status_code=404, detail=f"Organization '{org}' not found")
            target_org_id = target_organization['id']
        
        admin_info = await verify_organization_admin_access(request, target_org_id)
        org_id = admin_info['organization_id']
        
        # Get all assistants in organization
        assistants = db_manager.get_assistants_by_organization(org_id)
        
        # Format response
        assistants_list = []
        for asst in assistants:
            assistants_list.append(AssistantListItem(
                id=asst['id'],
                name=asst['name'],
                description=asst.get('description'),
                owner=asst['owner'],
                published=asst.get('published', False),
                group_id=asst.get('group_id'),
                created_at=asst.get('created_at', 0)
            ))
        
        return {"assistants": assistants_list}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing organization assistants: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/org-admin/assistants/{assistant_id}/access",
    tags=["Organization Admin - Assistant Management"],
    summary="Get Assistant Access Info",
    description="""Get information about who has access to an assistant and all organization users.
    
Example Request:
```bash
curl -X GET 'http://localhost:8000/creator/admin/org-admin/assistants/123/access' \\
-H 'Authorization: Bearer <org_admin_token>'
```

Example Response:
```json
{
  "assistant": {
    "id": 123,
    "name": "Math_Tutor",
    "owner": "prof@university.edu",
    "published": true,
    "group_id": "assistant_123"
  },
  "users_with_access": [
    "prof@university.edu",
    "student1@university.edu"
  ],
  "organization_users": [
    {
      "id": 1,
      "email": "prof@university.edu",
      "name": "Professor Smith",
      "user_type": "creator",
      "is_owner": true
    },
    {
      "id": 2,
      "email": "student1@university.edu",
      "name": "Student One",
      "user_type": "end_user",
      "is_owner": false
    }
  ]
}
```
    """,
    dependencies=[Depends(security)],
    response_model=AssistantAccessInfo
)
async def get_assistant_access(request: Request, assistant_id: int, org: Optional[str] = None):
    """Get access information for an assistant"""
    try:
        # If org parameter is provided, get organization by slug
        target_org_id = None
        if org:
            target_organization = db_manager.get_organization_by_slug(org)
            if not target_organization:
                raise HTTPException(status_code=404, detail=f"Organization '{org}' not found")
            target_org_id = target_organization['id']
        
        admin_info = await verify_organization_admin_access(request, target_org_id)
        org_id = admin_info['organization_id']
        
        # Get assistant and verify it belongs to this organization
        assistants = db_manager.get_assistants_by_organization(org_id)
        assistant = next((a for a in assistants if a['id'] == assistant_id), None)
        
        if not assistant:
            raise HTTPException(
                status_code=404, 
                detail="Assistant not found in this organization"
            )
        
        # Get users with access (from OWI group)
        users_with_access = []
        if assistant.get('group_id'):
            from lamb.owi_bridge.owi_group import OwiGroupManager
            group_manager = OwiGroupManager()
            users_with_access = group_manager.get_group_users_by_emails(assistant['group_id'])
        
        # Get all organization users
        org_users = db_manager.get_organization_users(org_id)
        organization_users = []
        for user in org_users:
            organization_users.append({
                "id": user['id'],
                "email": user['email'],
                "name": user['name'],
                "user_type": user.get('user_type', 'creator'),
                "is_owner": user['email'] == assistant['owner']
            })
        
        return AssistantAccessInfo(
            assistant=AssistantListItem(
                id=assistant['id'],
                name=assistant['name'],
                description=assistant.get('description'),
                owner=assistant['owner'],
                published=assistant.get('published', False),
                group_id=assistant.get('group_id'),
                created_at=assistant.get('created_at', 0)
            ),
            users_with_access=users_with_access,
            organization_users=organization_users
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assistant access info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put(
    "/org-admin/assistants/{assistant_id}/access",
    tags=["Organization Admin - Assistant Management"],
    summary="Update Assistant Access",
    description="""Grant or revoke access to an assistant for multiple users.
    The owner cannot be removed from access.
    
Example Request (Grant Access):
```bash
curl -X PUT 'http://localhost:8000/creator/admin/org-admin/assistants/123/access' \\
-H 'Authorization: Bearer <org_admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "user_emails": ["student1@university.edu", "student2@university.edu"],
  "action": "grant"
}'
```

Example Request (Revoke Access):
```bash
curl -X PUT 'http://localhost:8000/creator/admin/org-admin/assistants/123/access' \\
-H 'Authorization: Bearer <org_admin_token>' \\
-H 'Content-Type: application/json' \\
-d '{
  "user_emails": ["student1@university.edu"],
  "action": "revoke"
}'
```

Example Success Response:
```json
{
  "message": "Access updated successfully",
  "results": {
    "added": ["student1@university.edu", "student2@university.edu"],
    "removed": [],
    "already_member": [],
    "not_found": [],
    "errors": []
  }
}
```
    """,
    dependencies=[Depends(security)]
)
async def update_assistant_access(
    request: Request, 
    assistant_id: int, 
    access_update: AssistantAccessUpdate,
    org: Optional[str] = None
):
    """Grant or revoke access to an assistant for users"""
    try:
        # If org parameter is provided, get organization by slug
        target_org_id = None
        if org:
            target_organization = db_manager.get_organization_by_slug(org)
            if not target_organization:
                raise HTTPException(status_code=404, detail=f"Organization '{org}' not found")
            target_org_id = target_organization['id']
        
        admin_info = await verify_organization_admin_access(request, target_org_id)
        org_id = admin_info['organization_id']
        
        # Validate action
        if access_update.action not in ['grant', 'revoke']:
            raise HTTPException(
                status_code=400, 
                detail="Action must be 'grant' or 'revoke'"
            )
        
        # Get assistant and verify it belongs to this organization
        assistants = db_manager.get_assistants_by_organization(org_id)
        assistant = next((a for a in assistants if a['id'] == assistant_id), None)
        
        if not assistant:
            raise HTTPException(
                status_code=404, 
                detail="Assistant not found in this organization"
            )
        
        # Check if assistant has a group
        if not assistant.get('group_id'):
            raise HTTPException(
                status_code=400,
                detail="Assistant does not have an OWI group. Only published assistants can have access managed."
            )
        
        # Prevent owner from being removed
        if access_update.action == 'revoke' and assistant['owner'] in access_update.user_emails:
            raise HTTPException(
                status_code=403,
                detail="Cannot remove the assistant owner from access"
            )
        
        # Verify all users belong to the organization
        org_users = db_manager.get_organization_users(org_id)
        org_user_emails = {user['email'] for user in org_users}
        
        for email in access_update.user_emails:
            if email not in org_user_emails:
                raise HTTPException(
                    status_code=400,
                    detail=f"User {email} does not belong to this organization"
                )
        
        # Perform the action
        from lamb.owi_bridge.owi_group import OwiGroupManager
        group_manager = OwiGroupManager()
        
        if access_update.action == 'grant':
            result = group_manager.add_users_to_group(
                assistant['group_id'], 
                access_update.user_emails
            )
        else:  # revoke
            result = group_manager.remove_users_from_group(
                assistant['group_id'], 
                access_update.user_emails
            )
        
        if result.get('status') == 'error':
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update access: {result.get('error')}"
            )
        
        return {
            "message": "Access updated successfully",
            "results": result.get('results', {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assistant access: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Assistant Defaults Management Endpoints

@router.get("/organizations/{slug}/assistant-defaults")
async def get_organization_assistant_defaults(
    slug: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get assistant defaults for a specific organization
    
    This endpoint retrieves the assistant_defaults configuration for the specified organization.
    Only accessible by organization admins or system admins.
    
    Args:
        slug: Organization slug identifier
        credentials: Bearer token for authentication
    
    Returns:
        Dict containing the assistant_defaults object
    
    Raises:
        HTTPException: 401 if unauthorized, 404 if organization not found, 500 on server error
    """
    try:
        # Get authorization header
        auth_header = f"Bearer {credentials.credentials}"
        
        # Check admin authorization
        user_info = get_user_organization_admin_info(auth_header)
        if not user_info:
            raise HTTPException(status_code=401, detail="Admin access required")
        
        # Forward request to lamb API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PIPELINES_HOST}/lamb/v1/organizations/{slug}/assistant-defaults",
                headers={"Authorization": f"Bearer {LAMB_BEARER_TOKEN}"}
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Organization not found")
            elif response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch assistant defaults")
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching assistant defaults for {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/organizations/{slug}/assistant-defaults")
async def update_organization_assistant_defaults(
    slug: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update assistant defaults for a specific organization
    
    This endpoint updates the assistant_defaults configuration for the specified organization.
    Only accessible by organization admins or system admins.
    
    Args:
        slug: Organization slug identifier
        request: Request containing the assistant_defaults JSON in body
        credentials: Bearer token for authentication
    
    Returns:
        Dict with success message
    
    Raises:
        HTTPException: 401 if unauthorized, 404 if organization not found, 500 on server error
    """
    try:
        # Get authorization header
        auth_header = f"Bearer {credentials.credentials}"
        
        # Check admin authorization
        user_info = get_user_organization_admin_info(auth_header)
        if not user_info:
            raise HTTPException(status_code=401, detail="Admin access required")
        
        # Get request body
        body = await request.json()
        
        # Forward request to lamb API (pass the body as-is)
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{PIPELINES_HOST}/lamb/v1/organizations/{slug}/assistant-defaults",
                headers={
                    "Authorization": f"Bearer {LAMB_BEARER_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=body
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Organization not found")
            elif response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to update assistant defaults")
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assistant defaults for {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))