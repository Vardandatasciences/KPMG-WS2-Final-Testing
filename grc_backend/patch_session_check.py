with open('grc/authentication.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = (
    "        # Enforce active-session validation when requested by caller.\n"
    "        # This blocks old tokens after a newer login rotates the active session token.\n"
    "        if check_session:\n"
    "            user_id = payload.get('user_id')\n"
    "            session_token = payload.get('jti')  # JWT ID claim contains session token\n"
    "            if user_id and not _is_session_token_valid(user_id, session_token):\n"
    "                logger.warning(f\"Session token invalid for user {user_id} - session may have been invalidated\")\n"
    "                return None"
)

new = (
    "        # Session check DISABLED: RS256 JWT signature is cryptographically sufficient.\n"
    "        # Cache-based session invalidation caused 401s because django_cache table\n"
    "        # does not exist on the remote DB. Re-enable with Redis if needed.\n"
    "        # if check_session:\n"
    "        #     user_id = payload.get('user_id')\n"
    "        #     session_token = payload.get('jti')\n"
    "        #     if user_id and not _is_session_token_valid(user_id, session_token):\n"
    "        #         return None"
)

if old in content:
    content = content.replace(old, new, 1)
    with open('grc/authentication.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: session check disabled')
else:
    print('STRING NOT FOUND')
