# Frontend Architecture

**Purpose:** Overview of LAMB frontend structure, routing, and configuration  
**Related Docs:** `frontend_assistants_management.md`, `frontend_kb_management.md`, `frontend_org_management.md`

---

## Technology Stack

- **Svelte 5** - Latest reactivity model
- **SvelteKit** - SSR and routing framework
- **TailwindCSS** - Utility-first styling
- **Axios** - HTTP client for API calls
- **svelte-i18n** - Internationalization

---

## Project Structure

```
/frontend/svelte-app/
├── src/
│   ├── routes/              # Page routes (SvelteKit convention)
│   │   ├── +layout.svelte   # Root layout with Nav
│   │   ├── +page.svelte     # Home (redirects to /assistants)
│   │   ├── assistants/
│   │   │   └── +page.svelte # Assistants list page
│   │   ├── knowledgebases/
│   │   │   └── +page.svelte # Knowledge Bases list page
│   │   ├── admin/
│   │   │   └── +page.svelte # System admin panel
│   │   └── org-admin/
│   │       └── +page.svelte # Organization admin panel
│   ├── lib/
│   │   ├── components/      # Reusable UI components
│   │   ├── services/        # API service modules
│   │   ├── stores/          # Svelte stores for state management
│   │   ├── utils/           # Utility functions
│   │   ├── locales/         # i18n translation files
│   │   ├── config.js        # Runtime configuration loader
│   │   └── i18n.js          # i18n setup
│   ├── app.html             # HTML template
│   └── app.css              # Global styles
├── static/
│   ├── config.js            # Runtime config (created from sample)
│   ├── config.js.sample     # Config template
│   └── favicon.png
├── package.json
├── vite.config.js
└── svelte.config.js
```

---

## Routing Structure

**Key Routes:**

| Route | Purpose | Access Level |
|-------|---------|--------------|
| `/` | Home - redirects to /assistants | Authenticated |
| `/assistants` | List and manage assistants | Creator users |
| `/knowledgebases` | List and manage Knowledge Bases | Creator users |
| `/admin` | System administration panel | System admins only |
| `/org-admin` | Organization administration | Org admins |

**Route Protection:**
- All routes require authentication (except login/signup)
- Auth state managed via `userStore.js`
- Redirect to login if no valid token

---

## Configuration System

### Runtime Configuration

Frontend loads config from `/static/config.js` at runtime:

```javascript
// static/config.js
window.LAMB_CONFIG = {
    api: {
        lambServer: 'http://localhost:9099',      // LAMB Backend API
        owebuiServer: 'http://localhost:8080'     // Open WebUI URL
    }
};
```

**Why Runtime Config?**
- No rebuild needed for URL changes
- Same build works across environments
- Easy Docker volume mount for production

### Loading Config in Code

```javascript
// src/lib/config.js
export function getConfig() {
    return window.LAMB_CONFIG || {
        api: {
            lambServer: 'http://localhost:9099',
            owebuiServer: 'http://localhost:8080'
        }
    };
}
```

---

## State Management

### Svelte Stores

**Location:** `/src/lib/stores/`

| Store | Purpose | Key State |
|-------|---------|-----------|
| `userStore.js` | User session | token, email, name, role |
| `assistantStore.js` | Assistants list | assistants[], loading, error |
| `assistantConfigStore.js` | Assistant editor | current assistant config |
| `assistantPublish.js` | Publish modal | showModal, publishData |

**Store Pattern:**

```javascript
// userStore.js
import { writable } from 'svelte/store';

function createUserStore() {
    const { subscribe, set, update } = writable({
        token: localStorage.getItem('token'),
        email: localStorage.getItem('email'),
        name: localStorage.getItem('name'),
        role: localStorage.getItem('role'),
        isAuthenticated: !!localStorage.getItem('token')
    });

    return {
        subscribe,
        login: (userData) => {
            localStorage.setItem('token', userData.token);
            localStorage.setItem('email', userData.email);
            localStorage.setItem('name', userData.name);
            localStorage.setItem('role', userData.role);
            set({ ...userData, isAuthenticated: true });
        },
        logout: () => {
            localStorage.clear();
            set({ token: null, email: null, name: null, role: null, isAuthenticated: false });
        }
    };
}

export const userStore = createUserStore();
```

---

## Service Layer

**Location:** `/src/lib/services/`

Services encapsulate all API calls using Axios:

