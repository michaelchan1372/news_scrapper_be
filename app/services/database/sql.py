insert_news_items_to_db = """
    INSERT INTO news_items (`title`,`link`,`published`,`description`, `sl_id`, `source`)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

insert_logs_to_db = """
    INSERT INTO scrape_logs (`scrape_date`, region, keyword, k_id, r_id)
    VALUES (%s, %s, %s, %s, %s)
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
    , sl.keyword keyword
    , GROUP_CONCAT(distinct ds.summary) summary
    , k.id k_id
    from news_items ni 
    join scrape_logs sl 
        on sl.id = ni.sl_id
    join keywords k 
    	on k.id = sl.k_id
	join keyword_user ku 
        on ku.keyword_id = k.id
        and ku.user_id = %s
    join keyword_user_region kur 
    	on kur.ku_id = ku.id 
    	and kur.is_active = 1
	join regions r 
		on r.id = kur.region_id 
		and r.id = sl.r_id 
    left join daily_summary ds 
        on ni.ds_id = ds.id
        and ds.is_revoked = 0
    where ni.is_revoked = 0
        and ni.is_hidden = 0
    GROUP BY DATE(ni.published), sl.r_id, k.id
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
    join keywords k 
    	on k.id = sl.k_id 
	join keyword_user ku 
		on ku.keyword_id = k.id 
    where  DATE(ni.published) = %s
        and sl.region = %s
        and ni.is_hidden = 0
        and ni.is_revoked = 0
        and k.id = %s
        and ku.user_id = %s
    ORDER BY published desc
"""

find_page_path = """
    select id, content_path, html_path
    from news_items ni 
    where ni .id in (%s)
"""

find_page_summary = """
    select id, summary
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
    join keywords k 
        on k.id = sl.k_id
    join keyword_user ku 
        on ku.keyword_id = k.id
   	join keyword_user_region kur 
   	    on kur.ku_id = ku.id 
   	    and kur.is_active = 1
    where sl.region = %s
    and (ni.content_path is null or ni.html_path is null)
    and ni.is_revoked = 0
"""

daily_news_to_summarize = """
    SELECT t.*, ds.id FROM
    (
        SELECT DATE(ni.published) AS publised_date, GROUP_CONCAT(DISTINCT ni.id) ni_ids, sl.keyword, sl.region, SUM(CASE WHEN ni.ds_id IS NULL THEN 1 ELSE 0 END) AS has_new
        FROM news_items ni
        join scrape_logs sl 
        on ni.sl_id = sl.id
        join keywords k 
        on k.id = sl.k_id
        join keyword_user ku 
            on ku.keyword_id = k.id
        join keyword_user_region kur 
            on kur.ku_id = ku.id 
            and kur.is_active = 1
        WHERE ni.is_revoked = 0
        GROUP BY publised_date, sl.region , sl.k_id 
        ORDER BY publised_date
    ) t
    left join  daily_summary ds 
    on ds.published = t.publised_date
    and t.keyword = ds.keyword 
    and t.region = ds.region 
    and ds.is_revoked = 0
    where ds.id is null or t.has_new > 0;
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

update_article_summary = """
    UPDATE news_items
    SET summary = %s,
    model_name = %s,
    input_tokens = %s,
    output_tokens = %s,
    is_summary_revoked = 0
    WHERE id = %s

"""

def update_news_item_summary(ni_ids):
    format_strings = ','.join(['%s'] * len(ni_ids))
    return f"""
        UPDATE news_items 
        SET ds_id = %s
        WHERE id in ({format_strings})
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

articles_to_summarize = """
    SELECT ni.id
    , ni.title
    , sl.keyword
    FROM news_items ni
    join scrape_logs sl 
        on sl.id = ni.sl_id 
    join keywords k 
        on k.id = sl.k_id 
    join keyword_user ku 
        on ku.keyword_id = k.id
   	join keyword_user_region kur 
   	    on kur.ku_id = ku.id 
   	    and kur.is_active = 1
    where ni.summary is null 
        or is_summary_revoked = 1
    group by ni.id
"""

fetch_article_summary = """
   select summary
   from news_items ni
   where id in (%s)
"""

check_summary_finished = """
    select COUNT(CASE WHEN summary IS NOT NULL THEN 1 END) AS not_null_count
   , COUNT(*) item_count
   from news_items ni
   where id in (%s)
"""

get_recent_ds = """
       select ds.published, ds.summary, ds.keyword from daily_summary ds 
        join news_items ni 
        on ni.ds_id = ds.id 
        WHERE ds.published >= DATE_SUB(CURDATE(), INTERVAL 5 DAY)
        order by ds.keyword, ds.published DESC 
"""

def get_summaries_by_dates(dates):
    format_strings = ','.join(['%s'] * len(dates))
    return f"""
        select ds.published, ds.summary, ds.keyword from daily_summary ds 
        join news_items ni 
        on ni.ds_id = ds.id 
        WHERE  CAST(ds.published AS DATE) in ({format_strings})
        order by ds.keyword, ds.published DESC 
    """

get_summaries_by_date_range = """
        select ds.published, ds.summary, ds.keyword from daily_summary ds 
        join news_items ni 
        on ni.ds_id = ds.id 
        WHERE ds.published >= %s
        and ds.published  <= %s
        order by ds.keyword, ds.published DESC 
    """

get_user_data = """
    select hash
    , username
    , is_active
    , email
    , id
    , verification_code
    , verification_expired
    , verification_failed
      from users
    where username = %s 
    or email = %s
"""

insert_users_to_db = """
    INSERT INTO scrapper.users (email,hash,username)
	VALUES (%s,%s,%s);
"""

update_verification_code = """
    UPDATE users 
    SET verification_code = %s,
    verification_expired = (NOW() + INTERVAL 5 DAY)
    WHERE id = %s
"""

update_verification_failed = """
    UPDATE users 
    SET verification_failed = %s
    WHERE id = %s
"""

update_verification_success = """
    UPDATE users 
    SET is_active = 1
    WHERE id = %s
"""

get_user_latest_scrape_date = """
    select max(sl.scrape_date)
    from news_items ni 
    join scrape_logs sl 
        on sl.id = ni.sl_id
    join keywords k 
    	on k.id = sl.k_id
	join keyword_user ku 
        on ku.keyword_id = k.id
        and ku.user_id = %s
    join keyword_user_region kur 
    	on kur.ku_id = ku.id 
    	and kur.is_active = 1
	join regions r 
		on r.id = kur.region_id 
		and r.id = sl.r_id 
    left join daily_summary ds 
        on ni.ds_id = ds.id
        and ds.is_revoked = 0
    where ni.is_revoked = 0
        and ni.is_hidden = 0
    limit 1
"""