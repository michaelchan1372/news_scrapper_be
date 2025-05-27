insert_news_items_to_db = """
    INSERT INTO news_items (`title`,`link`,`published`,`description`, `sl_id`, `source`)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

insert_logs_to_db = """
    INSERT INTO scrape_logs (`scrape_date`, region, keyword)
    VALUES (%s, %s, %s)
"""

select_log_id = """
    SELECT `id` from `scrape_logs` WHERE `scrape_date` = %s
"""

update_content_path = """
    UPDATE news_items 
    SET content_path = %s
    WHERE id = %s
"""

update_html_path = """
    UPDATE news_items 
    SET html_path = %s
    WHERE id = %s
"""

find_history = """
    SELECT title, link FROM news_items;
"""

find_by_scrape_date = """
    select DATE(ni.published) published_date
    , sl.region, count(*) num
    , GROUP_CONCAT(distinct sl.keyword) keywords
    , GROUP_CONCAT(distinct ds.summary) summary
    from news_items ni 
    join scrape_logs sl on sl.id = ni.sl_id 
    left join daily_summary ds 
    on ni.ds_id = ds.id
    and ds.is_revoked = 0
    where ni.is_revoked = 0
    and ni.is_hidden = 0
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
    , sl.keyword 
    , ni.source
    from news_items ni 
    join scrape_logs sl 
        on ni.sl_id = sl.id
    where  DATE(ni.published) = %s
        and sl.region = %s  
        and ni.is_hidden = 0
        and ni.is_revoked = 0
    ORDER BY published desc
"""

find_page_path = """
    select id, content_path, html_path
    from news_items ni 
    where ni .id in (%s)
"""

news_items_to_scrape = """
    select ni.id
    , ni.title
    , ni.link
    , ni.published
    , ni.scrape_date
    , ni.description
    , ni.sl_id
    , ni.content_path
    , ni.html_path
    , ni.source
    from news_items ni 
    join scrape_logs sl 
    on ni.sl_id = sl.id 
    where sl.region = %s
    and (ni.content_path is null or ni.html_path is null)

"""

news_to_summarize = """
    SELECT t.*, ds.id FROM
    (
        SELECT DATE(ni.published) AS publised_date, GROUP_CONCAT(DISTINCT ni.id) ni_ids, sl.keyword, sl.region 
        FROM news_items ni
        join scrape_logs sl 
        on ni.sl_id = sl.id
        GROUP BY publised_date, sl.region , sl.keyword 
        ORDER BY publised_date
    ) t
    left join  daily_summary ds 
    on ds.published = t.publised_date
    and t.keyword = ds.keyword 
    and t.region = ds.region 
    and ds.is_revoked = 0
    where ds.id is null;
"""

update_content_path = """
    UPDATE news_items 
    SET content_path = %s
    WHERE id = %s
"""

insert_summary = """
    INSERT INTO daily_summary (`published`,`region`,`keyword`,`summary`, `model_name`, `input_tokens`, `output_tokens`)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

update_news_item_summary = """
    UPDATE news_items 
    SET ds_id = %s
    WHERE id in (%s)
"""

fetch_news_to_be_revoked = """
    select * from news_items ni
    join scrape_logs sl 
    on ni.sl_id = sl.id 
    where sl.region = %s
    and DATE(ni.published) = %s
"""

revoked_news = """
    UPDATE news_items ni
    SET is_revoked = 1
    WHERE id = %s
"""