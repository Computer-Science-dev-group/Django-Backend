# SQL Query to retrieve post to display on users feed
USER_FEED_QUERY = """
    SELECT mp.id as id
    FROM messaging_post mp
    INNER JOIN cluster_cluster cc
    ON	(
        cc.id = mp.cluster_id and cc.id::text IN (
            SELECT gu.object_pk
            FROM auth_permission ap
            INNER JOIN guardian_userobjectpermission gu ON (
                gu.content_type_id=ap.content_type_id
                AND gu.permission_id=ap.id
                AND gu.user_id=%s
            ) WHERE ap.codename=%s )
        )
    LIMIT %s
"""
