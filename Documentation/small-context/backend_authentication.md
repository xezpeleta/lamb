# Backend: Authentication & Authorization

**Purpose:** User authentication flows, token management, and permission checks  
**Related Docs:** `backend_architecture.md`, `backend_organizations.md`, `frontend_architecture.md`

---

## Overview

LAMB uses a **hybrid authentication system**:
- **Open WebUI** manages credentials and JWT tokens
- **LAMB** validates tokens and enforces permissions
- **Two user types:** creators (full interface) and end_users (OWI only)

---

## Authentication Flow

```
┌─────────┐                    ┌──────────────┐                ┌────────────┐
│ Browser │                    │   Creator    │                │    OWI     │
│         │                    │  Interface   │                │            │
└────┬────┘                    └──────┬───────┘                └─────┬──────┘
     │                                │                               │
     │  POST /creator/login           │                               │
     │  email, password               │                               │
     ├───────────────────────────────►│                               │
     │                                │                               │
     │                                │  Verify credentials           │
     │                                │  (via OWI bridge)             │
     │                                ├──────────────────────────────►│
     │                                │                               │
     │                                │  Password matches?            │
     │                                │◄──────────────────────────────┤
     │                                │                               │
     │                                │  Generate JWT token           │
     │                                ├──────────────────────────────►│
     │                                │                               │
     │                                │  JWT token + user_type        │
     │                                │◄──────────────────────────────┤
     │                                │                               │
     │  200 OK                        │                               │
     │  {token, user_info, user_type, │                               │
     │   launch_url}                  │                               │
     │◄───────────────────────────────┤                               │
     │                                │                               │
     │  Frontend checks user_type:    │                               │
     │  - If 'creator': Continue to   │                               │
     │    creator interface           │                               │
     │  - If 'end_user': Redirect to  │                               │
     │    launch_url (OWI)            │                               │
     │                                │                               │
     │  [For creator users only]      │                               │
     │  Store token in localStorage   │                               │
     │                                │                               │
     │  Subsequent requests           │                               │
     │  Authorization: Bearer {token} │                               │
     ├───────────────────────────────►│                               │
     │                                │                               │
     │                                │  Verify token                 │
     │                                │  (via OWI bridge)             │
     │                                ├──────────────────────────────►│
     │                                │                               │
     │                                │  User info                    │
     │                                │◄──────────────────────────────┤
     │                                │                               │
     │                                │  Check LAMB Creator user      │
     │                                │  exists & user_type           │
     │                                │                               │
     │  200 OK {data}                 │                               │
     │◄───────────────────────────────┤                               │
```

---

## Login Implementation

### Login Endpoint

**File:** `/backend/creator_interface/main.py`

```python
@app.post("/creator/login")
async def login(credentials: LoginRequest):
    """
    Authenticate user and return token
    
    Args:
        credentials: { email, password }
    
    Returns:
        {
            "token": "jwt-token",
            "email": "user@example.com",
            "name": "User Name",
            "role": "user" | "admin",
            "user_type": "creator" | "end_user",
            "launch_url": "http://owi.url/?token=..." (if end_user)
        }
    """
    email = credentials.email
    password = credentials.password
    
    # 1. Verify credentials with OWI
    user_manager = OwiUserManager()
    owi_user = user_manager.verify_password(email, password)
    
    if not owi_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 2. Check if LAMB creator user exists
    db_manager = LambDatabaseManager()
    creator_user = db_manager.get_creator_user_by_email(email)
    
    if not creator_user:
        raise HTTPException(status_code=401, detail="User not found in LAMB")
    
    # 3. Generate JWT token
    token = user_manager.generate_token(email, password)
    
    # 4. Check user type
    user_type = creator_user.get('user_type', 'creator')
    
    response = {
        "token": token,
        "email": email,
        "name": creator_user['name'],
        "role": owi_user.get('role', 'user'),
        "user_type": user_type
    }
    
    # 5. Add launch_url for end_users
    if user_type == 'end_user':
        owi_public_url = os.getenv('OWI_PUBLIC_BASE_URL', 'http://localhost:8080')
        response["launch_url"] = f"{owi_public_url}/?token={token}"
    
    return response
```

---

## User Types

### Creator Users