```javascript
// Example: assistantService.js
import axios from 'axios';
import { getConfig } from '../config.js';

const config = getConfig();
const API_URL = `${config.api.lambServer}/creator/assistant`;

export const assistantService = {
    async getAssistants(token) {
        const response = await axios.get(`${API_URL}/list`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    },
    
    async createAssistant(token, assistantData) {
        const response = await axios.post(`${API_URL}/create`, assistantData, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    }
    // ... more methods
};
```

---

## Authentication Flow

### Login Process

1. User enters credentials in `Login.svelte`
2. Call `authService.login(email, password)`
3. Backend validates and returns token + user data
4. Check `user_type`:
   - **creator**: Store token, navigate to `/assistants`
   - **end_user**: Redirect to Open WebUI (no LAMB interface access)
5. For creators: Token stored in localStorage and userStore

### Token Management

- Token stored in localStorage on login
- Included in all API requests: `Authorization: Bearer {token}`
- Token validated by backend on each request
- On 401 response: Clear token, redirect to login

### End User Feature

**Purpose:** Users who only need to interact with published assistants

**Flow:**
```javascript
// Login.svelte
async function handleLogin() {
    const result = await authService.login(email, password);
    
    if (result.user_type === 'end_user') {
        // Redirect to Open WebUI
        window.location.href = result.launch_url;
    } else {
        // Creator user - store token and navigate
        userStore.login(result);
        goto('/assistants');
    }
}
```

See `backend_authentication.md` for backend implementation details.

---

## Component Organization

### Shared Components

**Location:** `/src/lib/components/`

| Component | Purpose |
|-----------|---------|
| `Nav.svelte` | Navigation bar with user menu |
| `Login.svelte` | Login form |
| `Signup.svelte` | Signup form |
| `ChatInterface.svelte` | Test assistant chat |

### Feature-Specific Components

See related documentation:
- **Assistants:** `frontend_assistants_management.md`
- **Knowledge Bases:** `frontend_kb_management.md`
- **Organization Admin:** `frontend_org_management.md`

---

## Styling Approach

### TailwindCSS

Utility-first CSS with custom configuration:

```javascript
// tailwind.config.js
export default {
    content: ['./src/**/*.{html,js,svelte,ts}'],
    theme: {
        extend: {
            colors: {
                // Custom colors
            }
        }
    }
};
```

### Global Styles

```css
/* app.css */
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';

/* Custom global styles */
body {
    @apply bg-gray-50 text-gray-900;
}
```

---

## Build and Development

### Development Server

```bash
cd frontend/svelte-app
npm install
npm run dev
```

Access at: `http://localhost:5173`

### Production Build

```bash
npm run build
```

Output: `/frontend/build/` - Served by backend in production

### Environment Setup

1. Copy config template: `cp static/config.js.sample static/config.js`
2. Edit `static/config.js` with correct API URLs
3. Build or run dev server

---

## Internationalization (i18n)

### Setup

```javascript
// src/lib/i18n.js
import { addMessages, init } from 'svelte-i18n';
import en from './locales/en.json';
import es from './locales/es.json';

addMessages('en', en);
addMessages('es', es);

init({
    fallbackLocale: 'en',
    initialLocale: 'en'
});
```

### Usage in Components

```svelte
<script>
    import { _ } from 'svelte-i18n';
</script>

<h1>{$_('assistants.title')}</h1>
<button>{$_('common.save')}</button>
```

---

## API Integration

All API calls go through service layer with:
- Automatic token injection
- Error handling
- Response parsing

**Base URLs:**
- LAMB Backend: `{lambServer}/creator/*`
- Direct LAMB Core: `{lambServer}/lamb/v1/*` (rare, mostly internal)

---

## Error Handling

### Service Layer Errors

```javascript
try {
    const data = await assistantService.getAssistants(token);
    return data;
} catch (error) {
    if (error.response?.status === 401) {
        userStore.logout();
        goto('/login');
    } else {
        console.error('Failed to load assistants:', error);
        throw error;
    }
}
```

### Component Level

```svelte
<script>
    let error = null;
    let loading = true;
    
    onMount(async () => {
        try {
            await loadData();
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    });
</script>

{#if error}
    <div class="alert alert-error">{error}</div>
{/if}
```

---

## Next Steps

For specific frontend tasks, see:
- **Managing Assistants:** `frontend_assistants_management.md`
- **Knowledge Base UI:** `frontend_kb_management.md`
- **Admin Panels:** `frontend_org_management.md`
- **Backend Integration:** `backend_architecture.md`

