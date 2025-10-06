# LAMB Product Requirements Document (PRD)

**Version:** 2.0  
**Last Updated:** January 2025  
**Status:** Active Development

---

## Executive Summary

**LAMB** (Learning Assistants Manager and Builder) is an open-source platform that empowers educators to create, manage, and deploy AI-powered learning assistants directly into Learning Management Systems (LMS) without requiring technical expertise. LAMB bridges the gap between powerful Large Language Models (LLMs) and educational environments while maintaining student privacy and institutional control.

**Core Value Proposition:**
- **For Educators:** Create specialized AI tutors grounded in course materials without coding
- **For Institutions:** Deploy AI assistants while maintaining data sovereignty and privacy
- **For Students:** Access context-aware, subject-specific AI assistance within their familiar LMS environment

---

## 1. Product Vision & Goals

### 1.1 Vision Statement
To democratize AI in education by providing educators with an intuitive platform to create intelligent, privacy-respecting learning assistants that seamlessly integrate into existing educational workflows.

### 1.2 Strategic Goals
1. **Accessibility:** Enable educators without technical expertise to create AI assistants
2. **Privacy-First:** Ensure student data never leaves institutional control
3. **Integration:** Seamless deployment to LMS platforms via LTI standards
4. **Flexibility:** Support multiple LLM providers and organizational configurations
5. **Quality:** Maintain high-quality, context-aware AI responses grounded in course materials

---

## 2. Target Users & User Stories

### 2.1 Primary User Personas

#### 2.1.1 Educator (Creator User)
**Profile:** University professor, K-12 teacher, corporate trainer
- Creates and manages learning assistants
- Uploads and organizes course materials
- Tests and refines assistant behavior
- Publishes assistants to LMS courses

**Key User Stories:**
- As an educator, I want to create an AI tutor that only answers questions related to my course content
- As an educator, I want to upload PDFs and documents so the assistant can reference them
- As an educator, I want to test my assistant before making it available to students
- As an educator, I want to publish my assistant as an LTI activity in my Moodle course
- As an educator, I want to switch between different AI models (GPT-4, local models, etc.)

#### 2.1.2 Institution Administrator (System Admin)
**Profile:** IT administrator, educational technology coordinator
- Manages the LAMB deployment
- Configures LLM providers and API keys
- Creates and manages organizations
- Monitors system usage

**Key User Stories:**
- As an admin, I want to configure multiple LLM providers for different departments
- As an admin, I want to create separate organizations with isolated resources
- As an admin, I want to manage user roles and permissions
- As an admin, I want to monitor system usage across organizations

#### 2.1.3 Student (End User via LTI)
**Profile:** Learner accessing assistants through LMS
- Interacts with published learning assistants
- Receives context-aware tutoring and support
- Accesses assistants within LMS course interface

**Key User Stories:**
- As a student, I want to ask questions about course materials and get accurate answers
- As a student, I want to see sources cited when the assistant references materials
- As a student, I want to access my learning assistant directly from my Moodle course

#### 2.1.4 End User (Direct Access)
**Profile:** User with direct login access to Open WebUI
- Logs into LAMB and is automatically redirected to Open WebUI
- Does not have access to creator interface or assistant creation
- Can use published assistants and interact with the chat interface
- Can be created by admins or organization admins
- Belongs to a specific organization

**Key User Stories:**
- As an end user, I want to log into the system and be automatically directed to the chat interface
- As an end user, I want to use published learning assistants without needing to know how to create them
- As an end user, I want access limited to interaction capabilities, not creation capabilities

### 2.2 Secondary User Personas

#### 2.2.1 Educational Researcher
- Studies AI in education effectiveness
- Requires complete control over learning environment
- Needs to analyze assistant interactions

#### 2.2.2 Organization Admin
- Manages resources within a specific organization/department
- Configures organization-specific AI providers
- Manages organization members and their assistants

---

## 3. Functional Requirements

### 3.1 User Authentication & Management

#### 3.1.1 Authentication System
- **FR-AUTH-001:** System shall support email/password authentication
- **FR-AUTH-002:** System shall integrate with Open WebUI authentication
- **FR-AUTH-003:** System shall support JWT token-based sessions
- **FR-AUTH-004:** System shall allow configurable signup (enabled/disabled)
- **FR-AUTH-005:** System shall support organization-specific signup keys