**Access:** Full LAMB creator interface
- Create and manage assistants
- Manage Knowledge Bases
- Test assistants
- Publish assistants
- Access admin panels (if admin role)

**Login Flow:**
1. Enter credentials
2. Receive token
3. Store token in localStorage
4. Navigate to `/assistants`

### End Users

**Access:** Open WebUI only (bypasses LAMB interface)
- Interact with published assistants
- No access to creator interface
- Automatically redirected on login

**Login Flow:**
1. Enter credentials
2. Receive token and `launch_url`
3. Frontend detects `user_type === 'end_user'`
4. Browser redirects to `launch_url`
5. User sees Open WebUI chat interface

**Important:** `launch_url` uses `OWI_PUBLIC_BASE_URL` (browser-accessible) not `OWI_BASE_URL` (Docker internal)

---

## Token Validation

### Token Verification Helper

**File:** `/backend/creator_interface/assistant_router.py`

```python
def get_creator_user_from_token(auth_header: str):
    """
    Extract user info from JWT token and verify in LAMB database
    
    Args:
        auth_header: "Bearer {token}" string
    
    Returns:
        Creator user dict or None
    
    Process:
        1. Extract token from header
        2. Validate token with OWI
        3. Get OWI user info
        4. Check LAMB creator user exists
        5. Return creator user
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split("Bearer ")[1].strip()
    
    # Verify token with OWI
    user_manager = OwiUserManager()
    owi_user = user_manager.get_user_auth(token)
    
    if not owi_user:
        return None
    
    # Check if user exists in LAMB Creator database
    db_manager = LambDatabaseManager()
    creator_user = db_manager.get_creator_user_by_email(owi_user['email'])
    
    return creator_user
```

**Usage in Endpoints:**

```python
@router.get("/assistant/list")
async def list_assistants(request: Request):
    # Validate token
    creator_user = get_creator_user_from_token(request.headers.get("Authorization"))
    
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # User is authenticated - proceed
    db = LambDatabaseManager()
    assistants = db.list_assistants(creator_user['email'])
    return {"assistants": assistants}
```

---

## Authorization Levels

### Admin Check

**File:** `/backend/creator_interface/assistant_router.py`

```python
def is_admin_user(creator_user_or_token):
    """
    Check if user is an admin (system or organization)
    
    Args:
        creator_user_or_token: User dict or token string
    
    Returns:
        True if user is admin, False otherwise
    
    Checks:
        1. OWI role === 'admin' (system admin)
        2. Organization role === 'admin' or 'owner'
    """
    # If token string is passed, get creator user first
    if isinstance(creator_user_or_token, str):
        creator_user = get_creator_user_from_token(creator_user_or_token)
    else:
        creator_user = creator_user_or_token
    
    if not creator_user:
        return False
    
    # Check OWI role
    user_manager = OwiUserManager()
    owi_user = user_manager.get_user_by_email(creator_user['email'])
    
    if owi_user and owi_user.get('role') == 'admin':
        return True
    
    # Check organization role
    db_manager = LambDatabaseManager()
    system_org = db_manager.get_organization_by_slug("lamb")
    if system_org:
        org_role = db_manager.get_user_organization_role(
            system_org['id'], 
            creator_user['id']
        )
        if org_role in ['admin', 'owner']:
            return True
    
    return False
```

**Usage:**

```python
@router.get("/admin/users")
async def list_all_users(request: Request):
    # Check admin permission
    if not is_admin_user(request.headers.get("Authorization")):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Admin action
    db = LambDatabaseManager()
    users = db.list_all_users()
    return {"users": users}
```

---

## Permission Matrix

### Role Hierarchy

| Role | Level | Description |
|------|-------|-------------|
| **System Admin** | Highest | OWI role === 'admin' |
| **Org Owner** | High | Organization role === 'owner' |
| **Org Admin** | Medium | Organization role === 'admin' |
| **Org Member** | Low | Organization role === 'member' |
| **End User** | Lowest | user_type === 'end_user' |

### Action Permissions

