    This folder will contain the code to access and modify the owi native tables from the lamb backend.
    Tables used

    -- 
    CREATE TABLE "user" (
        "id" VARCHAR(255) NOT NULL,
        "name" VARCHAR(255) NOT NULL,
        "email" VARCHAR(255) NOT NULL,
        "role" VARCHAR(255) NOT NULL,
        "profile_image_url" TEXT NOT NULL NOT NULL,
        "api_key" VARCHAR(255),
        "created_at" INTEGER NOT NULL NOT NULL,
        "updated_at" INTEGER NOT NULL NOT NULL,
        "last_active_at" INTEGER NOT NULL NOT NULL,
        "settings" TEXT,
        "info" TEXT,
        "oauth_sub" TEXT
    );

    CREATE UNIQUE INDEX "user_api_key" ON "user" ("api_key");
    CREATE UNIQUE INDEX "user_id" ON "user" ("id");
    CREATE UNIQUE INDEX "user_oauth_sub" ON "user" ("oauth_sub");

    CREATE TABLE "auth" (
        "id" VARCHAR(255) NOT NULL,
        "email" VARCHAR(255) NOT NULL, 
        "password" TEXT NOT NULL NOT NULL,
        "active" INTEGER NOT NULL
    );

    CREATE UNIQUE INDEX "auth_id" ON "auth" ("id");


    CREATE TABLE "group" (
        id TEXT NOT NULL,   
        user_id TEXT, 
        name TEXT, 
        description TEXT, 
        data JSON, 
        meta JSON, 
        permissions JSON, 
        user_ids JSON, 
        created_at BIGINT, 
        updated_at BIGINT, 
        PRIMARY KEY (id), 
        UNIQUE (id)
    );
    ->  user_id -> user.id OWNER 
    ->  user_ids -> array of user_id 

{"read": {"group_ids": [], "user_ids": []}, "write": {"group_ids": [], "user_ids": []}}


test endpoints:
# create user
curl -X POST http://localhost:9099/lamb/v1/OWI/users \
-H 'Authorization: Bearer 0p3n-w3bu!' \
-H 'Content-Type: application/json' \
-d '{"name": "User 1", "email": "user-1@example.com", "password": "secure_password"}'

TODO -> test 

# Verify user
curl -X POST http://localhost:9099/lamb/v1/OWI/users/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "user-1@example.com", "password": "secure_password"}'

# Update password
curl -X PUT http://localhost:9099/lamb/v1/OWI/users/some-uuid/password \
  -H "Content-Type: application/json" \
  -d '{"new_password": "new_secure_password"}'

# Deactivate user
curl -X DELETE http://localhost:8000/owi/users/some-uuid

# groups
TODO -> test  
# Create a group
curl -X POST http://localhost:9099/lamb/v1/OWI/groups \
-H "Authorization: Bearer 0p3n-w3bu!" \
-H "Content-Type: application/json" \
-d '{
  "name": "Test Group",
  "user_id": "owner_user_id",
  "description": "A test group",
  "permissions": {"read": true, "write": true},
  "user_ids": ["user1", "user2"]
}'

# Get a group
curl -X GET http://localhost:9099/lamb/v1/OWI/groups/some-group-id \
-H "Authorization: Bearer 0p3n-w3bu!"

# Get user's groups
curl -X GET http://localhost:9099/lamb/v1/OWI/groups/user/some-user-id \
-H "Authorization: Bearer 0p3n-w3bu!"

# Update a group
curl -X PUT http://localhost:9099/lamb/v1/OWI/groups/some-group-id \
-H "Authorization: Bearer 0p3n-w3bu!" \
-H "Content-Type: application/json" \
-d '{
  "name": "Updated Group Name",
  "permissions": {"read": true, "write": false}
}'

# Add user to group
curl -X PUT http://localhost:9099/lamb/v1/OWI/groups/some-group-id/users/new-user-id \
-H "Authorization: Bearer 0p3n-w3bu!"

# Remove user from group
curl -X DELETE http://localhost:9099/lamb/v1/OWI/groups/some-group-id/users/old-user-id \
-H "Authorization: Bearer 0p3n-w3bu!"

CREATE TABLE LAMB_assistant_publish (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        assistant_id INTEGER NOT NULL,
                        assistant_name TEXT NOT NULL,
                        assistant_owner TEXT NOT NULL,
                        group_id TEXT NOT NULL,
                        group_name TEXT NOT NULL,
                        oauth_consumer_name TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        UNIQUE(assistant_id, group_id)
                    )
