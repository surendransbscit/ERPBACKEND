import requests
import json

def send_push_notification(player_id ,title, message):
        ONESIGNAL_APP_ID = "62959c11-07c4-4790-a9d1-a497ab4ed64a"
        ONESIGNAL_API_KEY = "os_v2_app_mkkzyeihyrdzbkorusl2wtwwjkxvec7foizukgngxfdv5dm2tcgym3k6gpeqtthz7ucs4qxshj6atcp2ljiv4kynqev2n7egqf6s4vq"
        
        url = "https://api.onesignal.com/notifications?c=push"  
        headers = {
            "Authorization": f"Key {ONESIGNAL_API_KEY}",
            "accept": "application/json",
            "content-type": "application/json",
        }
        payload = {
            "app_id": ONESIGNAL_APP_ID,
            "contents": {"en": message},
            "include_subscription_ids": [player_id],  # Matches your cURL request
        }
        
        response = requests.post(url, headers=headers, json=payload)
        print(response.text)
        return response.json()