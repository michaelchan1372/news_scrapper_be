get_all_keywords = """
    select k.keyword, r.name, r.code 
    from keyword_user_region kur 
    join keyword_user ku 
        on kur.ku_id = ku.id 
    join regions r 
        on r.id = kur.region_id 
    join keywords k 
        on ku.keyword_id = k.id
    where kur.is_active = 1
        and kur.is_revoked = 0
        and ku.is_revoked = 0
    group by k.keyword , r.name 
"""

get_keyword_by_uid = """
    select k.keyword, r.name, r.code, kur.id
    from keyword_user_region kur 
    join keyword_user ku 
        on kur.ku_id = ku.id 
    join regions r 
        on r.id = kur.region_id 
    join keywords k 
        on ku.keyword_id = k.id
    where kur.is_active = 1
        and kur.is_revoked = 0
        and ku.is_revoked = 0
        and ku.user_id = %s
"""

available_regions = """
    select r.id
    , r.name
    , r.code 
    from regions r 
"""

get_keyword_id = """
    select id 
    from keywords
    where keyword = %s
"""

create_keyword = """
    INSERT INTO keywords (keyword)
        VALUES (%s);
"""

create_keyword_user = """
    INSERT INTO keyword_user (keyword_id,user_id,is_revoked)
	VALUES (%s,%s,0);
"""

get_keyword_user = """
    SELECT id from keyword_user
    WHERE keyword_id = %s
        AND user_id = %s
"""

get_kur_id = """
    select kur.id
    from keyword_user_region kur 
    join keyword_user ku 
        on kur.ku_id = ku.id 
    join regions r 
        on r.id = kur.region_id 
    join keywords k 
        on ku.keyword_id = k.id
    where kur.is_revoked = 0
        and ku.is_revoked = 0
        and k.id = %s
        and ku.user_id = %s
"""

set_kur_active = """
    UPDATE keyword_user_region
    SET is_active = 1
    WHERE id = %s
"""

create_kur = """
    INSERT INTO scrapper.keyword_user_region (ku_id,is_revoked,is_active,region_id)
        VALUES (%s,0,1,%s);
"""

set_kur_inactive = """
    UPDATE keyword_user_region
    SET is_active = 0
    WHERE id = %s
"""