#### 3.1.2 User Roles & Permissions
- **FR-USER-001:** System shall support three user roles: admin, user, member
- **FR-USER-002:** System admins shall have full system access
- **FR-USER-003:** Organization admins shall manage their organization
- **FR-USER-004:** Regular users shall create and manage their own assistants
- **FR-USER-005:** System shall allow role-based access control to assistants
- **FR-USER-006:** System shall support two user types: creator and end_user
- **FR-USER-007:** Creator users shall have access to the creator interface for managing assistants
- **FR-USER-008:** End users shall be automatically redirected to Open WebUI upon login
- **FR-USER-009:** End users shall not have access to the creator interface or assistant creation features
- **FR-USER-010:** Admins and organization admins shall be able to create both creator and end users

### 3.2 Organization Management (Multi-Tenancy)

#### 3.2.1 Organization Structure
- **FR-ORG-001:** System shall support multiple isolated organizations
- **FR-ORG-002:** Each organization shall have independent configuration
- **FR-ORG-003:** System shall maintain a "lamb" system organization
- **FR-ORG-004:** Organizations shall have configurable LLM providers
- **FR-ORG-005:** Organizations shall support custom signup keys

#### 3.2.2 Organization Configuration
- **FR-ORG-006:** Each organization shall configure OpenAI, Ollama, and other LLM providers independently
- **FR-ORG-007:** Organization configs shall include API keys, base URLs, and available models
- **FR-ORG-008:** Organization configs shall support default assistant settings
- **FR-ORG-009:** Organizations shall have status: active, suspended, or trial
- **FR-ORG-010:** System shall allow organization-specific Knowledge Base server configuration

### 3.3 Assistant Creation & Management

#### 3.3.1 Basic Assistant Operations
- **FR-ASST-001:** Users shall create assistants with name and description
- **FR-ASST-002:** Users shall edit assistant properties at any time
- **FR-ASST-003:** Users shall delete their own assistants
- **FR-ASST-004:** Users shall duplicate existing assistants
- **FR-ASST-005:** System shall prevent duplicate assistant names per user
- **FR-ASST-006:** Assistants shall belong to a specific organization

#### 3.3.2 Assistant Configuration
- **FR-ASST-007:** Users shall define system prompts to guide assistant behavior
- **FR-ASST-008:** Users shall define prompt templates for message formatting
- **FR-ASST-009:** Users shall select LLM providers (OpenAI, Ollama, etc.)
- **FR-ASST-010:** Users shall select specific models from available providers
- **FR-ASST-011:** Users shall configure RAG (Retrieval-Augmented Generation) settings
- **FR-ASST-012:** Users shall associate Knowledge Base collections with assistants

#### 3.3.3 Plugin Architecture
- **FR-ASST-013:** Assistants shall support configurable Prompt Processors (PPS)
- **FR-ASST-014:** Assistants shall support configurable Connectors (LLM integrations)
- **FR-ASST-015:** Assistants shall support configurable RAG Processors
- **FR-ASST-016:** System shall provide default plugins: simple_augment, openai connector, simple_rag
- **FR-ASST-017:** Plugin configuration shall be stored in assistant metadata field

### 3.4 Knowledge Base Management

#### 3.4.1 Knowledge Base Operations
- **FR-KB-001:** Users shall create Knowledge Base collections
- **FR-KB-002:** Users shall upload documents (PDF, Word, Markdown, TXT, JSON) to collections
- **FR-KB-003:** System shall process and vectorize uploaded documents
- **FR-KB-004:** Users shall query collections to test retrieval
- **FR-KB-005:** Users shall delete documents from collections
- **FR-KB-006:** Users shall delete entire collections
- **FR-KB-007:** Collections shall belong to a specific user and organization

#### 3.4.2 RAG Integration
- **FR-KB-008:** Assistants shall retrieve relevant context from Knowledge Base collections
- **FR-KB-009:** Users shall configure number of retrieved chunks (Top K)
- **FR-KB-010:** Users shall associate multiple collections with one assistant
- **FR-KB-011:** System shall inject retrieved context into prompts
- **FR-KB-012:** System shall provide citation/source information when available