| Action | System Admin | Org Owner | Org Admin | Org Member | End User |
|--------|--------------|-----------|-----------|------------|----------|
| View all organizations | ✓ | ✗ | ✗ | ✗ | ✗ |
| Create organization | ✓ | ✗ | ✗ | ✗ | ✗ |
| Update org config | ✓ | ✓ | ✓ | ✗ | ✗ |
| Create org users | ✓ | ✓ | ✓ | ✗ | ✗ |
| Create assistants | ✓ | ✓ | ✓ | ✓ | ✗ |
| Edit own assistants | ✓ | ✓ | ✓ | ✓ | ✗ |
| Edit others' assistants | ✓ | ✓ | ✓ | ✗ | ✗ |
| Access creator UI | ✓ | ✓ | ✓ | ✓ | ✗ |
| Use published assistants | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## OWI Bridge Integration

### OwiUserManager

**File:** `/backend/lamb/owi_bridge/owi_users.py`

```python
class OwiUserManager:
    def __init__(self):
        self.db = OwiDatabaseManager()
    
    def verify_password(self, email: str, password: str) -> Optional[Dict]:
        """
        Verify user credentials against OWI auth table
        
        Returns:
            User dict if valid, None if invalid
        """
        auth_record = self.db.get_auth_by_email(email)
        if not auth_record:
            return None
        
        # Verify bcrypt password
        if bcrypt.checkpw(password.encode('utf-8'), auth_record['password'].encode('utf-8')):
            user = self.db.get_user_by_email(email)
            return user
        
        return None
    
    def generate_token(self, email: str, password: str) -> str:
        """
        Generate JWT token for authenticated user
        
        Uses OWI's secret key and token format
        """
        # This would typically call OWI's token generation
        # For now, simplified version:
        user = self.db.get_user_by_email(email)
        
        payload = {
            "id": user['id'],
            "email": email,
            "exp": int(time.time()) + (7 * 24 * 60 * 60)  # 7 days
        }
        
        secret_key = os.getenv("SECRET_KEY")
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        return token
    
    def get_user_auth(self, token: str) -> Optional[Dict]:
        """
        Validate JWT token and return user info
        
        Returns:
            User dict if valid, None if invalid
        """
        try:
            secret_key = os.getenv("SECRET_KEY")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            
            user = self.db.get_user_by_id(payload['id'])
            return user
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def create_user(self, email: str, name: str, password: str, role: str = "user") -> Dict:
        """
        Create new OWI user
        
        Args:
            email: User email
            name: Display name
            password: Plain text password (will be hashed)
            role: 'user' or 'admin'
        
        Returns:
            Created user dict
        """
        # Hash password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        
        # Generate user ID
        user_id = str(uuid.uuid4())
        
        # Insert into user table
        self.db.create_user(
            id=user_id,
            email=email,
            name=name,
            role=role
        )
        
        # Insert into auth table
        self.db.create_auth(
            id=user_id,
            email=email,
            password=hashed.decode('utf-8')
        )
        
        return self.db.get_user_by_id(user_id)
```

---

## User Creation Flow

### System Admin Creating User

**Endpoint:** `POST /creator/admin/users/create`

```python
@router.post("/admin/users/create")
async def create_user(user_data: CreateUserRequest, request: Request):
    """
    Create new user (system admin only)
    
    Args:
        user_data: {
            email, name, password, role, user_type, organization_id
        }
    
    Process:
        1. Verify admin permission
        2. Create OWI user
        3. Create LAMB creator user
        4. Assign organization role
    """
    # Check admin
    if not is_admin_user(request.headers.get("Authorization")):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Create OWI user
    owi_manager = OwiUserManager()
    owi_user = owi_manager.create_user(
        email=user_data.email,
        name=user_data.name,
        password=user_data.password,
        role=user_data.role or "user"
    )
    
    # Create LAMB creator user
    db_manager = LambDatabaseManager()
    creator_user_id = db_manager.create_creator_user(
        email=user_data.email,
        name=user_data.name,
        organization_id=user_data.organization_id,
        user_type=user_data.user_type or "creator"
    )
    
    # Assign organization role
    if user_data.organization_id:
        db_manager.assign_organization_role(
            user_data.organization_id,
            creator_user_id,
            "member"
        )
    
    return {
        "success": True,
        "user_id": creator_user_id,
        "owi_user_id": owi_user['id']
    }
```

### Organization Admin Creating User

**Endpoint:** `POST /creator/admin/org-admin/users/create`

