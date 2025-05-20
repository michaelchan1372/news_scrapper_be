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

find_by_scrape_date = """
    select DATE(ni.published) published_date, sl.region, count(*) num, GROUP_CONCAT(distinct sl.key_word) 
    from news_items ni 
    join scrape_logs sl on sl.id = ni.sl_id 
    GROUP BY DATE(ni.published), sl.region 
    ORDER BY published_date desc
"""

find_page = """
    select ni.id
    , ni.title
    , ni.link
    , ni.published
    , ni.description
    , ni.sl_id
    , ni.content_path
    , ni.html_path
    , sl.scrape_date 
    , sl.key_word 
    from news_items ni 
    join scrape_logs sl 
        on ni.sl_id = sl.id
    where  DATE(ni.published) = %s
        and sl.region = %s  
    ORDER BY published desc
"""

find_page_path = """
    select id, content_path, html_path
    from news_items ni 
    where ni .id = %s
"""