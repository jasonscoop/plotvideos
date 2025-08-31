# 🎥 Short Video Pipeline Doc: RapidAPI + yt-dlp + Redis + Celery

## Overview

Automated pipeline to:

- Fetch videos via RapidAPI
- Download with yt-dlp
- Remove start ad clip and recognize watermarker
- Generate subtitles with azure api
- Translate title and subtitles
- Publish to MediaCMS

# Hosts

- https://www.hostinger.com/pricing?content=vps-hosting
- https://www.kamatera.com/pricing/
- https://contabo.com/en/vps/cloud-vps-10/?image=ubuntu.332&qty=1&contract=12&storage-type=cloud-vps-10-150-gb-ssd

# Translators

- https://rapidapi.com/IRCTCAPI/api/google-translator9
- https://rapidapi.com/robust-api-robust-api-default/api/google-translate113

# Errors

## Add public access

```sql
CREATE POLICY "Allow public access"
    ON "public"."videos"
    FOR SELECT
    TO anon
    USING (
        (status = 'published'::videostatus)
        );
```

Run with docker

```bash
docker build . -t wuse
```

## Migration: BunnyCDN to B2

Migrate video embeds from BunnyCDN iframes to direct video tags with B2 URLs.

hopevideos
toovideos
weekvideos
flatvideos
muchvideos

```bash
docker build . -t wuse


docker run --rm --network container:dockerpress-mysql-1 \
  -e MYSQL_PWD=12345678 \
  mysql:8.0.36 \
  mysqldump -h 127.0.0.1 -u root weekvideos > weekvideos.sql

docker run --rm \
  --network container:dockerpress-mysql-1  \
  -e MYSQL_DB_HOST=127.0.0.1 \
  -e MYSQL_DB_USER=root \
  -e MYSQL_DB_PASSWORD=12345678 \
  -e MYSQL_DB_NAME=muchvideos \
  -e MYSQL_TABLE_PREFIX=wp_ \
  -v ./works:/workspace/works \
  wuse bash -c "pip install pymysql && python scripts/python/migrate_bunny_to_b2.py"


docker run --rm --network container:dockerpress-mysql-1 \
  -e MYSQL_PWD=12345678 \
  mysql:8.0.36 \
  mysql -h 127.0.0.1 -u root -p12345678 -e "USE toovideos; UPDATE wp_postmeta SET meta_value = REPLACE(meta_value, '/thumbnail.jpg', '/thumbnail.webp') WHERE meta_value LIKE '%/thumbnail.jpg%';"
```


yt-dlp download image:
```bash
yt-dlp -j --proxy "socks5://127.0.0.1:9150"  https://xhamster.com/videos/would-you-like-us-to-suck-you-off-grandpa-serina-gomez-and-mia-trejsi-for-oldhans-xhJOEen > info.json
```

Prevent MacOS sleep while run python:

```bash
caffeinate -i python3 my_script.py
```