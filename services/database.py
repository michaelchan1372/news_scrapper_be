import pymysql
import services.sql as sql
from datetime import datetime
import os

db_user=os.environ['db_user']
db_password=os.environ['db_password']

def convert_to_db_date(date_str):
    dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
    formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
    return formatted

def init_connection():
    # Connect to MySQL
    conn = pymysql.connect(
        host="localhost",
        user="anthony",
        password="D8f@2pL!vTz9#XeQ",
        database="scrapper"
    )
    return conn

def create_logs(conn, region_name, keyword):
    cursor = conn.cursor()
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(sql.insert_logs_to_db, (current_datetime, region_name, keyword))   
    conn.commit()

    cursor.execute(sql.select_log_id, (current_datetime))   
    result = cursor.fetchone()
    res_id = result[0]
    cursor.close()
    return res_id

def create_new_items(conn, object, log_id):
    cursor = conn.cursor()
    cursor.execute(sql.insert_news_items_to_db, (object['title'], object['link'], object['published'], object['description'], log_id))
    last_id = cursor.lastrowid
    cursor.close()
    return last_id

def save_path(conn, id, content_path, html_path):
    cursor = conn.cursor()
    cursor.execute(sql.update_path, (content_path, html_path, id))
    last_id = cursor.lastrowid
    cursor.close()
    return last_id

def scrape_history(conn):
    titles = []
    links = []
    cursor = conn.cursor()
    cursor.execute(sql.find_history)
    row = cursor.fetchone()
    while row is not None:
        titles.append(row[0])
        links.append(row[1])
        row = cursor.fetchone()
    
    cursor.close()
    return (titles, links)
