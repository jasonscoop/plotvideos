from base64 import b64encode

import httpx

# === Configuration ===
api_url = "https://wp.garymeng.com/wp-json/wp/v2/posts"
user="gary"
passw = "jPDB vqSs YT2P BlDW L9c3 VY40"
credentials = b64encode(f"{user}:{passw}".encode()).decode("utf-8")
headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json"
}

# === Step 1: Create English Post ===
en_data = {
    "title": "Ai agent4",
    "content": "This is an English post.",
    "status": "publish",
    "lang": "en",
    "meta": {
        "_harikrutfiwu_url": "https://beconnected.esafety.gov.au/pluginfile.php/99437/mod_resource/content/2/what-is-ai%20%281%29.jpg",
        "_harikrutfiwu_alt": "Your image alt text"
    }
}

with httpx.Client() as client:
    en_response = client.post(api_url, json=en_data, headers=headers)
    en_response.raise_for_status()
    en_post = en_response.json()
    en_post_id = en_post["id"]
    print(f"✅ English post created with ID: {en_post_id}")

    # === Step 2: Create Chinese Translation ===
    zh_data = {
        "title": "ai智能体4",
        "content": "這是中文內容。",
        "status": "publish",
        "lang": "zh",
        "meta": {
            "_harikrutfiwu_url": "https://www.sdsd.com/wp-content/uploads/2020/04/New-SDSD.jpg",
            "_harikrutfiwu_alt": "Your image alt text"
        }
    }

    zh_response = client.post(api_url, json=zh_data, headers=headers)
    zh_response.raise_for_status()
    zh_post = zh_response.json()
    zh_post_id = zh_post["id"]
    print(f"✅ Chinese post created with ID: {zh_post_id}")


link_data = {
    "posts": {
        "en": en_post_id,
        "zh": zh_post_id
    }
}

with httpx.Client() as client:
    response = client.post(
        "https://wp.garymeng.com/wp-json/custom/v1/link-posts",
        json=link_data,
        headers=headers
    )
    print("✅ Posts linked:", response.json())

