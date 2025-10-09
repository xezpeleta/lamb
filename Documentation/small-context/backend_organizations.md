# Backend: Organizations & Multi-Tenancy

**Purpose:** Organization structure, configuration, and multi-tenant isolation  
**Related Docs:** `backend_architecture.md`, `backend_authentication.md`, `database_schema.md`

---

## Overview

Organizations provide multi-tenant isolation in LAMB:
- **Independent configurations** - Each org has own LLM keys, KB server settings
- **User isolation** - Users belong to organizations
- **Resource isolation** - Assistants and Knowledge Bases scoped to org
- **Role-based access** - owner, admin, member roles within organizations

---

## Organization Structure

### Organization Record

```python
{
    "id": 1,
    "slug": "engineering",          # URL-safe identifier
    "name": "Engineering Department",
    "is_system": False,              # True only for "lamb" system org
    "status": "active",              # active | suspended | trial
    "config": {                      # JSON configuration (see below)
        "version": "1.0",
        "setups": {...},
        "kb_server": {...},
        "features": {...}
    },
    "created_at": 1678886400,
    "updated_at": 1678886400
}
```

### System Organization

The "lamb" organization is special:
- Created automatically during database initialization
- `is_system = true`
- Cannot be deleted
- System admins are members with admin role
- Fallback configuration source

---

## Organization Configuration

### Configuration Structure

```json
{
  "version": "1.0",
  "setups": {
    "default": {
      "name": "Default Setup",
      "providers": {
        "openai": {
          "enabled": true,
          "api_key": "sk-...",
          "base_url": "https://api.openai.com/v1",
          "default_model": "gpt-4o-mini",
          "models": ["gpt-4o", "gpt-4o-mini", "gpt-4"]
        },
        "ollama": {
          "enabled": true,
          "base_url": "http://localhost:11434",
          "default_model": "llama3.1:latest",
          "models": ["llama3.1:latest", "mistral:latest", "llama2:latest"]
        },
        "anthropic": {
          "enabled": false,
          "api_key": "",
          "default_model": "claude-3-5-sonnet-20241022",
          "models": []
        }
      }
    }
  },
  "kb_server": {
    "url": "http://localhost:9090",
    "api_key": "kb-api-key"
  },
  "assistant_defaults": {
    "prompt_template": "User: {user_message}\nAssistant:",
    "system_prompt": "You are a helpful educational assistant."
  },
  "features": {
    "signup_enabled": false,
    "signup_key": "org-specific-key-2024"
  },
  "metadata": {
    "description": "Engineering Department Organization",
    "contact_email": "admin@engineering.edu"
  }
}
```

### Configuration Sections

#### Setups

Multiple provider setups can be defined (future feature):

```json
"setups": {
  "default": {
    "name": "Default Setup",
    "providers": {...}
  },
  "research": {
    "name": "Research Setup",
    "providers": {...}
  }
}
```

**Current:** Only "default" setup is used.

#### Providers

Each provider has:
- `enabled` - Whether provider is available
- `api_key` - API key (if required)
- `base_url` - API endpoint
- `default_model` - Default model for assistants
- `models` - List of available models

**Supported Providers:**
- `openai` - OpenAI API
- `ollama` - Local Ollama
- `anthropic` - Claude (future)
- Add more by creating connector plugins

#### KB Server

```json
"kb_server": {
  "url": "http://localhost:9090",
  "api_key": "kb-api-key"
}
```

**Used by:**
- RAG processors to query Knowledge Bases
- KB management endpoints to create/manage collections

#### Features

```json
"features": {
  "signup_enabled": false,
  "signup_key": "unique-org-key"
}
```

**Signup:**
- Users with matching `signup_key` auto-join organization
- No admin approval needed
- Can be disabled anytime

---

## Organization Roles

### Role Types

| Role | Permissions |
|------|-------------|
| **owner** | Full control over organization, can delete org |
| **admin** | Can manage org settings, create users, view all assistants |
| **member** | Can create own assistants, access creator interface |

### Role Assignment

**Database Table:** `organization_roles`

```python
{
    "id": 1,
    "organization_id": 2,
    "user_id": 5,
    "role": "admin",
    "created_at": 1678886400,
    "updated_at": 1678886400
}
```

**Constraint:** One role per user per organization (UNIQUE(organization_id, user_id))

---

## Organization Management APIs

### List Organizations (System Admin)

**Endpoint:** `GET /creator/admin/organizations`

```python
@router.get("/admin/organizations")
async def list_organizations(request: Request):
    """
    List all organizations (system admin only)
    """
    if not is_admin_user(request.headers.get("Authorization")):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_manager = LambDatabaseManager()
    organizations = db_manager.list_organizations()
    
    return {"organizations": organizations}
```

**Response:**
```json
{
  "organizations": [
    {
      "id": 1,
      "slug": "lamb",
      "name": "LAMB System",
      "is_system": true,
      "status": "active",
      "member_count": 3
    },
    {
      "id": 2,
      "slug": "engineering",
      "name": "Engineering Department",
      "is_system": false,
      "status": "active",
      "member_count": 15
    }
  ]
}
```