### 3.5 Assistant Publishing & LTI Integration

#### 3.5.1 Publishing Workflow
- **FR-PUB-001:** Users shall publish assistants as LTI activities
- **FR-PUB-002:** Published assistants shall have LTI consumer credentials
- **FR-PUB-003:** Users shall configure LTI group name for published assistants
- **FR-PUB-004:** Users shall unpublish assistants at any time
- **FR-PUB-005:** System shall track publication status and timestamp

#### 3.5.2 LTI Standard Compliance
- **FR-LTI-001:** System shall support IMS LTI 1.1 standard
- **FR-LTI-002:** System shall provide LTI configuration XML/parameters
- **FR-LTI-003:** System shall authenticate LTI launch requests
- **FR-LTI-004:** System shall create/link LMS users to OWI users via LTI
- **FR-LTI-005:** System shall support trusted header authentication for LTI users

### 3.6 Chat Completions & Inference

#### 3.6.1 OpenAI API Compatibility
- **FR-COMP-001:** System shall provide OpenAI-compatible `/v1/chat/completions` endpoint
- **FR-COMP-002:** System shall support streaming and non-streaming responses
- **FR-COMP-003:** System shall provide `/v1/models` endpoint listing available assistants
- **FR-COMP-004:** System shall require API key authentication for completions
- **FR-COMP-005:** System shall return responses in OpenAI format

#### 3.6.2 Processing Pipeline
- **FR-COMP-006:** System shall execute prompt processor on user messages
- **FR-COMP-007:** System shall retrieve RAG context when configured
- **FR-COMP-008:** System shall inject system prompt and RAG context
- **FR-COMP-009:** System shall call configured LLM connector
- **FR-COMP-010:** System shall stream tokens back to client when requested
- **FR-COMP-011:** System shall resolve organization-specific LLM configuration

### 3.7 Testing & Debugging

#### 3.7.1 Assistant Testing
- **FR-TEST-001:** Users shall test assistants within the creator interface
- **FR-TEST-002:** System shall provide a chat interface for testing
- **FR-TEST-003:** Users shall see complete prompt with RAG context in debug mode
- **FR-TEST-004:** Users shall see source citations when RAG is enabled

### 3.8 Administrative Functions

#### 3.8.1 User Management (Admin)
- **FR-ADMIN-001:** Admins shall create new users with specified roles
- **FR-ADMIN-002:** Admins shall update user passwords
- **FR-ADMIN-003:** Admins shall change user roles (admin/user)
- **FR-ADMIN-004:** Admins shall enable/disable user accounts
- **FR-ADMIN-005:** Admins shall list all creator users with organization info

#### 3.8.2 Organization Management (Admin)
- **FR-ADMIN-006:** System admins shall create new organizations
- **FR-ADMIN-007:** System admins shall update organization configurations
- **FR-ADMIN-008:** System admins shall assign users to organizations with roles
- **FR-ADMIN-009:** System admins shall suspend or activate organizations
- **FR-ADMIN-010:** System admins shall configure organization-specific LLM providers

---

## 4. Non-Functional Requirements

### 4.1 Performance
- **NFR-PERF-001:** API responses shall complete within 500ms (non-LLM operations)
- **NFR-PERF-002:** System shall support streaming responses for real-time user experience
- **NFR-PERF-003:** Database queries shall be optimized with appropriate indexes
- **NFR-PERF-004:** System shall handle concurrent users per organization

### 4.2 Security
- **NFR-SEC-001:** All API endpoints shall require authentication
- **NFR-SEC-002:** Passwords shall be hashed using bcrypt
- **NFR-SEC-003:** JWT tokens shall expire and require renewal
- **NFR-SEC-004:** API keys shall be stored securely in environment variables
- **NFR-SEC-005:** LTI requests shall be validated with OAuth signatures
- **NFR-SEC-006:** Organizations shall be isolated from each other

