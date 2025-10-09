# Backend: LTI Integration

**Purpose:** Learning Tools Interoperability (LTI) for LMS integration and publishing  
**Related Docs:** `backend_architecture.md`, `backend_authentication.md`, `frontend_assistants_management.md`

---

## Overview

LTI (Learning Tools Interoperability) enables LAMB assistants to be embedded in Learning Management Systems (LMS) like Canvas, Moodle, Blackboard:
- **LTI 1.1 compliant** - Works with most LMS platforms
- **OAuth 1.0 signature validation** - Secure launches
- **Automatic user provisioning** - Students auto-created on first launch
- **Group-based access control** - Each assistant has own OWI group
- **Seamless redirect** - Students go straight to chat interface

---

## Publishing Flow

```
┌──────────┐                ┌──────────────┐              ┌────────────┐
│ Educator │                │     LAMB     │              │    OWI     │
│          │                │              │              │            │
└────┬─────┘                └──────┬───────┘              └─────┬──────┘
     │                             │                            │
     │ Publish Assistant           │                            │
     ├────────────────────────────►│                            │
     │                             │                            │
     │                             │ Create OWI Group           │
     │                             ├───────────────────────────►│
     │                             │                            │
     │                             │ Register Assistant as Model│
     │                             ├───────────────────────────►│
     │                             │                            │
     │                             │ Update Assistant in DB     │
     │                             │ (published=true, group_id) │
     │                             │                            │
     │ Return LTI Config           │                            │
     │◄────────────────────────────┤                            │
     │ (consumer key, secret, XML) │                            │
```

---

## Publish Endpoint

**Endpoint:** `POST /creator/assistant/{id}/publish`

**File:** `/backend/creator_interface/assistant_router.py`

```python
@router.post("/assistant/{assistant_id}/publish")
async def publish_assistant(
    assistant_id: int,
    publish_data: PublishRequest,
    request: Request
):
    """
    Publish assistant for LTI integration
    
    Args:
        publish_data: {
            group_name: "CS101 Assistant",
            oauth_consumer_name: "cs101_assistant"
        }
    
    Process:
        1. Validate user owns assistant
        2. Create OWI group
        3. Register assistant as OWI model
        4. Generate OAuth credentials
        5. Update assistant (published=true)
        6. Return LTI configuration
    """
    # Validate user
    creator_user = get_creator_user_from_token(request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get assistant
    db_manager = LambDatabaseManager()
    assistant = db_manager.get_assistant_by_id(assistant_id)
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    if assistant['owner'] != creator_user['email']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate group name and consumer name
    group_name = publish_data.group_name or f"{assistant['name']} Group"
    oauth_consumer_name = publish_data.oauth_consumer_name or f"assistant_{assistant_id}"
    
    # Create OWI group
    group_manager = OwiGroupManager()
    owi_user_manager = OwiUserManager()
    
    # Get creator's OWI user
    creator_owi_user = owi_user_manager.get_user_by_email(creator_user['email'])
    
    group_id = group_manager.create_group(
        name=group_name,
        description=f"Access group for {assistant['name']}",
        user_id=creator_owi_user['id']
    )
    
    # Register assistant as OWI model
    model_manager = OwiModelManager()
    
    lamb_base_url = os.getenv("LAMB_BASE_URL", "http://localhost:9099")
    model_id = f"lamb_assistant.{assistant_id}"
    
    model_manager.create_model(
        model_id=model_id,
        name=assistant['name'],
        base_model_id=f"{lamb_base_url}/v1/chat/completions",
        user_id=creator_owi_user['id'],
        description=assistant['description']
    )
    
    # Generate OAuth shared secret
    oauth_secret = secrets.token_urlsafe(32)
    
    # Store OAuth credentials (simplified - in production use secure storage)
    # For now, we'll use a simple approach
    
    # Update assistant
    db_manager.update_assistant(
        assistant_id,
        {
            "published": True,
            "published_at": int(time.time()),
            "group_id": group_id,
            "group_name": group_name,
            "oauth_consumer_name": oauth_consumer_name
        }
    )
    
    # Store OAuth secret (in production, use encrypted storage)
    # Here we use a simple file or database approach
    # TODO: Implement secure OAuth secret storage
    
    # Generate LTI configuration
    public_url = os.getenv("LAMB_PUBLIC_URL", "http://localhost:9099")
    launch_url = f"{public_url}/lamb/simple_lti/launch"
    
    lti_config = {
        "launch_url": launch_url,
        "consumer_key": oauth_consumer_name,
        "shared_secret": oauth_secret,
        "custom_parameters": {
            "assistant_id": str(assistant_id)
        },
        "xml_config": generate_lti_xml(
            title=assistant['name'],
            description=assistant['description'],
            launch_url=launch_url,
            assistant_id=assistant_id
        )
    }
    
    return {
        "success": True,
        "lti_config": lti_config,
        "group_id": group_id,
        "model_id": model_id
    }
```