---

### Create Organization (System Admin)

**Endpoint:** `POST /creator/admin/organizations/enhanced`

```python
@router.post("/admin/organizations/enhanced")
async def create_organization(org_data: CreateOrgRequest, request: Request):
    """
    Create new organization with admin user
    
    Args:
        org_data: {
            slug: "engineering",
            name: "Engineering Department",
            admin_user_id: 5,
            signup_enabled: true,
            signup_key: "eng-dept-2024",
            use_system_baseline: true
        }
    """
    if not is_admin_user(request.headers.get("Authorization")):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_manager = LambDatabaseManager()
    
    # Create base config
    if org_data.use_system_baseline:
        # Copy system org config as baseline
        system_org = db_manager.get_organization_by_slug("lamb")
        base_config = system_org['config']
    else:
        # Empty config
        base_config = {
            "version": "1.0",
            "setups": {
                "default": {
                    "providers": {}
                }
            },
            "kb_server": {},
            "features": {}
        }
    
    # Set org-specific features
    if org_data.signup_enabled:
        base_config['features'] = {
            "signup_enabled": True,
            "signup_key": org_data.signup_key
        }
    
    # Create organization
    org_id = db_manager.create_organization(
        slug=org_data.slug,
        name=org_data.name,
        config=base_config
    )
    
    # Assign admin user as owner
    if org_data.admin_user_id:
        db_manager.assign_organization_role(
            org_id,
            org_data.admin_user_id,
            "owner"
        )
    
    return {
        "success": True,
        "organization_id": org_id
    }
```

---

### Update Organization Config

**Endpoint:** `PUT /creator/admin/organizations/{slug}/config`

```python
@router.put("/admin/organizations/{slug}/config")
async def update_org_config(slug: str, config: dict, request: Request):
    """
    Update organization configuration
    
    Access: System admin OR org owner/admin
    """
    creator_user = get_creator_user_from_token(request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db_manager = LambDatabaseManager()
    org = db_manager.get_organization_by_slug(slug)
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check permission
    system_admin = is_admin_user(creator_user)
    org_role = db_manager.get_user_organization_role(org['id'], creator_user['id'])
    
    if not system_admin and org_role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Update config
    success = db_manager.update_organization_config(org['id'], config)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update config")
    
    return {"success": True}
```

**Example Request:**
```json
{
  "setups": {
    "default": {
      "providers": {
        "openai": {
          "enabled": true,
          "api_key": "sk-new-key",
          "base_url": "https://api.openai.com/v1",
          "default_model": "gpt-4o",
          "models": ["gpt-4o", "gpt-4o-mini"]
        }
      }
    }
  }
}
```

---

### Get Current User's Organization

**Endpoint:** `GET /creator/admin/organizations/current`

```python
@router.get("/admin/organizations/current")
async def get_current_org(request: Request):
    """
    Get organization for current user
    """
    creator_user = get_creator_user_from_token(request.headers.get("Authorization"))
    if not creator_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db_manager = LambDatabaseManager()
    org = db_manager.get_user_organization(creator_user['id'])
    
    if not org:
        raise HTTPException(status_code=404, detail="No organization found")
    
    # Include user's role
    org_role = db_manager.get_user_organization_role(org['id'], creator_user['id'])
    org['user_role'] = org_role
    
    return org
```

---

## Organization Config Resolution

### OrganizationConfigResolver Class

**File:** `/backend/lamb/completions/org_config_resolver.py`

```python
class OrganizationConfigResolver:
    """
    Resolve configuration based on user's organization
    
    Priority:
        1. Organization config
        2. Environment variables
        3. System defaults
    """
    
    def __init__(self, user_email: str):
        """
        Initialize with user email to determine organization
        """
        self.db_manager = LambDatabaseManager()
        self.user = self.db_manager.get_creator_user_by_email(user_email)
        
        if not self.user:
            raise ValueError(f"User not found: {user_email}")
        
        self.organization = self.db_manager.get_user_organization(self.user['id'])
        
        if not self.organization:
            # Fallback to system organization
            self.organization = self.db_manager.get_organization_by_slug("lamb")
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific provider
        
        Args:
            provider_name: 'openai', 'ollama', etc.
        
        Returns:
            Provider config dict or None
        """
        config = self.organization.get('config', {})
        setups = config.get('setups', {})
        default_setup = setups.get('default', {})
        providers = default_setup.get('providers', {})
        
        provider_config = providers.get(provider_name)
        
        if not provider_config or not provider_config.get('enabled'):
            return None
        
        return provider_config
    
    def get_kb_server_config(self) -> Dict:
        """
        Get Knowledge Base server configuration
        """
        config = self.organization.get('config', {})
        kb_config = config.get('kb_server', {})
        
        # Fallback to environment variables
        if not kb_config.get('url'):
            kb_config = {
                'url': os.getenv('KB_SERVER_URL', 'http://localhost:9090'),
                'api_key': os.getenv('KB_API_KEY', '')
            }
        
        return kb_config
    
    def get_assistant_defaults(self) -> Dict:
        """
        Get default assistant configuration
        """
        config = self.organization.get('config', {})
        defaults = config.get('assistant_defaults', {})
        
        return {
            'prompt_template': defaults.get('prompt_template', 'User: {user_message}\nAssistant:'),
            'system_prompt': defaults.get('system_prompt', 'You are a helpful assistant.')
        }
```