### 4.3 Privacy
- **NFR-PRIV-001:** Student data shall never be sent to external LLM providers without institutional control
- **NFR-PRIV-002:** System shall support on-premise deployment
- **NFR-PRIV-003:** User data shall be isolated per organization
- **NFR-PRIV-004:** System shall not log sensitive information (passwords, API keys)

### 4.4 Scalability
- **NFR-SCALE-001:** System shall support multiple organizations on one instance
- **NFR-SCALE-002:** Database schema shall support table prefixing for multi-instance deployments
- **NFR-SCALE-003:** System shall support horizontal scaling via load balancing

### 4.5 Reliability
- **NFR-REL-001:** System shall have 99.5% uptime during operational hours
- **NFR-REL-002:** System shall handle LLM provider failures gracefully with fallback models
- **NFR-REL-003:** Database operations shall use transactions for data consistency
- **NFR-REL-004:** System shall log errors for debugging and monitoring

### 4.6 Usability
- **NFR-USE-001:** Interface shall support multilingual UI (English, Spanish, Catalan, Basque)
- **NFR-USE-002:** System shall provide clear error messages
- **NFR-USE-003:** Assistant creation workflow shall be intuitive for non-technical users
- **NFR-USE-004:** System shall provide contextual help and documentation

### 4.7 Compatibility
- **NFR-COMP-001:** System shall support Docker deployment
- **NFR-COMP-002:** System shall be compatible with major LMS platforms via LTI 1.1
- **NFR-COMP-003:** Frontend shall support modern web browsers (Chrome, Firefox, Safari, Edge)
- **NFR-COMP-004:** System shall support multiple LLM providers (OpenAI, Anthropic, Ollama, etc.)

---

## 5. Technical Architecture Overview

### 5.1 System Components

#### 5.1.1 Core Services
1. **LAMB Backend API** (Port 9099)
   - FastAPI-based REST API
   - Dual API architecture (Creator Interface + LAMB Core)
   - Handles authentication, assistant management, completions

2. **Open WebUI Integration** (Port 8080)
   - User authentication and management
   - Model/assistant management
   - Knowledge Base (ChromaDB) integration
   - Web chat interface for published assistants

3. **Knowledge Base Server** (Port 9090)
   - Document ingestion and processing
   - Vector database (ChromaDB)
   - Semantic search and retrieval
   - Independent service for document management

4. **Frontend Application** (Port 5173 dev / served by backend in prod)
   - Svelte 5 SPA
   - Creator interface for assistant management
   - Admin panels for user/organization management

#### 5.1.2 Technology Stack

**Backend:**
- Python 3.11
- FastAPI for REST API
- SQLite for database
- SQLModel/SQLAlchemy for ORM
- PassLib + bcrypt for password hashing
- JWT for authentication
- Requests/AIOHTTP for HTTP clients

**AI/ML:**
- OpenAI, Anthropic, Google Generative AI SDKs
- Sentence-Transformers for embeddings
- ChromaDB for vector storage
- LlamaIndex for RAG capabilities

**Frontend:**
- Svelte 5 with SvelteKit
- TailwindCSS for styling
- Axios for HTTP requests
- svelte-i18n for internationalization

**Infrastructure:**
- Docker for containerization
- Docker Compose for orchestration

### 5.2 Data Architecture

#### 5.2.1 LAMB Database Schema (SQLite)
- **organizations:** Multi-tenancy organizational units
- **organization_roles:** User-organization membership and roles
- **Creator_users:** Creator user accounts
- **assistants:** Learning assistant definitions
- **lti_users:** LTI user mappings
- **model_permissions:** User-specific model access control
- **usage_logs:** System usage tracking

#### 5.2.2 Open WebUI Database (SQLite)
- **user:** User profile information
- **auth:** Authentication credentials
- **group:** User groups for assistants
- **model:** Published assistants as models

---

## 6. User Interface Requirements

### 6.1 Creator Interface

#### 6.1.1 Login/Signup
- Clean login form with email and password
- Optional signup with organization-specific keys
- Multi-language support

#### 6.1.2 Dashboard/Assistants List
- Paginated list of user's assistants
- Search and filter capabilities
- Quick actions: edit, delete, publish, duplicate
- Create new assistant button

