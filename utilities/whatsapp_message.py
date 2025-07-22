API_URL = "https://api.qikchat.in/v1/messages"
API_KEY = "JAux-Zc2i-aDXg"



def send_message_with_image(data):
        headers = {
        "QIKCHAT-API-KEY": API_KEY,
        "Content-Type": "application/json"
        }
        for message_instance in data:
            payload = {
                "to_contact": f"+91{message_instance['mobile']}",
                "type": "template",
                "template": {
                    "name": "new_order_receive",
                    "language": "en",
                    "components": [
                        {
                            "type": "header",
                            "parameters": [
                                # {
                                #     "type": "image",
                                #     "image": {
                                #         "link": "https://fastly.picsum.photos/id/237/200/300.jpg?hmac=TmmQSbShHz9CdQm0NkEjx1Dyh_Y984R9LpNrpvH2D_U"
                                #     }
                                # }
                                {
                                    "type": "image",
                                    "image": {
                                        "link": message_instance["image"]
                                        # "link":"https://wholesale.shiningdawn.in/retail_backend/jewelry_retail_api/assets/order_images/Repair%20Order/order_225/order_detail_162/20250508112830.jpg"
                                    }
                                }
                            ]
                        },
                        {
                            "type": "body",
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": message_instance["company_name"]
                                },
                                {
                                    "type": "text",
                                    "text": message_instance["product_name"]
                                },
                                {
                                    "type": "text",
                                    "text": message_instance["design_name"]
                                },
                                {
                                    "type": "text",
                                    "text": str(message_instance["gross_weight"])
                                },
                                {
                                    "type": "text",
                                    "text": message_instance["remarks"]
                                }
                            ]
                        }
                    ]
                }
            }
            print(payload)
            try:
                response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
                if response.status_code == 200:
                    print(f"Message sent successfully to {message_instance['mobile']}")
                else:
                    print(f"Failed to send message to {message_instance['mobile']}: {response.text}")
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")