# Frontend: Organization Management

**Purpose:** Admin panels for system and organization-level administration  
**Related Docs:** `frontend_architecture.md`, `backend_organizations.md`, `backend_authentication.md`

---

## Overview

LAMB provides two levels of administration:
1. **System Admin** (`/admin`) - Manage all organizations, create system-wide users
2. **Organization Admin** (`/org-admin`) - Manage specific organization, create org users

---

## System Admin Panel

**Route:** `/admin`  
**Access:** System administrators only  
**Location:** `/src/routes/admin/+page.svelte`

### Features

#### User Management

- List all users across all organizations
- Create new users (creator or end_user)
- Update user roles
- Enable/disable users
- Assign users to organizations

#### Organization Management

- List all organizations
- Create new organizations
- Update organization config
- View organization members
- Manage organization roles

---

### Admin Panel Components

#### UserManagement.svelte

**Purpose:** System-wide user administration

**Features:**

```svelte
<script>
    let users = [];
    let showCreateModal = false;
    
    async function loadUsers() {
        const response = await axios.get(
            `${config.api.lambServer}/creator/users`,
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        users = response.data;
    }
    
    async function createUser(userData) {
        await axios.post(
            `${config.api.lambServer}/creator/admin/users/create`,
            {
                email: userData.email,
                name: userData.name,
                password: userData.password,
                role: userData.role,  // 'admin' or 'user'
                user_type: userData.user_type,  // 'creator' or 'end_user'
                organization_id: userData.organization_id
            },
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        await loadUsers();
    }
    
    async function toggleUserStatus(userId, currentStatus) {
        await axios.put(
            `${config.api.lambServer}/creator/admin/users/${userId}/status`,
            { enabled: !currentStatus },
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        await loadUsers();
    }
</script>

<table>
    <thead>
        <tr>
            <th>Email</th>
            <th>Name</th>
            <th>Role</th>
            <th>Type</th>
            <th>Organization</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {#each users as user}
            <tr>
                <td>{user.email}</td>
                <td>{user.name}</td>
                <td>{user.role}</td>
                <td>{user.user_type}</td>
                <td>{user.organization_name || 'System'}</td>
                <td>
                    <span class="badge {user.enabled ? 'badge-success' : 'badge-error'}">
                        {user.enabled ? 'Active' : 'Disabled'}
                    </span>
                </td>
                <td>
                    <button on:click={() => toggleUserStatus(user.id, user.enabled)}>
                        {user.enabled ? 'Disable' : 'Enable'}
                    </button>
                </td>
            </tr>
        {/each}
    </tbody>
</table>
```

**User Types:**
- **creator:** Can access LAMB creator interface
- **end_user:** Redirected to Open WebUI on login

See `backend_authentication.md` for end_user implementation details.

---

#### OrganizationManagement.svelte

**Purpose:** Manage organizations

**Features:**

```svelte
<script>
    let organizations = [];
    let showCreateModal = false;
    
    async function loadOrganizations() {
        const response = await axios.get(
            `${config.api.lambServer}/creator/admin/organizations`,
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        organizations = response.data;
    }
    
    async function createOrganization(orgData) {
        await axios.post(
            `${config.api.lambServer}/creator/admin/organizations/enhanced`,
            {
                slug: orgData.slug,
                name: orgData.name,
                admin_user_id: orgData.admin_user_id,
                signup_enabled: orgData.signup_enabled,
                signup_key: orgData.signup_key,
                use_system_baseline: true
            },
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        await loadOrganizations();
    }
</script>

<table>
    <thead>
        <tr>
            <th>Slug</th>
            <th>Name</th>
            <th>Status</th>
            <th>Members</th>
            <th>Signup</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {#each organizations as org}
            <tr>
                <td>{org.slug}</td>
                <td>{org.name}</td>
                <td>{org.status}</td>
                <td>{org.member_count}</td>
                <td>
                    {#if org.signup_enabled}
                        <span class="badge badge-success">Enabled</span>
                    {:else}
                        <span class="badge badge-error">Disabled</span>
                    {/if}
                </td>
                <td>
                    <button on:click={() => editOrganization(org)}>Edit</button>
                    <button on:click={() => viewConfig(org)}>Config</button>
                </td>
            </tr>
        {/each}
    </tbody>
</table>
```

---

#### CreateOrganizationModal.svelte

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Slug | Text | Yes | URL-safe identifier |
| Name | Text | Yes | Display name |
| Admin User | Dropdown | Yes | Organization owner |
| Signup Enabled | Checkbox | No | Allow signup with key |
| Signup Key | Text | Conditional | Required if signup enabled |
| Use System Baseline | Checkbox | No | Inherit system config |

**Validation:**

```javascript
function validateOrgForm() {
    const errors = [];
    
    if (!slug || !/^[a-z0-9-]+$/.test(slug)) {
        errors.push('Slug must be lowercase alphanumeric with dashes');
    }
    
    if (!name) {
        errors.push('Name is required');
    }
    
    if (!adminUserId) {
        errors.push('Admin user is required');
    }
    
    if (signupEnabled && !signupKey) {
        errors.push('Signup key required when signup is enabled');
    }
    
    return errors;
}
```