#### 6.1.3 Assistant Editor
- Tabbed interface for configuration sections
- Form fields for name, description, system prompt, prompt template
- LLM provider and model selection dropdowns
- RAG configuration (collection selection, Top K)
- Save and cancel actions
- Test assistant directly from editor

#### 6.1.4 Knowledge Bases
- List of user's Knowledge Base collections
- Create, view, query, and delete collections
- Upload documents with drag-and-drop
- Document list within collections
- Test query interface

#### 6.1.5 Admin Panel
- User management table (list, create, edit, disable)
- Organization management (create, edit, configure)
- System configuration

### 6.2 Student/End-User Interface
- Accessed via Open WebUI chat interface
- Integrated into LMS via LTI iframe
- Standard chat interface with message history
- Source citations when RAG is enabled

---

## 7. API Specifications

### 7.1 Core API Endpoints

#### 7.1.1 Authentication
- `POST /creator/login` - User login
- `POST /creator/signup` - User registration (if enabled)

#### 7.1.2 Assistant Management (Creator Users Only)
- `GET /creator/assistant/get_assistants` - List assistants (paginated)
- `GET /creator/assistant/get_assistant/{id}` - Get assistant details
- `POST /creator/assistant/create_assistant` - Create new assistant
- `PUT /creator/assistant/update_assistant/{id}` - Update assistant
- `DELETE /creator/assistant/delete_assistant/{id}` - Delete assistant
- `PUT /creator/assistant/publish/{id}` - Publish/unpublish assistant

#### 7.1.3 Knowledge Base Management
- `GET /creator/knowledgebases/list` - List collections
- `POST /creator/knowledgebases/create` - Create collection
- `POST /creator/knowledgebases/{collection_id}/upload` - Upload document
- `GET /creator/knowledgebases/{collection_id}/query` - Test query
- `DELETE /creator/knowledgebases/{collection_id}` - Delete collection

#### 7.1.4 Completions (OpenAI-compatible)
- `POST /v1/chat/completions` - Generate completions
- `GET /v1/models` - List available assistants
- `POST /v1/pipelines/reload` - Reload pipeline configuration

#### 7.1.5 Admin
- `GET /creator/users` - List all users (admin)
- `POST /creator/admin/users/create` - Create user (admin, supports user_type parameter)
- `PUT /creator/admin/users/update-role-by-email` - Update user role (admin)
- `PUT /creator/admin/users/{id}/status` - Enable/disable user (admin)
- `GET /creator/admin/organizations` - List organizations (admin)
- `POST /creator/admin/organizations/enhanced` - Create organization with admin (admin)

**Create User Endpoint:**
Parameters: email, name, password, role, organization_id (optional), user_type ('creator' or 'end_user', default: 'creator')

---

## 8. Integration Requirements

### 8.1 LMS Integration (LTI 1.1)
- Support for Moodle, Canvas, Blackboard, and other LTI-compliant LMS
- Provide LTI configuration URL and consumer credentials
- Handle LTI launch requests with OAuth signature validation
- Map LTI user identities to OWI users

### 8.2 LLM Provider Integration
- OpenAI API (GPT-4, GPT-4-mini, etc.)
- Anthropic API (Claude models)
- Google Generative AI
- Ollama for local models
- Extensible connector architecture for new providers

### 8.3 Knowledge Base Server Integration
- RESTful API communication
- Document upload via multipart form-data
- Query endpoint for semantic search
- Collection management

---

## 9. Deployment & Configuration

### 9.1 Deployment Models

#### 9.1.1 Docker Compose (Recommended)
- Single-command deployment
- All services orchestrated
- Suitable for development and small-scale production

#### 9.1.2 Manual Installation
- Individual service installation
- Custom configuration
- Suitable for advanced deployments

### 9.2 Environment Configuration

#### 9.2.1 Required Variables
- `LAMB_DB_PATH` - Path to LAMB database
- `OWI_PATH` - Path to Open WebUI data directory
- `LAMB_WEB_HOST` - Public-facing URL for LAMB
- `LAMB_BACKEND_HOST` - Internal URL for LAMB (typically localhost)
- `OWI_BASE_URL` - Internal URL for Open WebUI
- `OWI_PUBLIC_BASE_URL` - Public-facing URL for Open WebUI