---

## LTI Launch Flow

```
┌─────────┐            ┌─────────┐           ┌──────────┐         ┌────────┐
│ Student │            │   LMS   │           │   LAMB   │         │  OWI   │
│         │            │         │           │          │         │        │
└────┬────┘            └────┬────┘           └─────┬────┘         └───┬────┘
     │                      │                      │                  │
     │ Click LTI Activity   │                      │                  │
     ├─────────────────────►│                      │                  │
     │                      │                      │                  │
     │                      │ LTI Launch POST      │                  │
     │                      │ (OAuth signed)       │                  │
     │                      ├─────────────────────►│                  │
     │                      │                      │                  │
     │                      │                      │ 1. Validate      │
     │                      │                      │    OAuth         │
     │                      │                      │                  │
     │                      │                      │ 2. Get/Create    │
     │                      │                      │    User          │
     │                      │                      ├─────────────────►│
     │                      │                      │                  │
     │                      │                      │ 3. Add to Group  │
     │                      │                      ├─────────────────►│
     │                      │                      │                  │
     │                      │                      │ 4. Generate Token│
     │                      │                      │◄─────────────────┤
     │                      │                      │                  │
     │                      │ Redirect to OWI Chat │                  │
     │                      │ with Token           │                  │
     │◄─────────────────────┴──────────────────────┤                  │
     │                                             │                  │
     │                         Open Chat Interface │                  │
     ├──────────────────────────────────────────────────────────────►│
     │                                             │                  │
     │                     Interact with Assistant │                  │
     │◄────────────────────────────────────────────────────────────────┤
```

---

## LTI Launch Handler

**Endpoint:** `POST /lamb/simple_lti/launch`

**File:** `/backend/lamb/simple_lti/simple_lti_main.py`

```python
@router.post("/simple_lti/launch")
async def lti_launch(request: Request):
    """
    Handle LTI launch from LMS
    
    Process:
        1. Parse LTI parameters
        2. Validate OAuth signature
        3. Extract user info
        4. Get or create OWI user
        5. Add user to assistant's group
        6. Generate JWT token
        7. Record LTI user
        8. Redirect to OWI chat
    """
    # Parse LTI parameters
    form_data = await request.form()
    
    # Extract key parameters
    user_email = form_data.get("lis_person_contact_email_primary")
    user_name = form_data.get("lis_person_name_full") or form_data.get("lis_person_name_given", "Student")
    user_role = form_data.get("roles", "Learner")
    assistant_id = form_data.get("custom_assistant_id")
    
    if not user_email or not assistant_id:
        raise HTTPException(
            status_code=400,
            detail="Missing required LTI parameters"
        )
    
    # Validate OAuth signature
    oauth_consumer_key = form_data.get("oauth_consumer_key")
    
    if not validate_oauth_signature(form_data, oauth_consumer_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid OAuth signature"
        )
    
    # Get assistant
    db_manager = LambDatabaseManager()
    assistant = db_manager.get_assistant_by_id(int(assistant_id))
    
    if not assistant or not assistant.get('published'):
        raise HTTPException(
            status_code=404,
            detail="Assistant not found or not published"
        )
    
    # Get or create OWI user
    user_manager = OwiUserManager()
    owi_user = user_manager.get_user_by_email(user_email)
    
    if not owi_user:
        # Create new OWI user
        password = secrets.token_urlsafe(32)  # Random password
        owi_user = user_manager.create_user(
            email=user_email,
            name=user_name,
            password=password,
            role="user"
        )
    
    # Add user to assistant's group
    group_id = assistant['group_id']
    group_manager = OwiGroupManager()
    group_manager.add_user_to_group(group_id, owi_user['id'])
    
    # Generate JWT token
    token = user_manager.generate_token_for_user(owi_user['id'])
    
    # Record LTI user in LAMB database
    db_manager.create_lti_user(
        assistant_id=assistant_id,
        assistant_name=assistant['name'],
        group_id=group_id,
        group_name=assistant['group_name'],
        assistant_owner=assistant['owner'],
        user_email=user_email,
        user_name=user_name,
        user_display_name=user_name,
        user_role=user_role
    )
    
    # Redirect to OWI chat with token and model
    owi_public_url = os.getenv('OWI_PUBLIC_BASE_URL', 'http://localhost:8080')
    model_id = f"lamb_assistant.{assistant_id}"
    redirect_url = f"{owi_public_url}/?token={token}&model={model_id}"
    
    return RedirectResponse(url=redirect_url)
```

