insert_news_items_to_db = """
    INSERT INTO news_items (`title`,`link`,`published`,`description`, `sl_id`)
    VALUES (%s, %s, %s, %s, %s)
"""

insert_logs_to_db = """
    INSERT INTO scrape_logs (`scrape_date`, region, key_word)
    VALUES (%s, %s, %s)
"""

select_log_id = """
    SELECT `id` from `scrape_logs` WHERE `scrape_date` = %s
"""

update_path = """
    UPDATE news_items 
    SET content_path = %s,
    html_path = %s
    WHERE id = %s
"""

find_history = """
    SELECT title, link FROM news_items;
"""