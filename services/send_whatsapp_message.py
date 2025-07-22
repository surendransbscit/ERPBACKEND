import os
import json
import requests

API_URL = os.getenv('QIKCHAT_URL')
API_KEY = os.getenv('QIKCHAT_KEY')

headers = {
        "QIKCHAT-API-KEY": API_KEY,
        "Content-Type": "application/json"
        }


def send_whatsapp_message(mobile_num, type, template_name, language, message_components):
    
    payload = {
        "to_contact": f"+91{mobile_num}",
        "type": type,
        "template": {
            "name": template_name,
            "language": language,
            "components" : message_components
            # "components": [
            #     # {
            #     #     "type": "header",
            #     #     "parameters": [
            #     #         {
            #     #             "type": "image",
            #     #             "image": {
            #     #                 "link": "https://fastly.picsum.photos/id/237/200/300.jpg?hmac=TmmQSbShHz9CdQm0NkEjx1Dyh_Y984R9LpNrpvH2D_U"
            #     #             }
            #     #         }
            #     #         # {
            #     #         #     "type": "image",
            #     #         #     "image": {
            #     #         #         "link": message_instance["image"]
            #     #         #     }
            #     #         # }
            #     #     ]
            #     # },
            #     {
            #         "type": "body",
            #         "parameters": [
            #             {
            #                 "type": "text",
            #                 "text": message_instance["company_name"]
            #             },
            #             {
            #                 "type": "text",
            #                 "text": message_instance["product_name"]
            #             },
            #             {
            #                 "type": "text",
            #                 "text": message_instance["design_name"]
            #             },
            #             {
            #                 "type": "text",
            #                 "text": message_instance["remarks"]
            #             }
            #         ]
            #     }
            # ]
        }
    }
    # print(payload)
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print(f"Message sent successfully to {mobile_num}")
        else:
            print(f"Failed to send message to {mobile_num}: {response.text}")
    except Exception as e:
        print(f"Error sending message to {mobile_num}: {e}")