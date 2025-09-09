```
# Create a new group
group = group_manager.create_group(
    name="Test Group",
    user_id="owner_user_id",
    description="A test group",
    permissions={"read": True, "write": True},
    user_ids=["user1", "user2"]
)

# Get group by ID
group = group_manager.get_group_by_id("group_id")

# Update group
updated_group = group_manager.update_group(
    group_id="group_id",
    name="New Name",
    permissions={"read": True, "write": False}
)

# Add/remove users
group_manager.add_user_to_group("group_id", "new_user_id")
group_manager.remove_user_from_group("group_id", "old_user_id")

# Get user's groups
user_groups = group_manager.get_user_groups("user_id")

# Delete group
success = group_manager.delete_group("group_id")