from datetime import datetime
from time import sleep
import time
import feedparser
import urllib.parse
import services.database as database
import services.file_write as file_write
import services.selenium_runner as selenium_runner
import services.database as database

excluded_titel = ["Shopping", "Maps"]
csv_titles = ['id','title', 'link', 'published', 'description']
regions = [
    {"name": "china","code": "hl=zh-CN&gl=CN&ceid=CN:zh"}, 
    {"name": "hong kong", "code": "hl=zh-HK&gl=HK&ceid=HK:zh-Hant"}
]

def get_news_links(keyword, max_results, region, region_name):
    conn = database.init_connection()
    log_id = database.create_logs(conn, region_name, keyword)
    (titles, links) = database.scrape_history(conn)
    encoded_keyword = urllib.parse.quote_plus(keyword)

    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&{region}"
    
    feed = feedparser.parse(rss_url)
    news = []
    
    for idx, entry in enumerate(feed.entries[:max_results], start=1):
        if  entry.title not in titles and entry.link not in links:
            object = {
                'title': entry.title, 
                'link': entry.link,
                'published': database.convert_to_db_date(entry.published) if 'published' in entry else None,
                'description': entry.description,
            }
            
            last_id = database.create_new_items(conn, object, log_id)
            object['id'] = last_id
            news.append(object)

    conn.commit()
    
    conn.close()
    folder_created = file_write.create_folder_if_not_exist(f'./output/{region_name}')
    if folder_created:
        file_write.save_to_csv(news, f'./output/{region_name}/news_articles.csv', csv_titles)
    else:
        file_write.save_to_csv(news, f'./output/{region_name}/news_articles.csv', csv_titles, True)
    return news


def scrape_content(news_items, name, keyword):
    conn = database.init_connection()
    driver = selenium_runner.init_driver()
    for news_item in news_items:
        selenium_runner.scrape_article(driver, news_item, conn, name, keyword)
        
        time.sleep(2)
        
    conn.close()
    driver.quit()

