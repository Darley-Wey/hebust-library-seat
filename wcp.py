import requests


# 微信公众号
class WeChatPush():
    def __init__(self):
        # 微信公众号app_id
        app_id = 'wxapp_id'
        # 微信公众号app_secret
        app_secret = 'd0c9cf48b4ce7e30a60e14052251c535'
        url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}'
        dict = requests.get(url).json()
        self.token = dict['access_token']

    def push_success(self, receiver, stuNum, seat, date, time):
        url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=' + self.token
        data = {
            "touser": receiver,
            "url": "http://tsgic.hebust.edu.cn/seat/MyCurBespeakSeat.aspx",
            # 消息模板，微信公众号后台设置
            "template_id": "f1nfcLgFMg_cN_EaWGQ3n7h0-RMKgEqMqXZ0ryvifb0",
            "data": {
                'stuNum': {
                    'value': stuNum,
                    "color": "#173177"
                },
                "seat": {
                    "value": seat,
                    "color": "#173177"
                },
                'date': {
                    "value": date,
                    "color": "#173177"
                },
                'time': {
                    "value": time,
                    "color": "#173177"
                }
            }
        }
        if receiver != '':
            requests.post(url, json=data)

    def push_fail(self, receiver, stuNum, reason, *push_url):
        url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=' + self.token
        if len(push_url) == 0:
            push_url = ''
        else:
            push_url = push_url[0]
        data = {
            "touser": receiver,
            "url": push_url,
            # 消息模板
            "template_id": "sl-ko9IqhrtQ-IvaWjWgHo1-k-lOCoFEjm-JMVkftoc",
            "data": {
                'stuNum': {
                    'value': stuNum,
                    "color": "#173177"
                },
                "reason": {
                    "value": reason,
                    "color": "#173177"
                }
            }
        }
        if receiver != '':
            requests.post(url, json=data)
