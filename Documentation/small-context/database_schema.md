# Database Schema

**Purpose:** Complete database schema reference for LAMB and OWI databases  
**Related Docs:** `backend_architecture.md`, `backend_organizations.md`, `backend_authentication.md`

---

## LAMB Database

**Location:** `$LAMB_DB_PATH/lamb_v4.db`  
**Engine:** SQLite 3  
**Encoding:** UTF-8

---

### Organizations Table

```sql
CREATE TABLE organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    is_system BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'suspended', 'trial')),
    config JSON NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
```

**Fields:**
- `id` - Primary key
- `slug` - URL-safe identifier (unique)
- `name` - Display name
- `is_system` - True only for "lamb" system organization
- `status` - Organization status: active | suspended | trial
- `config` - JSON configuration (see config structure below)
- `created_at` - Unix timestamp
- `updated_at` - Unix timestamp

**Config Structure:**
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
          "models": ["gpt-4o", "gpt-4o-mini"]
        },
        "ollama": {
          "enabled": true,
          "base_url": "http://localhost:11434",
          "default_model": "llama3.1:latest",
          "models": ["llama3.1:latest"]
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
    "system_prompt": "You are a helpful assistant."
  },
  "features": {
    "signup_enabled": false,
    "signup_key": "org-key"
  }
}
```

---

### Organization Roles Table

```sql
CREATE TABLE organization_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('owner', 'admin', 'member')),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Creator_users(id) ON DELETE CASCADE,
    UNIQUE(organization_id, user_id)
);
```

**Fields:**
- `id` - Primary key
- `organization_id` - Foreign key to organizations
- `user_id` - Foreign key to Creator_users
- `role` - User role: owner | admin | member
- `created_at` - Unix timestamp
- `updated_at` - Unix timestamp

**Constraints:**
- One role per user per organization (UNIQUE)
- Cascade delete when org or user deleted

---

### Creator Users Table

```sql
CREATE TABLE Creator_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    user_email TEXT NOT NULL UNIQUE,
    user_name TEXT NOT NULL,
    user_type TEXT NOT NULL DEFAULT 'creator' CHECK(user_type IN ('creator', 'end_user')),
    user_config JSON,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);
```

**Fields:**
- `id` - Primary key
- `organization_id` - Foreign key to organizations (nullable)
- `user_email` - Email address (unique)
- `user_name` - Display name
- `user_type` - creator | end_user
- `user_config` - JSON configuration (optional)
- `created_at` - Unix timestamp
- `updated_at` - Unix timestamp

**User Types:**
- **creator**: Access to creator interface
- **end_user**: Redirected to Open WebUI on login

**User Config Structure:**
```json
{
  "preferences": {
    "language": "en",
    "theme": "light"
  }
}
```

---

### Assistants Table

```sql
CREATE TABLE assistants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    owner TEXT NOT NULL,
    api_callback TEXT,
    system_prompt TEXT,
    prompt_template TEXT,
    RAG_endpoint TEXT,
    RAG_Top_k INTEGER,
    RAG_collections TEXT,
    pre_retrieval_endpoint TEXT,
    post_retrieval_endpoint TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    published_at INTEGER,
    group_id TEXT,
    group_name TEXT,
    oauth_consumer_name TEXT,
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    UNIQUE(organization_id, name, owner)
);
```

**Fields:**
- `id` - Primary key
- `organization_id` - Foreign key to organizations
- `name` - Assistant name (unique per org/owner)
- `description` - Description
- `owner` - Owner email
- `api_callback` - **IMPORTANT: Stores metadata JSON** (see below)
- `system_prompt` - System instructions
- `prompt_template` - Message formatting template
- `RAG_endpoint` - **DEPRECATED** (empty)
- `RAG_Top_k` - Number of RAG results to retrieve
- `RAG_collections` - Comma-separated collection IDs
- `pre_retrieval_endpoint` - **DEPRECATED** (empty)
- `post_retrieval_endpoint` - **DEPRECATED** (empty)
- `created_at` - Unix timestamp
- `updated_at` - Unix timestamp
- `published` - Is assistant published for LTI
- `published_at` - Unix timestamp of publishing
- `group_id` - OWI group ID (for published assistants)
- `group_name` - OWI group name
- `oauth_consumer_name` - LTI consumer key

**CRITICAL: api_callback Field**

The `api_callback` column stores the assistant's metadata JSON:

```json
{
  "connector": "openai",
  "llm": "gpt-4o-mini",
  "prompt_processor": "simple_augment",
  "rag_processor": "simple_rag"
}
```

**Why?**
- Avoids schema changes
- Application code uses `assistant.metadata`
- Database stores in `api_callback` column
- Provides semantic clarity

---

### LTI Users Table

```sql
CREATE TABLE lti_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assistant_id TEXT NOT NULL,
    assistant_name TEXT NOT NULL,
    group_id TEXT NOT NULL DEFAULT '',
    group_name TEXT NOT NULL DEFAULT '',
    assistant_owner TEXT NOT NULL DEFAULT '',
    user_email TEXT NOT NULL,
    user_name TEXT NOT NULL DEFAULT '',
    user_display_name TEXT NOT NULL,
    user_role TEXT NOT NULL DEFAULT 'student',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
