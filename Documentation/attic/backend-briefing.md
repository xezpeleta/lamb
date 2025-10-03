# LAMB Backend Briefing: Creator User Management

## Overview

The LAMB (Learning Assistant Management Backend) system integrates with Open WebUI (OWI) to provide a comprehensive solution for managing learning assistants. This document explains how creator users are managed in the LAMB system, focusing on the authentication flow, database structure, and integration with OWI.

## Backend Architecture

LAMB employs a dual API architecture consisting of two distinct internal APIs:

1. **Creator Interface API** (`/backend/creator_interface/main.py`)
   - User-facing API layer that handles frontend requests
   - Acts as a proxy to the LAMB core API, often adding additional logic
   - Manages authentication, file operations, assistant management
   - Serves templates and handles internationalization

2. **LAMB Core API** (`/backend/lamb/main.py`)
   - Internal API for core business logic
   - Not directly exposed to end users
   - Provides direct database access
   - Handles core operations for assistants, users, OWI integration

This separation of concerns creates a layered architecture where the Creator Interface API acts as a proxy and gateway to the LAMB Core API. The Creator Interface layer handles user-specific logic while the LAMB Core provides the fundamental operations.

## Creator User Architecture

Creator users in LAMB follow a two-layer authentication approach:

1. **LAMB Creator User**: The primary entity stored in the LAMB database
2. **OWI User**: A corresponding user entity in the Open WebUI system

Every creator user in LAMB has a corresponding OWI user, and LAMB leverages OWI's authentication mechanisms to provide secure access.

```
┌─────────────────┐          ┌─────────────────┐
│                 │          │                 │
│  LAMB Creator   │  1:1     │    OWI User     │
│     User        │◄────────►│                 │
│                 │          │                 │
└─────────────────┘          └─────────────────┘
```

## Database Structure

### LAMB Database (SQLite)

Creator users are stored in the `Creator_users` table with the following structure:

```sql
CREATE TABLE Creator_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    user_name TEXT NOT NULL,
    user_config JSON,
    UNIQUE(user_email)
)
```

- `id`: Unique identifier for the creator user in LAMB
- `user_email`: Email address (unique, used for authentication)
- `user_name`: Display name of the creator
- `user_config`: JSON object containing user-specific configurations

### OWI Database (Accessed via Bridge)

The OWI database is accessed through the `OwiDatabaseManager` and contains two key tables for user management:

1. **user**: Stores user profile information
   ```sql
   CREATE TABLE user (
       id TEXT PRIMARY KEY,
       name TEXT,
       email TEXT UNIQUE,
       role TEXT,
       profile_image_url TEXT,
       created_at INTEGER,
       updated_at INTEGER,
       last_active_at INTEGER
   )
   ```

2. **auth**: Stores authentication credentials
   ```sql
   CREATE TABLE auth (
       id TEXT PRIMARY KEY,
       email TEXT UNIQUE,
       password TEXT,
       active INTEGER
   )
   ```

## User Management Flow

### User Creation

When a new creator user is created:

1. The `UserCreatorManager` receives a request with email, name, and password
2. It forwards the request to the LAMB backend `/lamb/v1/creator_user/create` endpoint
3. The `create_creator_user` function in `creator_user_router.py` is called
4. The system checks if the creator user already exists in the LAMB database
5. The system then checks if a corresponding OWI user exists via `OwiUserManager`
6. If the OWI user doesn't exist, it creates one with the provided credentials
7. Finally, it creates the creator user in the LAMB database

```
┌────────────┐     ┌───────────────────┐     ┌────────────────┐     ┌─────────────┐
│            │     │                   │     │                │     │             │
│   Client   │────►│ UserCreatorManager│────►│creator_user_   │────►│OwiUserManager│
│            │     │                   │     │router.py       │     │             │
└────────────┘     └───────────────────┘     └────────────────┘     └─────────────┘
                                                      │                    │
                                                      ▼                    ▼
                                             ┌────────────────┐    ┌─────────────┐
                                             │                │    │             │
                                             │LAMB Database   │    │OWI Database │
                                             │                │    │             │
                                             └────────────────┘    └─────────────┘
```

### User Authentication

The authentication flow is as follows:

1. The user provides email and password to the `login` endpoint
2. `UserCreatorManager.verify_user()` is called, which:
   - Sends a request to `/lamb/v1/creator_user/verify`
   - The backend then uses `OwiUserManager` to verify credentials against the OWI database
3. If verification succeeds:
   - An authentication token is obtained from OWI
   - The OWI launch URL is obtained
   - User details and token are returned to the client

There's special handling for admin users:
- If an OWI admin user attempts to log in but isn't a creator user yet
- The system verifies their credentials against OWI directly
- If they're confirmed as admin, a creator user is automatically created for them

### Token Management

Authentication tokens are JWT tokens generated and managed by the OWI system:

1. The `get_auth_token` method in `OwiUserManager` obtains a token from OWI
2. This token is used for subsequent API calls to both LAMB and OWI systems
3. The token carries user identity information and is validated on each request

## Integration with Frontend

The creator user authentication system integrates with the frontend through:

