import pymysql
import services.sql as sql
from datetime import datetime
import os

db_user=os.environ['db_user']
db_password=os.environ['db_password']
host=os.environ['db_host']
db=os.environ['database']
mode=os.environ['mode']
if mode == 'remote':
    print("Conneting to remote db")
    db_user=os.environ['db_user_remote']
    db_password=os.environ['db_password_remote']
    host=os.environ['db_host_remote']
    db=os.environ['database_remote']

def convert_to_db_date(date_str):
    dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
    formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
    return formatted

def init_connection():
    # Connect to MySQL
    print("Connecting to " + host)
    conn = pymysql.connect(
        host=host,
        user=db_user,
        password=db_password,
        database=db
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
    cursor.execute(sql.insert_news_items_to_db, (object['title'], object['link'], object['published'], object['description'], log_id, object['source']))
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

def fetch_group():
    res = []
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.find_by_scrape_date)
    rows = cursor.fetchall()
    for row in rows:
        payload = {}
        payload["published_date"] = row[0]
        payload["region"] = row[1]
        payload["num"] = row[2]
        payload["keywords"] = row[3]
        res.append(payload)

    return res


def fetch_page(published_date, region):
    res = []
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.find_page, (published_date, region))
    rows = cursor.fetchall()
    for row in rows:
        payload = {}
        payload["id"] = row[0]
        payload["title"] = row[1]
        payload["link"] = row[2]
        payload["published"] = row[3]
        payload["description"] = row[4]
        payload["sl_id"] = row[5]
        payload["content_path"] = row[6]
        payload["html_path"] = row[7]
        payload["scrape_date"] = row[8]
        payload["keyword"] = row[9]
        payload["source"] = row[10]
        res.append(payload)

    return res

def fetch_page_paths(id):
    conn = init_connection()
    cursor = conn.cursor()
    payload = {}
    cursor.execute(sql.find_page_path, (id))
    row = cursor.fetchone()
    payload["id"] = row[0]
    payload["content_path"] = row[1]
    payload["html_path"] = row[2]
    return payload

def news_items_to_scape(region_name):
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.news_items_to_scrape, (region_name))
    rows = cursor.fetchall()
    for row in rows:
        payload = {}
        payload["id"] = row[0]
        payload["title"] = row[1]
        payload["link"] = row[2]
        payload["published"] = row[3]
        payload["scrape_date"] = row[4]
        payload["description"] = row[5]
        payload["sl_id"] = row[6]
        payload["content_path"] = row[7]
        payload["html_path"] = row[8]
        payload["source"] = row[9]
        res.append(payload)

    return res

