import http.client
import json

import http.client
import json

def send_customer_reg_sms(mobile: str, otp: str, name: str, params, template_id, message):
    # print(mobile)
    # print(otp)
    # print(name)
    # print(params)
    # print(template_id)
    conn = http.client.HTTPSConnection("rest.qikberry.ai")
    
    payload = json.dumps({
        "to": f"+91{mobile}",
        "sender": "TNJWLS",
        "service": "SI",
        "template_id": template_id,
        "message": message,
        "params": params
    })

    headers = {
        'Authorization': 'Bearer 590a9ede5ed3a689238c920455c531cc',
        'Content-Type': 'application/json'
    }

    conn.request("POST", "/v1/sms/messages", payload, headers)
    res = conn.getresponse()
    print(res)
    data = res.read()
    print(data.decode("utf-8"))
    return data.decode("utf-8")
