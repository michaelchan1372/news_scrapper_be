## Navigations

from services.database.database import init_connection
import services.database.navigation.sql as sql

def get_all_path():
    # Find any article that does not have a summarize id
    # to combine with existing ds of same date
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.get_all_path, ())
    rows = cursor.fetchall()
    res = [
        {
            "id": row[0],
            "path": row[1],
            "is_active": row[2],
            "is_dashboard": row[3],
        }
        for row in rows
    ]
    conn.close()
    return res