---

## OAuth 1.0 Signature Validation

```python
def validate_oauth_signature(form_data: dict, consumer_key: str) -> bool:
    """
    Validate OAuth 1.0 signature from LMS
    
    Args:
        form_data: LTI launch parameters
        consumer_key: OAuth consumer key
    
    Returns:
        True if signature is valid, False otherwise
    """
    # Get shared secret for consumer
    shared_secret = get_oauth_secret(consumer_key)
    
    if not shared_secret:
        logger.error(f"No shared secret found for consumer: {consumer_key}")
        return False
    
    # Extract OAuth parameters
    oauth_signature = form_data.get("oauth_signature")
    oauth_signature_method = form_data.get("oauth_signature_method")
    
    if oauth_signature_method != "HMAC-SHA1":
        logger.error(f"Unsupported signature method: {oauth_signature_method}")
        return False
    
    # Build base string
    # 1. Collect parameters (exclude oauth_signature)
    params = {k: v for k, v in form_data.items() if k != "oauth_signature"}
    
    # 2. Sort parameters
    sorted_params = sorted(params.items())
    
    # 3. URL encode and concatenate
    param_string = "&".join([
        f"{quote_plus(str(k))}={quote_plus(str(v))}"
        for k, v in sorted_params
    ])
    
    # 4. Get HTTP method and URL
    http_method = "POST"
    base_url = str(request.url).split('?')[0]  # Remove query params
    
    # 5. Build base string
    base_string = f"{http_method}&{quote_plus(base_url)}&{quote_plus(param_string)}"
    
    # 6. Generate signature
    key = f"{quote_plus(consumer_key)}&{quote_plus(shared_secret)}"
    signature = hmac.new(
        key.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha1
    ).digest()
    generated_signature = base64.b64encode(signature).decode('utf-8')
    
    # 7. Compare signatures
    return generated_signature == oauth_signature
```

---

## LTI Configuration XML

```python
def generate_lti_xml(
    title: str,
    description: str,
    launch_url: str,
    assistant_id: int
) -> str:
    """
    Generate LTI cartridge XML configuration
    
    Returns XML string for LMS import
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<cartridge_basiclti_link xmlns="http://www.imsglobal.org/xsd/imslticc_v1p0"
    xmlns:blti="http://www.imsglobal.org/xsd/imsbasiclti_v1p0"
    xmlns:lticm="http://www.imsglobal.org/xsd/imslticm_v1p0"
    xmlns:lticp="http://www.imsglobal.org/xsd/imslticp_v1p0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsglobal.org/xsd/imslticc_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticc_v1p0.xsd
    http://www.imsglobal.org/xsd/imsbasiclti_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imsbasiclti_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticm_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticm_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticp_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticp_v1p0.xsd">
    <blti:title>{title}</blti:title>
    <blti:description>{description}</blti:description>
    <blti:launch_url>{launch_url}</blti:launch_url>
    <blti:custom>
        <lticm:property name="assistant_id">{assistant_id}</lticm:property>
    </blti:custom>
    <blti:extensions platform="canvas.instructure.com">
        <lticm:property name="privacy_level">public</lticm:property>
    </blti:extensions>
</cartridge_basiclti_link>"""
    
    return xml
```

---

## OWI Bridge Components

### OwiGroupManager

**File:** `/backend/lamb/owi_bridge/owi_group.py`

```python
class OwiGroupManager:
    """
    Manage OWI groups for assistant access control
    """
    
    def __init__(self):
        self.db = OwiDatabaseManager()
    
    def create_group(self, name: str, description: str, user_id: str) -> str:
        """
        Create new OWI group
        
        Args:
            name: Group name
            description: Group description
            user_id: Creator's OWI user ID
        
        Returns:
            Group ID
        """
        group_id = str(uuid.uuid4())
        
        permissions = {
            "read": {
                "group_ids": [],
                "user_ids": []  # Will be populated as users join
            },
            "write": {
                "group_ids": [],
                "user_ids": [user_id]  # Creator can manage
            }
        }
        
        self.db.create_group(
            id=group_id,
            user_id=user_id,
            name=name,
            description=description,
            permissions=json.dumps(permissions)
        )
        
        return group_id
    
    def add_user_to_group(self, group_id: str, user_id: str):
        """
        Add user to group (grant read access to assistants)
        """
        group = self.db.get_group_by_id(group_id)
        
        if not group:
            raise ValueError(f"Group not found: {group_id}")
        
        permissions = json.loads(group['permissions'])
        
        # Add user to read permissions
        if user_id not in permissions['read']['user_ids']:
            permissions['read']['user_ids'].append(user_id)
        
        # Update group
        self.db.update_group_permissions(group_id, json.dumps(permissions))
```

