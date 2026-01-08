# User session management for login flow
user_sessions = {}
api_sessions = {}  # Store API clients for logged-in users

def set_user_state(user_id, state, data=None):
    """Set user's current state"""
    user_sessions[user_id] = {
        'state': state,
        'data': data or {}
    }

def get_user_state(user_id):
    """Get user's current state"""
    return user_sessions.get(user_id, {'state': None, 'data': {}})

def clear_user_state(user_id):
    """Clear user's state"""
    if user_id in user_sessions:
        del user_sessions[user_id]

def update_user_data(user_id, key, value):
    """Update user session data"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {'state': None, 'data': {}}
    user_sessions[user_id]['data'][key] = value

def set_api_session(user_id, app_id, api_client):
    """Store API client for user"""
    if user_id not in api_sessions:
        api_sessions[user_id] = {}
    api_sessions[user_id][app_id] = api_client

def get_api_session(user_id, app_id):
    """Get stored API client"""
    if user_id in api_sessions:
        return api_sessions[user_id].get(app_id)
    return None

def clear_api_session(user_id, app_id=None):
    """Clear API session"""
    if user_id in api_sessions:
        if app_id:
            if app_id in api_sessions[user_id]:
                del api_sessions[user_id][app_id]
        else:
            del api_sessions[user_id]