1. Login/signup forms that communicate with the backend endpoints
2. Token storage in the client for session management
3. Protected API routes that require valid authentication
4. Integration with the OWI interface through the launch URL

## Open WebUI Bridge

The `owi_bridge` module provides connectivity between LAMB and OWI:

1. **OwiDatabaseManager**: Direct database access to OWI's SQLite database
2. **OwiUserManager**: User operations (create, verify, get, update ) against OWI
3. Password hashing using the same scheme as OWI (bcrypt)

It handles compatibility issues between passlib 1.7.4 and bcrypt 4.2.0 by suppressing specific warnings. While these warnings appear during authentication operations, they do not affect the functionality of password verification, so they can safely be ignored.

## User Role Management

The system implements role-based access control with two primary roles:

1. **admin**: Users with administrative privileges
2. **user**: Regular creator users with standard permissions

Role updates are managed through:

1. **Email-based Role Updates**: The preferred way to update user roles
   - Uses the `/admin/users/update-role-by-email` endpoint
   - Directly updates roles in the database using email as identifier
   - Eliminates the need to look up user IDs, reducing potential failure points
   - Implemented through `OwiUserManager.update_user_role_by_email()`

2. **ID-based Role Updates**: Legacy method still supported
   - Uses the `/admin/users/{user_id}/update-role` endpoint
   - Requires user ID lookup, which adds complexity

Only users with admin privileges can modify roles, and special protection prevents changing the primary admin (ID 1) role.

## Debugging and Monitoring

The system includes detailed logging for authentication processes:

1. Login/authentication attempts are logged
2. Password verification steps are tracked with detailed hash comparison logs
3. User creation operations are monitored
4. Detailed error reporting helps identify authentication issues
5. Role updates are logged for security and auditing purposes

## Creator Interface API Architecture

### API Organization

The Creator Interface API is organized as follows:

1. **Main Router** (`/backend/creator_interface/main.py`)
   - Entry point for user requests
   - Handles login/signup operations
   - Manages file operations (list, upload, delete)
   - Provides user information endpoints
   - Includes utility endpoints like the LAMB helper assistant

2. **Assistant Router** (`/backend/creator_interface/assistant_router.py`)
   - Mounted at `/creator/assistant`
   - Manages all assistant-related operations
   - Proxies requests to the LAMB Core API
   - Handles knowledge base operations

### Authentication Flow in Creator Interface

The Creator Interface implements a token-based authentication flow:

1. **Initial Authentication**:
   - User submits credentials to `/login` endpoint
   - `UserCreatorManager` forwards request to LAMB API to verify credentials
   - On success, returns a JWT token from OWI along with user info and launch URL

2. **Subsequent Requests**:
   - All protected endpoints extract the token from the Authorization header
   - The `get_creator_user_from_token` function in `assistant_router.py` validates tokens
   - This function uses `OwiUserManager.get_user_auth()` to verify the token with OWI
   - Then it checks if the user exists in the LAMB Creator users database

3. **Token Validation Process**:
   ```
   ┌────────────┐     ┌───────────────────┐     ┌─────────────┐     ┌─────────────┐
   │            │     │                   │     │             │     │             │
   │   Request  │────►│get_creator_user_  │────►│OwiUserManager│────►│ OWI System  │
   │   with     │     │from_token()       │     │get_user_auth│     │             │
   │   Token    │     │                   │     │             │     │             │
   └────────────┘     └───────────────────┘     └─────────────┘     └─────────────┘
                                  │                                         │
                                  ▼                                         │
                        ┌───────────────────┐                               │
                        │                   │                               │
                        │LambDatabaseManager│◄───────────────────────────────
                        │get_creator_user_  │
                        │by_email()         │
                        └───────────────────┘
   ```

4. **Proxy Pattern**:
   - After authentication, most endpoints in the Creator Interface act as proxies
   - They forward requests to the LAMB Core API, adding the `Authorization` header
   - Some endpoints enhance the requests with additional logic or transformations
   - This pattern isolates the frontend from changes in the core API

### Special Authentication Cases

1. **Admin Auto-Creation**:
   - The OWI admin can log in without a pre-existing creator user
   - The system detects admin credentials and automatically creates a creator user
   - This facilitates system initialization and admin operations

2. **Launch URL Generation**:
   - After login, the system generates a direct OWI launch URL
   - This URL contains a token for seamless access to OWI
   - Enables integrated navigation between LAMB and OWI interfaces

## Conclusion

Creator user management in LAMB combines a local user database with OWI's authentication system, providing a secure and integrated approach. Each creator user has a corresponding OWI user, and authentication tokens from OWI are used throughout the system. 

The dual API architecture (Creator Interface API and LAMB Core API) creates a layered design that separates user-facing concerns from core business logic. The Creator Interface acts as a proxy layer, adding user-specific logic while forwarding requests to the LAMB Core, which handles fundamental operations.

This architecture allows LAMB to leverage OWI's robust user management while adding features specific to creator users in the learning assistant context. The proxy pattern employed by the Creator Interface API provides flexibility and isolation between the frontend and the core backend systems.