### OwiModelManager

**File:** `/backend/lamb/owi_bridge/owi_model.py`

```python
class OwiModelManager:
    """
    Register LAMB assistants as OWI models
    """
    
    def __init__(self):
        self.db = OwiDatabaseManager()
    
    def create_model(
        self,
        model_id: str,
        name: str,
        base_model_id: str,
        user_id: str,
        description: str = None
    ):
        """
        Register assistant as OWI model
        
        Args:
            model_id: "lamb_assistant.{id}"
            name: Assistant name
            base_model_id: LAMB completion endpoint URL
            user_id: Creator's OWI user ID
            description: Assistant description
        """
        params = {
            "model": model_id,
            "base_url": base_model_id
        }
        
        meta = {
            "description": description,
            "profile_image_url": "/static/img/lamb_1.png"
        }
        
        self.db.create_model(
            id=model_id,
            user_id=user_id,
            base_model_id=base_model_id,
            name=name,
            params=json.dumps(params),
            meta=json.dumps(meta)
        )
```

---

## LTI User Tracking

### LTI Users Table

```python
{
    "id": 1,
    "assistant_id": "42",
    "assistant_name": "CS101 Assistant",
    "group_id": "group-uuid",
    "group_name": "CS101 Group",
    "assistant_owner": "prof@university.edu",
    "user_email": "student@university.edu",
    "user_name": "John Doe",
    "user_display_name": "John Doe",
    "user_role": "Learner",
    "created_at": 1678886400,
    "updated_at": 1678886400
}
```

**Purpose:**
- Track which students have accessed which assistants
- Analytics and reporting
- Audit trail

---

## LMS Configuration Guide

### Canvas

1. Go to Settings → Apps → View App Configurations
2. Click "+ App"
3. Configuration Type: "Manual Entry"
4. Name: `{assistant_name}`
5. Consumer Key: `{oauth_consumer_name}`
6. Shared Secret: `{shared_secret}`
7. Launch URL: `{launch_url}`
8. Custom Fields: `assistant_id={assistant_id}`

### Moodle

1. Site Administration → Plugins → External Tool → Manage Tools
2. Add External Tool Configuration
3. Tool Name: `{assistant_name}`
4. Consumer Key: `{oauth_consumer_name}`
5. Shared Secret: `{shared_secret}`
6. Tool URL: `{launch_url}`
7. Custom Parameters: `assistant_id={assistant_id}`

### Blackboard

1. System Admin → Integrations → LTI Tool Providers
2. Register Provider Domain
3. Provider Domain: `{your_domain}`
4. Consumer Key: `{oauth_consumer_name}`
5. Shared Secret: `{shared_secret}`

---

## Unpublishing

**Endpoint:** `POST /creator/assistant/{id}/unpublish`

```python
@router.post("/assistant/{assistant_id}/unpublish")
async def unpublish_assistant(assistant_id: int, request: Request):
    """
    Unpublish assistant (disable LTI access)
    
    Process:
        1. Validate user owns assistant
        2. Mark as unpublished in database
        3. Optionally delete OWI group and model
    """
    creator_user = get_creator_user_from_token(request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db_manager = LambDatabaseManager()
    assistant = db_manager.get_assistant_by_id(assistant_id)
    
    if not assistant or assistant['owner'] != creator_user['email']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update assistant
    db_manager.update_assistant(
        assistant_id,
        {
            "published": False,
            "published_at": None
        }
    )
    
    return {"success": True}
```

---

## Security Considerations

### OAuth Secrets

- Store securely (encrypted at rest)
- Never log secrets
- Use strong random generation
- Rotate periodically

### User Privacy

- Only collect necessary LTI data
- Follow institutional privacy policies
- Provide clear data usage info

### Access Control

- OWI groups enforce model access
- Only group members can use assistant
- LTI users automatically added to group

---

## Related Documentation

- **Backend Architecture:** `backend_architecture.md`
- **Backend Authentication:** `backend_authentication.md`
- **Frontend Assistants:** `frontend_assistants_management.md`
- **Database Schema:** `database_schema.md`

