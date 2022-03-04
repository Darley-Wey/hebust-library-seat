from bs4 import BeautifulSoup
from wcp import WeChatPush
import requests
import re
import time
import datetime
import json
import math


# 用户类，包含学号，密码，预约时间，用户微信对推送公众号的openid
class user(object):
    def __init__(self, stuNum, pwd, time, weChat):
        self.stuNum = stuNum
        self.pwd = pwd
        self.time = time
        self.weChat = weChat


# 此处存储用户信息
users = [
    user('user1', 'password', '9:00', 'oCLvE53QWS8tOJEUZaCkJ3miwe5k'),
    user('user2', 'password', '10:00', 'oCLvE53QWS8tOJEUZaCkJ3miwe5k')
]


# 登录超星图书馆
def login_library(session, user, push):
    session.get('http://m.5read.com/2149')
    url = 'http://mc.m.5read.com/irdUser/login/opac/opacLogin.jspx'
    data = {
        'schoolid': '2149',
        'backurl': '',
        'userType': '0',
        'username': user.stuNum,
        'password': user.pwd
    }
    response = session.post(url, data).text
    error = re.findall(r'em>(.*)<', response)
    if len(error) == 0:
        return True
    else:
        log = error[0]
        print(stuNum, log)
        push.push_fail(user.weChat, user.stuNum, log)
        return False


# 登录预约系统
def login_system(session):
    url = 'http://mc.m.5read.com/cmpt/opac/opacLink.jspx?stype=1'
    response = session.get(url, allow_redirects=False)
    location = response.headers['Location']
    sn = re.search('sn=(.*?)&', location, re.S).group(1)
    #sn = re.search('name="sn".*?value="(.*?)"', response, re.S).group(1)
    url = 'http://tsgic.hebust.edu.cn/seat/validate.aspx?needsn=true&sn='+sn
    session.get(url)


def get_time(user):
    now = datetime.datetime.now()
    localDate = now.strftime('%Y/%m/%d')
    localtime = now.strftime('%H:%M:%S')
    if user.time[1:2] == ':':
        userTime = '0' + user.time + ':00'
    else:
        userTime = user.time+':00'
    n_days = now + datetime.timedelta(days=1)
    tomorrowDate = n_days.strftime('%Y/%m/%d')
    if localtime < userTime:
        time = localDate + ' ' + userTime
    else:
        time = tomorrowDate + ' ' + userTime
    # print(time)
    return time


# 检查占座情况
def have_bespeaked(session):
    url = 'http://tsgic.hebust.edu.cn/ajaxpro/WechatTSG.Web.Seat.Menu2,WechatTSG.Web.ashx'
    session.headers['X-AjaxPro-Method'] = 'HaveBespeaked'
    response = session.post(url).text
    status = response.split('"')[1]
    # print(status)
    if status == '1':
        #log = '你已有预约座位'
        return True
    else:
        return False


# 当前座位信息
def my_current_seat(session, user):
    url = 'http://tsgic.hebust.edu.cn/seat/MyCurBespeakSeat.aspx'
    response = session.get(url).text
    # print(response)
    stuNum = re.search(
        '<input name="hidIdent_id".*?value="(.*?)" />', response, re.S)
    values = re.findall(
        '<div class="col-md-10".*?value="(.*?)" /></div>', response, re.S)
    lefttime = re.search(
        '<input name="hidlefttime".*?value="(.*?)" />', response, re.S)
    user.room = values[0]
    user.seat = values[1]
    datetime = values[2]
    pattern = re.compile(r'[/\s]')
    result = pattern.split(datetime)
    user.date = result[1] + "月" + result[2] + "日"
    user.time = result[3][:-3]
    lefttime = int(lefttime.group(1))
    left_hour = math.floor((lefttime / 3600) % 24)
    left_minute = math.floor((lefttime / 60) % 60)
    user.lefttime = '%d小时%d分钟' % (left_hour, left_minute)


# 获取用户设置的喜爱座位信息
def getSeatNum(session):
    url = 'http://tsgic.hebust.edu.cn/ajaxpro/WechatTSG.Web.Seat.BespeakSeat.BespeakChoice,WechatTSG.Web.ashx'
    session.headers['X-AjaxPro-Method'] = 'SeatCanBeUsed'
    response = session.post(url).text
    seatNum = response.split('"')[1]
    # print(seatNum)
    return seatNum


# 占座
def getSeat(session, user):
    seatNum = getSeatNum(session)
    time = get_time(user)
    if seatNum != '':
        url = 'http://tsgic.hebust.edu.cn/ajaxpro/WechatTSG.Web.Seat.BespeakSeat.BespeakChoice,WechatTSG.Web.ashx'
        session.headers['X-AjaxPro-Method'] = 'OnekeyBespeak'
        payLoad = {
            "strSeatNo": seatNum,
            # "BespeakTime": "2020/11/27 8:00:00"
            "BespeakTime": time
        }
        session.post(url, data=json.dumps(payLoad))
        return True
    else:
        return False


# 占座结果
def getResult(session):
    url = 'http://tsgic.hebust.edu.cn/seat/BespeakSeat/SubmitBespeak.aspx'
    response = session.get(url).text
    response = BeautifulSoup(response, 'html.parser')
    resultScript = (response.find_all('script'))
    resultKey = str(resultScript[3])
    return resultKey


if __name__ == "__main__":
    time.sleep(15)
    push = WeChatPush()
    print("\n\n", time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()), "\n")
    for user in users:
        weChatID = user.weChat
        stuNum = user.stuNum
        session = requests.session()
        if login_library(session, user, push):
            login_system(session)
            count = 0
            while True:
                count += 1
                print("CardNum:" + stuNum)
                if have_bespeaked(session):
                    my_current_seat(session, user)
                    log = '你已有预约座位，点击查看座位信息'
                    print(log)
                    seat_url = 'http://tsgic.hebust.edu.cn/seat/MyCurBespeakSeat.aspx'
                    push.push_fail(user.weChat, stuNum, log, seat_url)
                    break
                elif getSeat(session, user):
                    resultKey = getResult(session)
                    result = re.search(
                        'title:"(.*?)".*?type:"(.*?)"', resultKey, re.S)
                    title = result.group(1)
                    type = result.group(2)
                    print("Result:", title+"\n")
                    if type == "success":
                       # my_current_seat(session,user)
                        pattern = re.compile(r'[约，于/\s前]')
                        values = pattern.split(title)
                        seat = values[1]
                        date = f'{values[3]}年{values[4]}月{values[5]}日'
                        inTime = f'{values[6]}前'
                        push.push_success(weChatID, stuNum, seat, date, inTime)
                        break
                    elif count >= 1 and count < 10:
                        time.sleep(1)
                    else:
                        push.push_fail(weChatID, stuNum, result)
                        break
                else:
                    log = '你的喜爱座位已全部被占！'
                    print(log)
                    push.push_fail(weChatID, stuNum, log)
                    break
            time.sleep(1)
    print("\n本次任务结束\n")
    exit()