**Usage in Completions:**

```python
# In connector plugin
config_resolver = OrganizationConfigResolver(assistant_owner)
openai_config = config_resolver.get_provider_config("openai")

if openai_config:
    api_key = openai_config['api_key']
    base_url = openai_config['base_url']
    model = openai_config['default_model']
```

---

## Organization Signup

### Signup with Organization Key

When user signs up with organization-specific key:

1. Frontend sends signup request with `secret_key`
2. Backend searches for organization with matching `signup_key`
3. If found:
   - Create OWI user
   - Create LAMB creator user in that organization
   - Assign "member" role
4. If not found:
   - Check system signup (if enabled)
   - Otherwise reject

**Implementation:**

```python
@app.post("/creator/signup")
async def signup(signup_data: SignupRequest):
    """
    User signup
    
    Args:
        signup_data: { email, name, password, secret_key }
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
            # Assign member role
            db_manager.assign_organization_role(
                target_org['id'],
                result['user_id'],
                "member"
            )
        
        return result
    
    # Fallback to system org (if enabled)
    elif os.getenv('SIGNUP_ENABLED') == 'true':
        # ... system signup logic
        pass
    else:
        raise HTTPException(status_code=400, detail="Invalid signup key")
```

---

## Database Operations

### LambDatabaseManager Methods

```python
class LambDatabaseManager:
    # Create organization
    def create_organization(self, slug: str, name: str, config: dict) -> int:
        """
        Create new organization
        
        Returns organization ID
        """
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO {self.table_prefix}organizations 
            (slug, name, config, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (slug, name, json.dumps(config), int(time.time()), int(time.time())))
        self.conn.commit()
        return cursor.lastrowid
    
    # Get organization by slug
    def get_organization_by_slug(self, slug: str) -> Optional[Dict]:
        """
        Get organization by slug
        """
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT * FROM {self.table_prefix}organizations
            WHERE slug = ?
        """, (slug,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    # Update organization config
    def update_organization_config(self, org_id: int, config: dict) -> bool:
        """
        Update organization configuration
        """
        cursor = self.conn.cursor()
        cursor.execute(f"""
            UPDATE {self.table_prefix}organizations
            SET config = ?, updated_at = ?
            WHERE id = ?
        """, (json.dumps(config), int(time.time()), org_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # Assign organization role
    def assign_organization_role(self, org_id: int, user_id: int, role: str) -> bool:
        """
        Assign role to user in organization
        
        Role: 'owner', 'admin', or 'member'
        """
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT OR REPLACE INTO {self.table_prefix}organization_roles
            (organization_id, user_id, role, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (org_id, user_id, role, int(time.time()), int(time.time())))
        self.conn.commit()
        return True
    
    # Get user's organization role
    def get_user_organization_role(self, org_id: int, user_id: int) -> Optional[str]:
        """
        Get user's role in organization
        
        Returns: 'owner', 'admin', 'member', or None
        """
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT role FROM {self.table_prefix}organization_roles
            WHERE organization_id = ? AND user_id = ?
        """, (org_id, user_id))
        row = cursor.fetchone()
        
        if row:
            return row['role']
        return None
    
    # Get user's organization
    def get_user_organization(self, user_id: int) -> Optional[Dict]:
        """
        Get organization user belongs to
        """
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT o.* FROM {self.table_prefix}organizations o
            INNER JOIN {self.table_prefix}Creator_users u ON u.organization_id = o.id
            WHERE u.id = ?
        """, (user_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
```

---

## Best Practices

### Configuration Management

1. **Use system baseline** for new organizations
2. **Store API keys securely** in org config, not code
3. **Test configuration** before deploying to users
4. **Document changes** in metadata section

### Organization Structure

1. **One organization per department/institution**
2. **Clear naming** - use descriptive names and slugs
3. **Assign owners** - ensure each org has at least one owner
4. **Regular audits** - review members and permissions

### Signup Keys

1. **Unique keys** per organization
2. **Rotate keys** periodically
3. **Disable signup** when not actively recruiting
4. **Monitor signups** - track new users

---

## Related Documentation

- **Backend Architecture:** `backend_architecture.md`
- **Authentication:** `backend_authentication.md`
- **Completions Pipeline:** `backend_completions_pipeline.md`
- **Database Schema:** `database_schema.md`
- **Frontend Org Management:** `frontend_org_management.md`

