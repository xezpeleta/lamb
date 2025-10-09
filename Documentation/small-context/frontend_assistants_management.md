# Frontend: Assistants Management

**Purpose:** UI components and flows for creating, editing, and managing AI assistants  
**Related Docs:** `frontend_architecture.md`, `backend_completions_pipeline.md`, `api_reference.md`

---

## Overview

The assistants management interface allows creators to:
- List their assistants
- Create new assistants
- Edit assistant configuration
- Test assistants via chat
- Publish assistants for LTI/student access
- Delete assistants

---

## Key Components

### AssistantsList.svelte

**Location:** `/src/lib/components/AssistantsList.svelte`

**Purpose:** Display user's assistants with actions

**Features:**
- Grid/list view of assistants
- Quick actions: Edit, Test, Publish, Delete
- Search/filter by name
- Status badges (Published/Draft)

**Usage:**
```svelte
<script>
    import AssistantsList from '$lib/components/AssistantsList.svelte';
    import { userStore } from '$lib/stores/userStore.js';
    
    let assistants = [];
    let loading = true;
    
    async function loadAssistants() {
        const response = await assistantService.getAssistants($userStore.token);
        assistants = response.assistants;
        loading = false;
    }
</script>

<AssistantsList 
    {assistants} 
    {loading}
    on:edit={handleEdit}
    on:delete={handleDelete}
/>
```

---

### AssistantForm.svelte

**Location:** `/src/lib/components/assistants/AssistantForm.svelte`

**Purpose:** Create or edit assistant configuration

**Form Fields:**

| Field | Type | Purpose | Required |
|-------|------|---------|----------|
| Name | Text | Assistant display name | Yes |
| Description | Textarea | Assistant description | No |
| System Prompt | Textarea | Instructions for AI behavior | Yes |
| Prompt Template | Text | Message formatting template | No |
| LLM Connector | Dropdown | Provider (openai, ollama) | Yes |
| Model | Dropdown | Specific model name | Yes |
| Prompt Processor | Dropdown | Message processor plugin | Yes |
| RAG Processor | Dropdown | RAG plugin (optional) | No |
| Knowledge Bases | Multi-select | Associated collections | No |
| Top K Results | Number | RAG retrieval count | If RAG enabled |

**State Management:**

Uses `assistantConfigStore.js` to manage form state:

```javascript
// assistantConfigStore.js
export const assistantConfigStore = writable({
    name: '',
    description: '',
    system_prompt: '',
    prompt_template: 'User: {user_message}\nAssistant:',
    metadata: {
        connector: 'openai',
        llm: 'gpt-4o-mini',
        prompt_processor: 'simple_augment',
        rag_processor: ''
    },
    RAG_collections: '',
    RAG_Top_k: 3
});
```

**Validation:**

```javascript
function validateForm() {
    const errors = [];
    
    if (!$assistantConfigStore.name) {
        errors.push('Name is required');
    }
    
    if (!$assistantConfigStore.system_prompt) {
        errors.push('System prompt is required');
    }
    
    if (!$assistantConfigStore.metadata.connector) {
        errors.push('Connector is required');
    }
    
    if ($assistantConfigStore.metadata.rag_processor && !$assistantConfigStore.RAG_collections) {
        errors.push('Knowledge Bases required when RAG processor is selected');
    }
    
    return errors;
}
```

**Save Flow:**

```javascript
async function saveAssistant() {
    const errors = validateForm();
    if (errors.length > 0) {
        alert(errors.join('\n'));
        return;
    }
    
    const assistantData = {
        name: $assistantConfigStore.name,
        description: $assistantConfigStore.description,
        system_prompt: $assistantConfigStore.system_prompt,
        prompt_template: $assistantConfigStore.prompt_template,
        metadata: JSON.stringify($assistantConfigStore.metadata),
        RAG_collections: $assistantConfigStore.RAG_collections,
        RAG_Top_k: $assistantConfigStore.RAG_Top_k
    };
    
    try {
        if (editMode) {
            await assistantService.updateAssistant($userStore.token, assistantId, assistantData);
        } else {
            await assistantService.createAssistant($userStore.token, assistantData);
        }
        goto('/assistants');
    } catch (error) {
        alert('Failed to save assistant: ' + error.message);
    }
}
```

