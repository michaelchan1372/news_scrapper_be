
get_user_data = """
    select hash
    , username
    , is_active
    , email
    , id
    , verification_code
    , verification_expired
    , verification_failed
      from users
    where username = %s 
    or email = %s
"""

insert_users_to_db = """
    INSERT INTO scrapper.users (email,hash,username)
	VALUES (%s,%s,%s);
"""

update_verification_code = """
    UPDATE users 
    SET verification_code = %s,
    verification_expired = (NOW() + INTERVAL 5 DAY)
    WHERE id = %s
"""

update_verification_failed = """
    UPDATE users 
    SET verification_failed = %s
    WHERE id = %s
"""

update_verification_success = """
    UPDATE users 
    SET is_active = 1
    WHERE id = %s
"""
