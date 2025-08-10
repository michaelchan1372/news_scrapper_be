import pymysql
import requests
from services.aws_s3 import get_presigned_url
import services.database.sql as sql
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
    conn = pymysql.connect(
        host=host,
        user=db_user,
        password=db_password,
        database=db
    )
    return conn

def create_logs(conn, region_name, keyword, k_id, r_id):
    cursor = conn.cursor()
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(sql.insert_logs_to_db, (current_datetime, region_name, keyword, k_id, r_id))   
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

def save_content_path(conn, id, content_path):
    cursor = conn.cursor()
    cursor.execute(sql.update_content_path, (content_path, id))
    last_id = cursor.lastrowid
    cursor.close()
    return last_id

def save_html_path(conn, id, html_path):
    cursor = conn.cursor()
    cursor.execute(sql.update_html_path, (html_path, id))
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

def fetch_group(uid):
    res = []
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.find_by_scrape_date, (uid))
    rows = cursor.fetchall()
    for row in rows:
        payload = {}
        payload["published_date"] = row[0]
        payload["region"] = row[1]
        payload["num"] = row[2]
        payload["keyword"] = row[3]
        payload["summary"] = row[4]
        payload["k_id"] = row[5]
        res.append(payload)
    conn.close()
    return res


def fetch_page(published_date, region, k_id, uid):
    res = []
    conn = init_connection()
    cursor = conn.cursor()
    print(published_date)
    print(region)
    cursor.execute(sql.find_page, (published_date, region, k_id, uid))
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
    conn.close()
    return res

def fetch_page_path(id):
    conn = init_connection()
    cursor = conn.cursor()
    payload = {}
    cursor.execute(sql.find_page_path, (id))
    row = cursor.fetchone()
    payload["id"] = row[0]
    payload["content_path"] = row[1]
    payload["html_path"] = row[2]
    conn.close()
    return payload

def fetch_page_paths(ids):
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.find_page_path, (ids))
    rows = cursor.fetchall()

    for row in rows:
        payload = {}
        payload["id"] = row[0]
        payload["content_path"] = row[1]
        payload["html_path"] = row[2]
        res.append(payload)
    conn.close()
    return res


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
    conn.close()
    return res

def fetch_page_text(id):
    path = fetch_page_path(id)["content_path"]
    url = get_presigned_url(path)
    response = requests.get(url)
    return response.text

def fetch_pages_text(ids):
    pages = fetch_page_paths(ids)
    res = []
    for page in pages:
        path = page["content_path"]
        url = get_presigned_url(path)
        response = requests.get(url)
        text = response.text
        res.append(text)
    return res

def fetch_pages_summary(ids):
    conn = init_connection()
    cursor = conn.cursor()
    texts = []
    cursor.execute(sql.find_page_summary, (ids))
    rows = cursor.fetchall()
    for row in rows:
        summary = row[1]
        texts.append(summary)
    return texts

def fetch_article_summary(ids):
    conn = init_connection()
    cursor = conn.cursor()
    texts = []
    cursor.execute(sql.check_summary_finished, (ids))
    row = cursor.fetchone()
    if row[0] == row[1]:
        cursor.execute(sql.check_summary_finished, (ids))
        rows = cursor.fetchall()
        for row in rows:
            texts.append(row[0])
        
    conn.close()
    return texts

def get_daily_summarize_article():
    # Find any article that does not have a summarize id
    # to combine with existing ds of same date
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.daily_news_to_summarize, ())
    rows = cursor.fetchall()
    for row in rows:
        payload = {}
        payload["publised_date"] = row[0]
        payload["ni_ids"] = row[1]
        payload["keyword"] = row[2]
        payload["region"] = row[3]
        res.append(payload)
    conn.close()
    return res

def get_summarize_article():
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.articles_to_summarize, ())
    rows = cursor.fetchall()
    for row in rows:
        payload = {}
        payload["ni_id"] = row[0]
        payload["title"] = row[1]
        payload["keyword"] = row[2]
        res.append(payload)
    conn.close()
    return res
    
def save_summary_daily(news_article_group):
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.insert_summary, (
        news_article_group["publised_date"],
        news_article_group["region"],
        news_article_group["keyword"],
        news_article_group["summary"],
        news_article_group["model_name"],
        news_article_group["input_tokens"],
        news_article_group["output_tokens"]
    ))
    last_id = cursor.lastrowid
    print("Last Id" + str(last_id))
    ni_ids = news_article_group["ni_ids"]
    ni_ids = [int(i.strip()) for i in news_article_group["ni_ids"].split(',')]
    params = (last_id, *ni_ids)
    cursor.execute(sql.update_news_item_summary(ni_ids), params)
    conn.commit()
    conn.close()

def save_summary(news_article_group):
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(sql.update_article_summary, (
        news_article_group["summary"],
        news_article_group["model_name"],
        news_article_group["input_tokens"],
        news_article_group["output_tokens"],
        news_article_group["ni_id"]
    ))

    conn.commit()
    conn.close()


def remove_news(region, published_date):
    conn = init_connection()
    cursor = conn.cursor()

    cursor.execute(sql.fetch_news_to_be_revoked, (
        region, published_date
    ))
    res = []
    rows = cursor.fetchall()
    for row in rows:
        id = row[0]
        cursor.execute(sql.revoked_news, (
            id
        ))
    conn.commit()
    conn.close()

def get_recent_summary(num_days = 5):
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.get_recent_ds, (num_days))
    rows = cursor.fetchall()
    for row in rows:
        payload = {}
        payload["published_date"] = row[0]
        payload["summary"] = row[1]
        payload["keyword"] = row[2]
        res.append(payload)
        
    conn.commit()
    conn.close()
    return res

def get_summaries_by_dates(dates):
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.get_summaries_by_dates(dates), (dates))
    rows = cursor.fetchall()
    for row in rows:
        payload = {}
        payload["published_date"] = row[0]
        payload["summary"] = row[1]
        payload["keyword"] = row[2]
        res.append(payload)
        
    conn.commit()
    conn.close()
    return res

def get_summaries_by_date_range(date_1, date_2):
    sorted_dates = sorted([date_1, date_2], key=lambda d: datetime.strptime(d, "%Y-%m-%d"))
    conn = init_connection()
    cursor = conn.cursor()
    res = []
    cursor.execute(sql.get_summaries_by_date_range, (sorted_dates[0], sorted_dates[1]))
    rows = cursor.fetchall()
    for row in rows:
        payload = {}
        payload["published_date"] = row[0]
        payload["summary"] = row[1]
        payload["keyword"] = row[2]
        res.append(payload)
        
    conn.commit()
    conn.close()
    return res


