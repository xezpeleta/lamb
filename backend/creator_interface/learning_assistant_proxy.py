"""
Learning Assistant Proxy Service

This module provides a secure proxy service for frontend chat interfaces to access
learning assistants without exposing API keys. It uses proper user authentication
and access control while maintaining OpenAI API compatibility.

Security Features:
- User token authentication (no exposed API keys)
- Assistant access control based on ownership/organization
- Full streaming and non-streaming support
- Audit trail for all assistant interactions
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Path
from fastapi.responses import StreamingResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .assistant_router import get_creator_user_from_token
from lamb.completions.main import run_lamb_assistant
from lamb.database_manager import LambDatabaseManager
import json
import logging
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Initialize router and security
router = APIRouter(tags=["Learning Assistant Proxy"])
security = HTTPBearer()
db_manager = LambDatabaseManager()


def verify_assistant_access(user: Dict[str, Any], assistant_id: int) -> bool:
    """
    Verify user has access to the specified assistant.
    
    Access is granted if:
    1. User is the owner of the assistant
    2. User belongs to the same organization as the assistant
    3. Assistant is in system organization and user has system access
    
    Args:
        user: Authenticated user information
        assistant_id: ID of the assistant to access
        
    Returns:
        bool: True if user has access, False otherwise
    """
    try:
        # Get assistant details
        assistant = db_manager.get_assistant_by_id(assistant_id)
        if not assistant:
            logger.warning(f"Assistant {assistant_id} not found")
            return False
        
        # Check if user is owner
        if assistant.owner == user['email']:
            logger.debug(f"User {user['email']} is owner of assistant {assistant_id}")
            return True
        
        # Check organization membership
        user_org = user.get('organization', {})
        assistant_org_id = getattr(assistant, 'organization_id', None)
        
        if user_org.get('id') == assistant_org_id:
            logger.debug(f"User {user['email']} has org access to assistant {assistant_id}")
            return True
        
        # Check if assistant is in system organization and user has system access
        if assistant_org_id == 1:  # System organization ID is typically 1
            system_org = db_manager.get_organization_by_slug("lamb")
            if system_org and user_org.get('id') == system_org.get('id'):
                logger.debug(f"User {user['email']} has system org access to assistant {assistant_id}")
                return True
        
        logger.warning(f"User {user['email']} denied access to assistant {assistant_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error checking assistant access: {str(e)}")
        return False


@router.post(
    "/assistant/{assistant_id}/chat/completions",
    summary="Chat with Learning Assistant",
    description="""
    Secure proxy endpoint for chat completions with learning assistants.
    
    This endpoint provides OpenAI-compatible chat completions while maintaining
    proper security through user authentication and access control.
    
    Features:
    - User token authentication (no API key exposure)
    - Assistant access control based on ownership/organization
    - Full streaming and non-streaming support
    - OpenAI-compatible request/response format
    
    Example Request:
    ```bash
    curl -X POST 'http://localhost:9099/creator/assistant/1/chat/completions' \\
    -H 'Authorization: Bearer <user_token>' \\
    -H 'Content-Type: application/json' \\
    -d '{
      "messages": [
        {"role": "user", "content": "Hello, how can you help me?"}
      ],
      "stream": false
    }'
    ```
    
    Example Streaming Request:
    ```bash
    curl -X POST 'http://localhost:9099/creator/assistant/1/chat/completions' \\
    -H 'Authorization: Bearer <user_token>' \\
    -H 'Content-Type: application/json' \\
    -d '{
      "messages": [
        {"role": "user", "content": "Tell me a story"}
      ],
      "stream": true
    }' --no-buffer
    ```
    """,
    dependencies=[Depends(security)]
)
async def proxy_assistant_chat(
    assistant_id: int = Path(..., description="ID of the assistant to chat with"),
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Proxy endpoint for chat completions with user authentication and access control.
    
    This endpoint eliminates the need for exposed API keys by using proper user
    authentication while maintaining full OpenAI API compatibility.
    """
    try:
        # 1. Authenticate user
        auth_header = f"Bearer {credentials.credentials}"
        creator_user = get_creator_user_from_token(auth_header)
        
        if not creator_user:
            logger.warning(f"Invalid authentication attempt for assistant {assistant_id}")
            raise HTTPException(
                status_code=401, 
                detail="Invalid authentication. Please check your token."
            )
        
        logger.info(f"User {creator_user['email']} requesting access to assistant {assistant_id}")
        
        # 2. Verify assistant access
        if not verify_assistant_access(creator_user, assistant_id):
            logger.warning(f"User {creator_user['email']} denied access to assistant {assistant_id}")
            raise HTTPException(
                status_code=403,
                detail="Access denied. You don't have permission to use this assistant."
            )
        
        # 3. Parse request body
        try:
            body = await request.json()
        except Exception as e:
            logger.error(f"Failed to parse request body: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON in request body"
            )
        
        # 4. Validate required fields
        if "messages" not in body:
            raise HTTPException(
                status_code=400,
                detail="Missing 'messages' field in request body"
            )
        
        # 5. Log the request for audit trail
        stream_mode = body.get("stream", False)
        logger.info(f"Processing {'streaming' if stream_mode else 'non-streaming'} "
                   f"completion for user {creator_user['email']} with assistant {assistant_id}")
        
        # 6. Call internal completion system
        # The run_lamb_assistant function handles all the processing and returns
        # the appropriate response format (streaming or non-streaming)
        response = await run_lamb_assistant(
            request=body,
            assistant=assistant_id,
            headers=None  # Internal call, no need for special headers
        )
        
        logger.info(f"Successfully processed completion for user {creator_user['email']} "
                   f"with assistant {assistant_id}")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (authentication, authorization, validation errors)
        raise
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in proxy_assistant_chat: {str(e)}", exc_info=True)
        
        # Check if this was a streaming request for appropriate error response
        try:
            body = await request.json()
            stream_mode = body.get("stream", False)
        except:
            stream_mode = False
        
        error_detail = {
            "error": {
                "message": "Internal server error occurred while processing your request",
                "type": "internal_server_error",
                "param": None,
                "code": None
            }
        }
        
        if stream_mode:
            # Return streaming error response
            error_sse = f"data: {json.dumps(error_detail['error'])}\\n\\n"
            return StreamingResponse(
                iter([error_sse.encode()]),
                media_type="text/event-stream",
                status_code=500
            )
        else:
            # Return JSON error response
            raise HTTPException(
                status_code=500,
                detail=error_detail["error"]["message"]
            )


@router.get(
    "/assistant/{assistant_id}/info",
    summary="Get Assistant Information",
    description="""
    Get basic information about a learning assistant if user has access.
    
    This endpoint allows users to verify they have access to an assistant
    and get basic information about it.
    """,
    dependencies=[Depends(security)]
)
async def get_assistant_info(
    assistant_id: int = Path(..., description="ID of the assistant"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get assistant information with access control.
    """
    try:
        # 1. Authenticate user
        auth_header = f"Bearer {credentials.credentials}"
        creator_user = get_creator_user_from_token(auth_header)
        
        if not creator_user:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # 2. Verify assistant access
        if not verify_assistant_access(creator_user, assistant_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied. You don't have permission to view this assistant."
            )
        
        # 3. Get assistant details
        assistant = db_manager.get_assistant_by_id(assistant_id)
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        # 4. Return basic info (don't expose sensitive details)
        return {
            "id": assistant.id,
            "name": assistant.name,
            "description": assistant.description,
            "owner": assistant.owner,
            "created_at": str(assistant.created_at) if hasattr(assistant, 'created_at') else None,
            "updated_at": str(assistant.updated_at) if hasattr(assistant, 'updated_at') else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assistant info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
