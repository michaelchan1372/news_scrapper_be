# Keywords

from services.database.database import init_connection
import services.database.keywords.sql as sql

def get_all_keywords():
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.get_all_keywords, ())
    rows = cursor.fetchall()
    res = [
        {
            "keyword": row[0],
            "name": row[1],
            "code": row[2],
            "k_id": row[3],
            "r_id": row[4]
        }
        for row in rows
    ]
    conn.close()
    return res

def get_user_keywords(uid):
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.get_keyword_by_uid, (uid))
    rows = cursor.fetchall()
    res = [
        {
            "keyword": row[0],
            "name": row[1],
            "code": row[2],
            "kur_id": row[3]
        }
        for row in rows
    ]
    conn.close()
    return res

def get_available_regions():
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.available_regions, ())
    rows = cursor.fetchall()
    res = [
        {
            "id": row[0],
            "name": row[1],
            "code": row[2]
        }
        for row in rows
    ]
    conn.close()
    return res

def add_keyword(keyword, uid):
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.get_keyword_id, (keyword))
    rows = cursor.fetchall()
    if len(rows) == 0:
        id = create_keyword(keyword, conn)
    else:
        id = row[0]

    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.get_keyword_user, (id, uid))
    row = cursor.fetchone()
    if row != None:
        return (row[0], id)
    cursor.execute(sql.create_keyword_user, (id, uid))
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return (last_id, id)

def create_keyword(keyword, conn):
    cursor = conn.cursor()
    cursor.execute(sql.create_keyword, (keyword))
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

def add_region_to_keyword(keyword, uid, region_id):
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.get_keyword_id, (keyword))
    row = cursor.fetchone()
    id = row[0]
    cursor.execute(sql.get_kur_id_with_region, (id, uid, region_id))
    row = cursor.fetchone()
    if row != None:
        kur_id = row[0]
        cursor.execute(sql.set_kur_active, (kur_id))
        last_id = kur_id
    else:
        cursor.execute(sql.get_keyword_user, (id, uid))
        row = cursor.fetchone()
        ku_id = row[0]
        cursor.execute(sql.create_kur, (ku_id, str(region_id)))
        last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id


def remove_region_from_keyword(keyword, uid, region_id):
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.get_keyword_id, (keyword))
    row = cursor.fetchone()
    id = row[0]
    cursor.execute(sql.get_kur_id_with_region, (id, uid, region_id))
    row = cursor.fetchone()
    if row != None:
        kur_id = row[0]
        cursor.execute(sql.set_kur_inactive, (kur_id))
    else:
        return False
    conn.commit()
    conn.close()
    return True