#### 9.2.2 LLM Provider Variables (at system level, can be overridden per organization)
- `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`
- Additional provider-specific keys

---

## 10. Success Metrics

### 10.1 Adoption Metrics
- Number of creator users registered
- Number of organizations created
- Number of assistants created
- Number of assistants published to LMS
- Number of student interactions with assistants

### 10.2 Engagement Metrics
- Average sessions per creator user per week
- Average assistants per creator user
- Average documents uploaded per Knowledge Base
- Average student messages per assistant per week

### 10.3 Quality Metrics
- User satisfaction scores (surveys)
- Assistant test completion rate before publication
- Error rate in completions API
- Response time for completions

### 10.4 Technical Metrics
- System uptime percentage
- Average API response time
- LLM provider availability
- Database query performance

---

## 11. Roadmap & Future Enhancements

### 11.1 Near-Term (Next 3-6 months)
- Enhanced analytics dashboard for usage tracking
- Improved organization configuration UI
- Support for additional LLM providers (Mistral, Cohere)
- Advanced RAG techniques (hybrid search, re-ranking)
- Export/import assistant templates

### 11.2 Mid-Term (6-12 months)
- LTI 1.3 / LTI Advantage support
- Assistant versioning and rollback
- Fine-tuning support for custom models
- Multi-modal support (images, audio)
- Collaborative assistant editing

### 11.3 Long-Term (12+ months)
- Integration with major LMS APIs beyond LTI
- Marketplace for sharing assistant templates
- Advanced permission models (sharing, forking)
- Built-in analytics and learning insights
- Support for agentic workflows (tool use, function calling)

---

## 12. Compliance & Ethical Considerations

### 12.1 Safe AI in Education Manifesto Alignment

LAMB is designed to comply with the [Safe AI in Education Manifesto](https://manifesto.safeaieducation.org):

1. **Human Oversight:** Educators create, control, and manage all assistants
2. **Privacy Protection:** Self-hosted, no student data shared with external providers
3. **Educational Alignment:** Assistants are grounded in course materials and learning objectives
4. **Didactic Integration:** Seamless LMS integration via LTI
5. **Accuracy & Explainability:** RAG provides source citations
6. **Transparent Interfaces:** Clear communication of AI capabilities and limitations
7. **Ethical Training:** Open-source, academically-developed platform

### 12.2 Data Privacy
- GDPR and FERPA compliance considerations
- No personally identifiable information (PII) sent to external LLM providers without explicit configuration
- Data residency options (self-hosted, on-premise)
- Clear data retention and deletion policies

### 12.3 Responsible AI Use
- Educators trained to create appropriate system prompts
- Mechanisms to detect and prevent harmful content
- Clear attribution and citation of sources
- Transparent about AI-generated content

---

## 13. Support & Documentation

### 13.1 User Documentation
- Getting Started guide for educators
- Assistant creation best practices
- Knowledge Base management guide
- LTI integration guide for LMS administrators
- Troubleshooting guide

### 13.2 Developer Documentation
- Architecture overview
- API reference
- Plugin development guide
- Deployment guide
- Contributing guide

### 13.3 Community Support
- GitHub issues for bug reports and feature requests
- Discussion forums for community Q&A
- Email support for institutional deployments

---

## 14. Conclusion

LAMB represents a comprehensive solution for bringing AI-powered learning assistants into educational environments while maintaining privacy, control, and pedagogical alignment. By focusing on educator empowerment, institutional sovereignty, and seamless LMS integration, LAMB addresses critical needs in the evolving landscape of AI in education.

The platform's modular architecture, multi-tenancy support, and extensible plugin system ensure it can adapt to diverse institutional needs while maintaining simplicity for end users. As AI technology continues to evolve, LAMB provides a stable, ethical, and effective foundation for educational AI deployment.

---

**Document Control:**
- **Authors:** LAMB Development Team (Marc Alier, Juanan Pereira, and contributors)
- **Stakeholders:** Educators, Educational Institutions, Developers, Researchers
- **Review Cycle:** Quarterly
- **Next Review:** November 2025

