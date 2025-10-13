# User Deletion Feature - Testing Guide

## Prerequisites
- Organization admin account with access to the org-admin panel
- At least one test user in your organization (besides yourself)
- Backend server running
- Frontend accessible at http://localhost:5173

## Test Scenarios

### Test 1: Successful User Deletion
**Steps:**
1. Log in as an organization admin
2. Navigate to http://localhost:5173/org-admin?view=users
3. Locate a test user in the users table
4. Click the red trash icon in the Actions column
5. Click "OK" on the first confirmation dialog
6. Click "OK" on the second confirmation dialog

**Expected Result:**
- Alert shows: "User [name] has been permanently deleted."
- User is removed from the table immediately
- User cannot log in anymore

### Test 2: Self-Deletion Prevention
**Steps:**
1. Log in as an organization admin
2. Navigate to http://localhost:5173/org-admin?view=users
3. Find your own user account in the table
4. Try to click the delete icon

**Expected Result:**
- Delete icon is grayed out/disabled
- Tooltip shows: "You cannot delete your own account"
- If clicked, alert shows: "You cannot delete your own account. Please ask another administrator to delete your account if needed."

### Test 3: Admin Role Protection
**Steps:**
1. Log in as an organization admin
2. Try to delete another admin or organization owner

**Expected Result:**
- API returns 403 error
- Alert shows: "Cannot delete an organization admin or owner. Please remove their admin privileges first."

### Test 4: Cancel Deletion
**Steps:**
1. Navigate to the users table
2. Click the delete icon for a user
3. Click "Cancel" on the confirmation dialog

**Expected Result:**
- No deletion occurs
- User remains in the table

### Test 5: API Direct Test
**Test with curl:**
```bash
# Replace with actual user ID and token
USER_ID=123
TOKEN="your_admin_token_here"

curl -X DELETE "http://localhost:8000/creator/admin/org-admin/users/${USER_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -v
```

**Expected Response:**
```json
{
  "message": "User user@example.com has been permanently deleted"
}
```

### Test 6: Cross-Organization Protection
**Steps:**
1. Log in as admin of Organization A
2. Try to delete a user from Organization B (via API or by manipulating the URL)

**Expected Result:**
- API returns 404 error
- Alert shows: "User not found in this organization"

## Verification Checklist

- [ ] Delete button appears in the Actions column
- [ ] Delete button is disabled for your own account
- [ ] First confirmation dialog appears when clicking delete
- [ ] Second confirmation dialog appears after first confirmation
- [ ] User is removed from the table after successful deletion
- [ ] Success message is displayed
- [ ] Deleted user cannot log in
- [ ] Cannot delete yourself
- [ ] Cannot delete organization admins/owners
- [ ] Cannot delete users from other organizations
- [ ] Error messages are clear and helpful

## Database Verification

After deletion, verify in the database:

```sql
-- Check if user is removed from auth table
SELECT * FROM auth WHERE email = 'deleted_user@example.com';
-- Should return no rows

-- Check if user is removed from user table
SELECT * FROM user WHERE email = 'deleted_user@example.com';
-- Should return no rows
```

## Rollback/Undo

**Important:** There is no undo functionality. Once a user is deleted:
- They are permanently removed from the authentication system
- They cannot log in
- A new user can be created with the same email address if needed

## Known Limitations

1. User data (assistants, chats, etc.) may remain in the system as orphaned records
2. No soft delete - deletion is immediate and permanent
3. No audit trail of who deleted whom (only in application logs)
4. No bulk deletion functionality

## Troubleshooting

### Issue: Delete button not appearing
**Solution:** 
- Clear browser cache and refresh
- Verify you're logged in as an organization admin
- Check browser console for JavaScript errors

### Issue: "Failed to delete user" error
**Solution:**
- Check backend logs for detailed error message
- Verify user exists in the database
- Ensure OWI database is accessible
- Check user is not admin/owner

### Issue: User still appears in table after deletion
**Solution:**
- Refresh the page manually
- Check network tab for failed API call
- Verify backend returned success response

## Logs to Monitor

Backend logs will show:
```
INFO:lamb.owi_bridge.owi_users:User user@example.com has been deleted successfully
INFO:creator_interface.organization_router:Organization admin admin@example.com deleted user user@example.com from organization 1
```

## Security Considerations

- All deletion operations are logged
- Requires organization admin privileges
- Cannot be performed by regular users
- Self-deletion is prevented
- Admin/owner deletion requires privilege removal first
- Cross-organization deletion is prevented

## Performance Notes

- Deletion is immediate (synchronous operation)
- No impact on other users
- Database operations are transactional
- Failed deletions are rolled back automatically