---

### ChatInterface.svelte

**Location:** `/src/lib/components/ChatInterface.svelte`

**Purpose:** Test assistant before publishing

**Features:**
- Send messages to assistant
- Display conversation history
- Streaming response support
- Source citations (if RAG enabled)

**Usage:**

```svelte
<ChatInterface assistantId={selectedAssistantId} />
```

**Implementation:**

```javascript
async function sendMessage() {
    const userMessage = { role: 'user', content: inputText };
    messages = [...messages, userMessage];
    inputText = '';
    
    try {
        const response = await axios.post(
            `${config.api.lambServer}/v1/chat/completions`,
            {
                model: `lamb_assistant.${assistantId}`,
                messages: messages,
                stream: false
            },
            {
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        const assistantMessage = {
            role: 'assistant',
            content: response.data.choices[0].message.content
        };
        messages = [...messages, assistantMessage];
    } catch (error) {
        console.error('Chat error:', error);
    }
}
```

---

### PublishModal.svelte

**Location:** `/src/lib/components/PublishModal.svelte`

**Purpose:** Publish assistant for LTI integration

**Publish Options:**

| Option | Description | Default |
|--------|-------------|---------|
| Group Name | OWI group for access control | Assistant name |
| OAuth Consumer Name | LTI consumer identifier | Generated |

**Publish Flow:**

```javascript
async function publishAssistant() {
    try {
        const result = await assistantService.publishAssistant(
            $userStore.token,
            assistantId,
            {
                group_name: groupName,
                oauth_consumer_name: consumerName
            }
        );
        
        // Show LTI configuration to user
        showLTIConfig(result);
    } catch (error) {
        alert('Publish failed: ' + error.message);
    }
}

function showLTIConfig(result) {
    // Display:
    // - Launch URL
    // - Consumer Key
    // - Shared Secret
    // - XML config download
}
```

**LTI Configuration Display:**

After publishing, show educator:
- **Launch URL:** `https://your-domain.com/lamb/simple_lti/launch`
- **Consumer Key:** `{oauth_consumer_name}`
- **Shared Secret:** `{generated_secret}`
- **Custom Parameter:** `assistant_id={assistant_id}`

---

## Service Layer

### assistantService.js

**Location:** `/src/lib/services/assistantService.js`

**Methods:**