```python
@router.post("/admin/org-admin/users/create")
async def create_org_user(user_data: CreateOrgUserRequest, request: Request):
    """
    Create user within organization (org admin only)
    
    Process:
        1. Verify org admin permission
        2. Get user's organization
        3. Create user in that organization
    """
    # Get current user
    creator_user = get_creator_user_from_token(request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Check org admin permission
    db_manager = LambDatabaseManager()
    org = db_manager.get_user_organization(creator_user['id'])
    org_role = db_manager.get_user_organization_role(org['id'], creator_user['id'])
    
    if org_role not in ['admin', 'owner']:
        raise HTTPException(status_code=403, detail="Org admin access required")
    
    # Create user
    user_creator = UserCreatorManager()
    result = await user_creator.create_user(
        email=user_data.email,
        name=user_data.name,
        password=user_data.password,
        organization_id=org['id'],
        user_type=user_data.user_type or "creator"
    )
    
    return result
```

---

## Signup Flow

### Public Signup

**Endpoint:** `POST /creator/signup`

```python
@app.post("/creator/signup")
async def signup(signup_data: SignupRequest):
    """
    User self-signup (if enabled)
    
    Args:
        signup_data: { email, name, password, secret_key }
    
    Process:
        1. Check if signup key matches any organization
        2. If match: create user in that organization
        3. If no match and system signup enabled: create in system org
        4. Otherwise: reject
    """
    # Try organization-specific signup
    db_manager = LambDatabaseManager()
    target_org = db_manager.get_organization_by_signup_key(signup_data.secret_key)
    
    if target_org:
        # Create user in organization
        user_creator = UserCreatorManager()
        result = await user_creator.create_user(
            email=signup_data.email,
            name=signup_data.name,
            password=signup_data.password,
            organization_id=target_org['id'],
            user_type="creator"
        )
        
        if result["success"]:
            db_manager.assign_organization_role(
                target_org['id'],
                result['user_id'],
                "member"
            )
        
        return result
    
    # Fallback to system organization if enabled
    elif os.getenv('SIGNUP_ENABLED') == 'true' and signup_data.secret_key == os.getenv('SIGNUP_SECRET_KEY'):
        system_org = db_manager.get_organization_by_slug("lamb")
        
        user_creator = UserCreatorManager()
        result = await user_creator.create_user(
            email=signup_data.email,
            name=signup_data.name,
            password=signup_data.password,
            organization_id=system_org['id'],
            user_type="creator"
        )
        
        return result
    
    else:
        raise HTTPException(status_code=400, detail="Invalid signup key")
```

---

## API Key Authentication (Completions)

**Endpoint:** `POST /v1/chat/completions`

```python
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    Generate chat completion (OpenAI-compatible)
    
    Uses API key authentication instead of user tokens
    """
    # Get API key from header
    api_key = request.headers.get("Authorization")
    if api_key and api_key.startswith("Bearer "):
        api_key = api_key.split("Bearer ")[1].strip()
    
    # Validate API key
    expected_key = os.getenv("LAMB_BEARER_TOKEN", "0p3n-w3bu!")
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Process completion
    body = await request.json()
    result = await run_lamb_assistant(body, headers=request.headers)
    return result
```

**Configuration:**
```bash
LAMB_BEARER_TOKEN=your-secure-api-key
```

**Security:** Change default value in production!

---

## Security Best Practices

### Password Handling

- ✓ Passwords hashed with bcrypt (cost factor 12)
- ✓ Never store plain text passwords
- ✓ Never log passwords
- ✓ Use HTTPS in production

### Token Security

- ✓ JWT tokens signed with secret key
- ✓ 7-day expiration
- ✓ Tokens stored in localStorage (frontend)
- ✓ Validate on every request
- ✗ No token refresh mechanism (user must re-login)

### API Key Security

- ✓ Change default `LAMB_BEARER_TOKEN`
- ✓ Use environment variables
- ✓ Rotate keys periodically
- ✗ Same key for all assistants (future: per-assistant keys)

---

## Related Documentation

- **Backend Architecture:** `backend_architecture.md`
- **Organizations:** `backend_organizations.md`
- **Frontend Architecture:** `frontend_architecture.md`
- **Database Schema:** `database_schema.md`