---

## Organization Admin Panel

**Route:** `/org-admin`  
**Access:** Organization admins and owners  
**Location:** `/src/routes/org-admin/+page.svelte`

### Features

#### Organization User Management

- List users in organization
- Create new org users
- Manage user roles within org
- Remove users from org

#### Organization Configuration

- Edit LLM provider settings
- Configure Knowledge Base server
- Set assistant defaults
- Manage signup settings

---

### Org Admin Components

#### OrgUserManagement.svelte

**Purpose:** Manage users within organization

```svelte
<script>
    let orgUsers = [];
    let currentOrg = null;
    
    onMount(async () => {
        await loadCurrentOrg();
        await loadOrgUsers();
    });
    
    async function loadCurrentOrg() {
        const response = await axios.get(
            `${config.api.lambServer}/creator/admin/organizations/current`,
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        currentOrg = response.data;
    }
    
    async function loadOrgUsers() {
        const response = await axios.get(
            `${config.api.lambServer}/creator/admin/org-admin/users`,
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        orgUsers = response.data;
    }
    
    async function createOrgUser(userData) {
        await axios.post(
            `${config.api.lambServer}/creator/admin/org-admin/users/create`,
            {
                email: userData.email,
                name: userData.name,
                password: userData.password,
                user_type: userData.user_type,  // 'creator' or 'end_user'
                role: userData.role || 'member'
            },
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        await loadOrgUsers();
    }
</script>
```

**Organization Roles:**
- **owner:** Full control over organization
- **admin:** Can manage org settings and members
- **member:** Can create assistants within org

---

#### OrgConfigEditor.svelte

**Purpose:** Edit organization configuration

**Configuration Sections:**

1. **LLM Providers**
2. **Knowledge Base Server**
3. **Assistant Defaults**
4. **Signup Settings**
5. **Metadata**

**Implementation:**

```svelte
<script>
    let config = {
        setups: {
            default: {
                providers: {
                    openai: {
                        enabled: false,
                        api_key: '',
                        base_url: 'https://api.openai.com/v1',
                        default_model: 'gpt-4o-mini',
                        models: []
                    },
                    ollama: {
                        enabled: false,
                        base_url: 'http://localhost:11434',
                        default_model: 'llama3.1:latest',
                        models: []
                    }
                }
            }
        },
        kb_server: {
            url: 'http://localhost:9090',
            api_key: ''
        },
        assistant_defaults: {
            prompt_template: 'User: {user_message}\nAssistant:',
            system_prompt: 'You are a helpful assistant.'
        },
        features: {
            signup_enabled: false,
            signup_key: ''
        }
    };
    
    async function loadConfig() {
        const response = await axios.get(
            `${config.api.lambServer}/creator/admin/organizations/${currentOrg.slug}/config`,
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        config = response.data;
    }
    
    async function saveConfig() {
        await axios.put(
            `${config.api.lambServer}/creator/admin/organizations/${currentOrg.slug}/config`,
            config,
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        alert('Configuration saved!');
    }
</script>

<!-- OpenAI Provider -->
<section class="config-section">
    <h3>OpenAI Provider</h3>
    <label>
        <input type="checkbox" bind:checked={config.setups.default.providers.openai.enabled} />
        Enabled
    </label>
    
    {#if config.setups.default.providers.openai.enabled}
        <label>
            API Key
            <input 
                type="password" 
                bind:value={config.setups.default.providers.openai.api_key}
                placeholder="sk-..."
            />
        </label>
        
        <label>
            Base URL
            <input 
                type="url" 
                bind:value={config.setups.default.providers.openai.base_url}
            />
        </label>
        
        <label>
            Default Model
            <input 
                type="text" 
                bind:value={config.setups.default.providers.openai.default_model}
            />
        </label>
        
        <label>
            Available Models (comma-separated)
            <input 
                type="text" 
                value={config.setups.default.providers.openai.models.join(', ')}
                on:change={(e) => {
                    config.setups.default.providers.openai.models = 
                        e.target.value.split(',').map(m => m.trim());
                }}
            />
        </label>
    {/if}
</section>

<!-- Similar sections for Ollama, KB Server, etc. -->

<button on:click={saveConfig}>Save Configuration</button>
```

---

## Assistant Access Management

**New Feature:** Control which users can access specific assistants within an organization

**Component:** `AssistantAccessManager.svelte`  
**Location:** `/src/lib/components/AssistantAccessManager.svelte`

**Purpose:** Manage user permissions for assistants