```javascript
export const assistantService = {
    // List assistants
    async getAssistants(token) {
        const response = await axios.get(`${API_URL}/list`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    },
    
    // Get single assistant
    async getAssistant(token, id) {
        const response = await axios.get(`${API_URL}/${id}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    },
    
    // Create assistant
    async createAssistant(token, data) {
        const response = await axios.post(`${API_URL}/create`, data, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    },
    
    // Update assistant
    async updateAssistant(token, id, data) {
        const response = await axios.put(`${API_URL}/${id}`, data, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    },
    
    // Delete assistant
    async deleteAssistant(token, id) {
        const response = await axios.delete(`${API_URL}/${id}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.data;
    },
    
    // Publish assistant
    async publishAssistant(token, id, publishData) {
        const response = await axios.post(
            `${API_URL}/${id}/publish`,
            publishData,
            {
                headers: { Authorization: `Bearer ${token}` }
            }
        );
        return response.data;
    },
    
    // Unpublish assistant
    async unpublishAssistant(token, id) {
        const response = await axios.post(
            `${API_URL}/${id}/unpublish`,
            {},
            {
                headers: { Authorization: `Bearer ${token}` }
            }
        );
        return response.data;
    }
};
```

---

## Assistant Configuration

### Metadata Structure

The `metadata` field stores plugin configuration as JSON:

```json
{
  "connector": "openai",
  "llm": "gpt-4o-mini",
  "prompt_processor": "simple_augment",
  "rag_processor": "simple_rag"
}
```

**Important:** Backend stores this in `api_callback` column (see `database_schema.md`)

### Available Plugins

**Connectors:**
- `openai` - OpenAI API
- `ollama` - Local Ollama models
- `bypass` - Testing only

**Prompt Processors:**
- `simple_augment` - Adds system prompt and RAG context

**RAG Processors:**
- `simple_rag` - Query Knowledge Base and inject context
- `no_rag` - Disable RAG
- *(empty string)* - No RAG

**Models:**
- Depends on organization configuration
- Common: `gpt-4o`, `gpt-4o-mini`, `gpt-4`, `llama3.1:latest`

---

## User Experience Patterns

### Creating an Assistant

1. Navigate to `/assistants`
2. Click "Create Assistant"
3. Fill in basic info (name, description)
4. Write system prompt (instructions for AI)
5. Select connector and model
6. (Optional) Enable RAG and select Knowledge Bases
7. Test via chat interface
8. Save assistant

### Editing an Assistant

1. Click "Edit" on assistant card
2. Modify fields
3. Re-test if needed
4. Save changes

**Warning:** Editing published assistants affects live students

### Publishing an Assistant

1. Ensure assistant is tested and working
2. Click "Publish"
3. Configure group name and consumer key
4. Get LTI configuration
5. Add to LMS (Canvas, Moodle, etc.)

See `backend_lti_integration.md` for LTI technical details.

---

## Common Tasks

### Load Models from Organization Config

```javascript
async function loadAvailableModels() {
    try {
        const response = await axios.get(
            `${config.api.lambServer}/creator/admin/organizations/${orgSlug}/config`,
            {
                headers: { Authorization: `Bearer ${$userStore.token}` }
            }
        );
        
        const orgConfig = response.data;
        const providers = orgConfig.setups?.default?.providers || {};
        
        // Extract OpenAI models
        if (providers.openai?.enabled) {
            availableModels.openai = providers.openai.models || [];
        }
        
        // Extract Ollama models
        if (providers.ollama?.enabled) {
            availableModels.ollama = providers.ollama.models || [];
        }
    } catch (error) {
        console.error('Failed to load models:', error);
    }
}
```

### Show RAG Collections Selector

```svelte
<script>
    let knowledgeBases = [];
    let selectedCollections = [];
    
    onMount(async () => {
        const response = await knowledgeBaseService.list($userStore.token);
        knowledgeBases = response.collections;
    });
</script>

<label>
    <span>Knowledge Bases (RAG)</span>
    <select multiple bind:value={selectedCollections}>
        {#each knowledgeBases as kb}
            <option value={kb.id}>{kb.name}</option>
        {/each}
    </select>
</label>

<!-- Store as comma-separated string -->
<input 
    type="hidden" 
    bind:value={$assistantConfigStore.RAG_collections}
    value={selectedCollections.join(',')}
/>
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Name already exists" | Duplicate assistant name | Choose different name |
| "Invalid connector" | Unknown plugin | Select valid connector |
| "No API key configured" | Org missing LLM config | Configure in org settings |
| "Knowledge Base not found" | Invalid collection ID | Refresh KB list |

### User Feedback

```svelte
<script>
    let errorMessage = '';
    let successMessage = '';
    
    async function handleSave() {
        try {
            await saveAssistant();
            successMessage = 'Assistant saved successfully!';
            setTimeout(() => successMessage = '', 3000);
        } catch (error) {
            errorMessage = error.response?.data?.detail || error.message;
        }
    }
</script>

{#if errorMessage}
    <div class="alert alert-error">{errorMessage}</div>
{/if}

{#if successMessage}
    <div class="alert alert-success">{successMessage}</div>
{/if}
```

---

## Related Documentation

- **Frontend Architecture:** `frontend_architecture.md`
- **Backend Completions:** `backend_completions_pipeline.md`
- **Knowledge Base UI:** `frontend_kb_management.md`
- **Publishing & LTI:** `backend_lti_integration.md`
- **API Endpoints:** `api_reference.md`

