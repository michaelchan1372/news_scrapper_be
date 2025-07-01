
## Users

from types import NoneType
from pydantic import BaseModel
from services.database.database import init_connection
import services.database.users.sql as sql

class User(BaseModel):
    username: str
    password: str
    email: str

def get_user_data(username):
    email = username
    user = {}
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.get_user_data, (username, email))
    row = cursor.fetchone()
    if type(row) == NoneType:
        return None
    user["hashed_password"] = row[0]
    user["username"] = row[1]
    user["is_active"] = row[2]
    user["email"] = row[3]
    user["id"] = row[4]
    user["verification_code"] = row[5]
    user["verification_expired"] = row[6]
    user["verification_failed"] = row[7]
    return user

def create_users(user: User, hash):
    try:
        conn = init_connection()
        cursor = conn.cursor()
        cursor.execute(sql.get_user_data, (user.username, user.email))
        row = cursor.fetchone()
        if type(row) != NoneType:
            return [False, -1]
        cursor.execute(sql.insert_users_to_db, (user.email, hash, user.username))
        last_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        return [True, last_id]
    except Exception as e:
        return [False, -1]

def update_verification_code(user_id, code):
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.update_verification_code, (code, user_id))
    conn.commit()
    cursor.close()
    return True

def update_user_verification_failed(failed_num, user_id):
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.update_verification_failed, (failed_num, user_id))
    conn.commit()
    cursor.close()
    return True

def update_user_verification_success(user_id):
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.update_verification_success, (user_id))
    conn.commit()
    cursor.close()
    return True