```

**Fields:**
- `id` - Primary key
- `assistant_id` - Assistant ID (as string)
- `assistant_name` - Assistant name
- `group_id` - OWI group ID
- `group_name` - OWI group name
- `assistant_owner` - Owner email
- `user_email` - Student email
- `user_name` - Student name
- `user_display_name` - Display name
- `user_role` - LTI role (Learner, Instructor, etc.)
- `created_at` - Unix timestamp
- `updated_at` - Unix timestamp

**Purpose:** Track LTI launches for analytics

---

### Usage Logs Table

```sql
CREATE TABLE usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    user_id INTEGER,
    assistant_id INTEGER,
    usage_data JSON NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    FOREIGN KEY (user_id) REFERENCES Creator_users(id),
    FOREIGN KEY (assistant_id) REFERENCES assistants(id)
);
```

**Fields:**
- `id` - Primary key
- `organization_id` - Foreign key to organizations
- `user_id` - Foreign key to Creator_users (nullable)
- `assistant_id` - Foreign key to assistants (nullable)
- `usage_data` - JSON event data
- `created_at` - Unix timestamp

**Usage Data Structure:**
```json
{
  "event": "completion",
  "tokens_used": 150,
  "model": "gpt-4o-mini",
  "duration_ms": 1234
}
```

---

## Open WebUI Database

**Location:** `$OWI_PATH/webui.db`  
**Engine:** SQLite 3  
**Managed by:** Open WebUI (LAMB reads/writes via OWI bridge)

---

### User Table

```sql
CREATE TABLE user (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    profile_image_url TEXT,
    api_key TEXT UNIQUE,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    last_active_at INTEGER NOT NULL,
    settings TEXT,
    info TEXT,
    oauth_sub TEXT
);
```

**Fields:**
- `id` - UUID primary key
- `name` - Display name
- `email` - Email address (unique)
- `role` - user | admin
- `profile_image_url` - Avatar URL
- `api_key` - Optional API key
- `created_at` - Unix timestamp
- `updated_at` - Unix timestamp
- `last_active_at` - Unix timestamp
- `settings` - JSON settings
- `info` - JSON additional info
- `oauth_sub` - OAuth subject (if OAuth login)

---

### Auth Table

```sql
CREATE TABLE auth (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    active INTEGER NOT NULL
);
```

**Fields:**
- `id` - UUID (matches user.id)
- `email` - Email address (unique)
- `password` - bcrypt hashed password
- `active` - 1 = active, 0 = disabled

**Password Hashing:** bcrypt with cost factor 12

---

### Group Table

```sql
CREATE TABLE group (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    name TEXT,
    description TEXT,
    data JSON,
    meta JSON,
    permissions JSON,
    user_ids JSON,
    created_at INTEGER,
    updated_at INTEGER,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

**Fields:**
- `id` - UUID primary key
- `user_id` - Creator's user ID
- `name` - Group name
- `description` - Group description
- `data` - JSON data
- `meta` - JSON metadata
- `permissions` - JSON permissions (see structure below)
- `user_ids` - JSON array of member IDs
- `created_at` - Unix timestamp
- `updated_at` - Unix timestamp

**Permissions Structure:**
```json
{
  "read": {
    "group_ids": [],
    "user_ids": ["user-uuid-1", "user-uuid-2"]
  },
  "write": {
    "group_ids": [],
    "user_ids": ["creator-uuid"]
  }
}
```

---

### Model Table

```sql
CREATE TABLE model (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    base_model_id TEXT,
    name TEXT,
    params JSON,
    meta JSON,
    created_at INTEGER,
    updated_at INTEGER,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

**Fields:**
- `id` - Model ID (e.g., `lamb_assistant.1`)
- `user_id` - Creator's OWI user ID
- `base_model_id` - Backend URL for completions
- `name` - Model/assistant name
- `params` - JSON parameters
- `meta` - JSON metadata
- `created_at` - Unix timestamp
- `updated_at` - Unix timestamp

**Published Assistant Example:**
```json
{
  "id": "lamb_assistant.42",
  "base_model_id": "http://lamb-backend:9099/v1/chat/completions",
  "name": "CS101 Assistant",
  "params": {
    "model": "lamb_assistant.42"
  },
  "meta": {
    "description": "Learning assistant for CS101",
    "profile_image_url": "/static/img/lamb_1.png"
  }
}
```

---

## Database Migrations

### Adding user_type Column

**Migration Script:**

```python
def run_migrations(self):
    """Run database migrations for schema updates"""
    cursor = self.conn.cursor()
    
    # Check if user_type column exists
    cursor.execute(f"PRAGMA table_info({self.table_prefix}Creator_users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'user_type' not in columns:
        # Add user_type column with default 'creator'
        cursor.execute(f"""
            ALTER TABLE {self.table_prefix}Creator_users 
            ADD COLUMN user_type TEXT NOT NULL DEFAULT 'creator' 
            CHECK(user_type IN ('creator', 'end_user'))
        """)
        self.conn.commit()
        logger.info("Added user_type column to Creator_users table")
```

**Run on:** Database initialization

---

## Indexes (Recommended)

```sql
-- Creator users by email (frequent lookup)
CREATE INDEX idx_creator_users_email ON Creator_users(user_email);

-- Assistants by owner (list user's assistants)
CREATE INDEX idx_assistants_owner ON assistants(owner);

-- Assistants by organization (org queries)
CREATE INDEX idx_assistants_org ON assistants(organization_id);

-- Organization roles lookup
CREATE INDEX idx_org_roles_user ON organization_roles(user_id);
CREATE INDEX idx_org_roles_org ON organization_roles(organization_id);

-- LTI users by email (launch lookup)
CREATE INDEX idx_lti_users_email ON lti_users(user_email);

-- Usage logs by organization (analytics)
CREATE INDEX idx_usage_logs_org ON usage_logs(organization_id);
```

---

## Common Queries

### Get User's Organization

```sql
SELECT o.* 
FROM organizations o
INNER JOIN Creator_users u ON u.organization_id = o.id
WHERE u.id = ?
```

### List User's Assistants

```sql
SELECT * FROM assistants
WHERE owner = ? AND organization_id = ?
ORDER BY created_at DESC
```

### Get Organization Role

```sql
SELECT role FROM organization_roles
WHERE organization_id = ? AND user_id = ?
```

### Find Organization by Signup Key

```sql
SELECT * FROM organizations
WHERE json_extract(config, '$.features.signup_key') = ?
AND json_extract(config, '$.features.signup_enabled') = true
```

### List Published Assistants

```sql
SELECT * FROM assistants
WHERE published = TRUE
ORDER BY published_at DESC
```

---

## Data Types

### Unix Timestamps

All timestamps stored as INTEGER (Unix epoch):

```python
import time
timestamp = int(time.time())
```

### JSON Fields

Stored as TEXT, parsed in application:

```python
import json

# Store
config_json = json.dumps(config_dict)

# Retrieve
config_dict = json.loads(config_json)
```

### Boolean Fields

SQLite doesn't have BOOLEAN type, uses INTEGER:
- `0` = False
- `1` = True

```python
# Store
published = 1 if is_published else 0

# Retrieve
is_published = bool(published)
```

---

## Backup and Maintenance

### Backup

```bash
# LAMB database
sqlite3 /opt/lamb/lamb_v4.db ".backup '/backup/lamb_v4_backup.db'"

# OWI database
sqlite3 /app/backend/data/webui.db ".backup '/backup/webui_backup.db'"
```

### Vacuum (Optimize)

```bash
sqlite3 /opt/lamb/lamb_v4.db "VACUUM;"
```

### Integrity Check

```bash
sqlite3 /opt/lamb/lamb_v4.db "PRAGMA integrity_check;"
```

---

## Related Documentation

- **Backend Architecture:** `backend_architecture.md`
- **Organizations:** `backend_organizations.md`
- **Authentication:** `backend_authentication.md`
- **Completions Pipeline:** `backend_completions_pipeline.md`

