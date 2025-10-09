import { getApiUrl } from '$lib/config';

/**
 * Get list of all assistants in the organization
 * @param {string} token - Authorization token
 * @returns {Promise<any>} - Promise resolving to assistants list
 */
export async function getOrganizationAssistants(token) {
  try {
    const response = await fetch(getApiUrl('/admin/org-admin/assistants'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch organization assistants');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching organization assistants:', error);
    throw error;
  }
}

/**
 * Get access information for a specific assistant
 * @param {string} token - Authorization token
 * @param {number} assistantId - Assistant ID
 * @returns {Promise<any>} - Promise resolving to access info
 */
export async function getAssistantAccess(token, assistantId) {
  try {
    const response = await fetch(getApiUrl(`/admin/org-admin/assistants/${assistantId}/access`), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch assistant access info');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching assistant access:', error);
    throw error;
  }
}

/**
 * Update assistant access for users
 * @param {string} token - Authorization token
 * @param {number} assistantId - Assistant ID
 * @param {string[]} userEmails - Array of user emails
 * @param {string} action - 'grant' or 'revoke'
 * @returns {Promise<any>} - Promise resolving to update result
 */
export async function updateAssistantAccess(token, assistantId, userEmails, action) {
  try {
    const response = await fetch(getApiUrl(`/admin/org-admin/assistants/${assistantId}/access`), {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_emails: userEmails,
        action: action
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update assistant access');
    }

    return await response.json();
  } catch (error) {
    console.error('Error updating assistant access:', error);
    throw error;
  }
}

