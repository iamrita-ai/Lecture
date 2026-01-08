# User session management for login flow
user_sessions = {}

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
