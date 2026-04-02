
# How to deploy to cloudflare

Assume your websinamte will be `mybestwebsite`.

1. Setup database from Cloudflare portal or commands:
    ```shell
    npx wrangler d1 create mybestwebsite
    npx wrangler d1 execute mybestwebsite --remote --file=player/src/schema.sql
    npx wrangler d1 execute mybestwebsite --remote --command "UPDATE settings SET value = 'MyBestWebsite' WHERE key = 'site_name'; UPDATE settings SET value = 'https://pv.garymeng.com' WHERE key = 'fetch_api_url'; UPDATE settings SET value = 'Test@789' WHERE key = 'fetch_api_key';UPDATE settings SET value = 'title_original_id' WHERE key = 'slug_from';"
    ```
    Then copy the database id, it is a UUID.
2. Go to cloudflare, create worker applications.
    - Project name: `mybestwebsite`
    - Build command: <Empty>
    - Deploy command: `npm run deploy`
    - Path: `/player`
    - Variable name: `D1_DB_ID`
    - Variable value: <paste the database ID you got from step 1>
3. Click `Deploy` button.
4. Once deployment finished, bind your own domain.