```svelte
<script>
    export let assistantId;
    
    let orgUsers = [];
    let assistantUsers = [];
    
    async function loadAssistantAccess() {
        const response = await axios.get(
            `${config.api.lambServer}/creator/admin/org-admin/assistants/${assistantId}/users`,
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        assistantUsers = response.data;
    }
    
    async function grantAccess(userId) {
        await axios.post(
            `${config.api.lambServer}/creator/admin/org-admin/assistants/${assistantId}/grant-access`,
            { user_id: userId },
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        await loadAssistantAccess();
    }
    
    async function revokeAccess(userId) {
        await axios.post(
            `${config.api.lambServer}/creator/admin/org-admin/assistants/${assistantId}/revoke-access`,
            { user_id: userId },
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        await loadAssistantAccess();
    }
</script>

<div class="access-manager">
    <h3>Assistant Access Control</h3>
    
    <div class="user-list">
        {#each orgUsers as user}
            <div class="user-item">
                <span>{user.name} ({user.email})</span>
                {#if assistantUsers.includes(user.id)}
                    <button on:click={() => revokeAccess(user.id)}>
                        Revoke Access
                    </button>
                {:else}
                    <button on:click={() => grantAccess(user.id)}>
                        Grant Access
                    </button>
                {/if}
            </div>
        {/each}
    </div>
</div>
```

---

## Organization Signup Flow

### User Perspective

1. User visits signup page
2. Enters email, name, password, and **signup key**
3. System finds organization with matching signup key
4. User created in that organization as "member"
5. User can now create assistants within org context

### Admin Setup

1. Admin creates organization with signup enabled
2. Admin sets unique signup key (e.g., "cs-dept-2024")
3. Admin shares signup key with intended users
4. Users sign up with key and auto-join organization

**Security:**
- Unique keys per organization
- Can disable signup anytime
- Keys should be rotated periodically

---

## Service Layer

### organizationService.js

**Location:** `/src/lib/services/organizationService.js`

```javascript
import axios from 'axios';
import { getConfig } from '../config.js';

const config = getConfig();
const API_URL = `${config.api.lambServer}/creator/admin`;

export const organizationService = {
    // List all organizations (system admin)
    async list(token) {
        const response = await axios.get(`${API_URL}/organizations`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    },
    
    // Create organization (system admin)
    async create(token, orgData) {
        const response = await axios.post(
            `${API_URL}/organizations/enhanced`,
            orgData,
            {
                headers: { Authorization: `Bearer ${token}` }
            }
        );
        return response.data;
    },
    
    // Get organization config
    async getConfig(token, slug) {
        const response = await axios.get(
            `${API_URL}/organizations/${slug}/config`,
            {
                headers: { Authorization: `Bearer ${token}` }
            }
        );
        return response.data;
    },
    
    // Update organization config
    async updateConfig(token, slug, config) {
        const response = await axios.put(
            `${API_URL}/organizations/${slug}/config`,
            config,
            {
                headers: { Authorization: `Bearer ${token}` }
            }
        );
        return response.data;
    },
    
    // Get current user's organization
    async getCurrent(token) {
        const response = await axios.get(
            `${API_URL}/organizations/current`,
            {
                headers: { Authorization: `Bearer ${token}` }
            }
        );
        return response.data;
    }
};
```

---

## Access Control

### Role Permissions

| Action | System Admin | Org Owner | Org Admin | Org Member |
|--------|--------------|-----------|-----------|------------|
| Create organization | ✓ | ✗ | ✗ | ✗ |
| View all orgs | ✓ | ✗ | ✗ | ✗ |
| Edit own org config | ✓ | ✓ | ✓ | ✗ |
| Create org users | ✓ | ✓ | ✓ | ✗ |
| Create assistants | ✓ | ✓ | ✓ | ✓ |
| View org assistants | ✓ | ✓ | ✓ | ✓ |

### Frontend Route Protection

```svelte
<!-- /admin/+page.svelte -->
<script>
    import { userStore } from '$lib/stores/userStore.js';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    
    onMount(() => {
        if ($userStore.role !== 'admin') {
            goto('/assistants');
        }
    });
</script>
```

```svelte
<!-- /org-admin/+page.svelte -->
<script>
    onMount(async () => {
        // Check if user has org admin role
        const hasAccess = await checkOrgAdminAccess($userStore.token);
        if (!hasAccess) {
            goto('/assistants');
        }
    });
</script>
```

---

## Common Tasks

### Add LLM Provider to Organization

1. Navigate to `/org-admin`
2. Click "Configuration"
3. Enable provider (OpenAI/Ollama)
4. Enter API key (if required)
5. Add available models
6. Save configuration

### Create Organization with Signup

1. System admin goes to `/admin`
2. Click "Create Organization"
3. Fill in slug, name, admin user
4. Check "Enable Signup"
5. Enter unique signup key
6. Save organization
7. Share signup key with intended users

### Grant User Access to Assistant

1. Navigate to assistant detail page
2. Click "Manage Access"
3. Select users to grant/revoke access
4. Save changes

---

## Related Documentation

- **Frontend Architecture:** `frontend_architecture.md`
- **Backend Organizations:** `backend_organizations.md`
- **Backend Authentication:** `backend_authentication.md`
- **Database Schema:** `database_schema.md`

