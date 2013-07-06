# coding=utf-8
#把输出传送到yeelink，同时可以接受yeelink网站的继电器控制代码
from weibo import *
import time

APP_KEY = '204574897' # app key
APP_SECRET = '16090a4faf9ffdf06c9d377f26f4abd7' # app secret
CALLBACK_URL = 'www.renren.com/yuanpuhao' # callback url

from threading import *
from Queue import *
from ZigSerial import ZigSerial
from time import *
import urllib2
import urllib
import json
import crc16

#At first, I just use the PL2303H USB-UART module to test the project
port = '/dev/ttyUSB0'
baudrate = 115200

zig = ZigSerial(port, baudrate)

SerWrLock = Lock()

#yeelink http request header
api_key = "749026a27b17f437ed2f932cbf0f8f5d"
header = {"U-ApiKey":api_key}

#yeelink relay control address
RelayAddr = [   [0, 3557, 4959], \
                [1, 3557, 4960], \
                [2, 3557, 4961], \
                [3, 3557, 4962], \
                [4, 3557, 4963], \
                [5, 3557, 4964], \
                [6, 3557, 4965], \
                [7, 3557, 4966], \
                [8, 3557, 4967], \
                [9, 3557, 4968], \
                [10,3557, 4969], \
                [11,3557, 4970], \
                [12,3557, 4971], \
                [13,3557, 4972], \
                [14,3557, 4973], \
                [15,3557, 4974], \
                ]

sensor_data = {"value":21.1}
jdata = json.dumps(sensor_data)

#store the zigbee data,SensorData thread pass the data to the yeelink send thread 
DataQueue = Queue() 

#thread list
thread_list = []

#Zigbee ecomesh data type
ZigData = { "DevAddr":0x11,
            "SensorId":0x3,
            "SensorDataId":0x01,
            "SensorData":0x11}
#Data Adjust
DataAdj = { 0x01:0.01,
            0x02:0.01,
            0x05:1.25,
            0x06:0.01,
            0x03:1.0,
            0x04:0.001,
            0x0b:0.1,
            }
#Yeelink Sensor Data pointdata addr [Deviceid, SensorId]
YeeDataPoint = { 0x6d0501:["3762","5340"],
                 0x6d0502:["3762","5341"],
                 0x6d0305:["3762","5342"],
                 0x6d0b0b:["3762","5343"],
                 }

#Sensor List
#[名称，单位，数值比例, 默认值]
SensorList = {
    0x01:["温度", "°C", 0.01, 25],
    0x02:["湿度", "%RH", 0.01, 71],
    0x05:["光照强度", "lux", 1.25, 1200],
    0x0b:["气压", "hPa", 0.1, 1013],
}
CurrentState = {
    "SensorId":0x01,
    "Data":24,
}
#current weather situation
TmprQueue = Queue()
HumyQueue = Queue()
LighQueue = Queue()
PrssQueue = Queue()

WeatherQueueList = {
    0x01:TmprQueue,
    0x02:HumyQueue,
    0x05:LighQueue,
    0x0b:PrssQueue,
}

#sina weibo post message queue
MessageQueue = Queue()

def sensor_data_receive():
    print "Start Getting the zigbee network data"
    while True:
        zig.pkt_rcv()
        if (zig.RcvFlag):
            print "DevAddr =", zig.DevAddr,
            print "SensorId =", zig.SensorId,            
            print "SensorDataId =", zig.SensorDataId,
            print "SensorDataGet =", zig.SensorDataGet

            ZigData["DevAddr"] = zig.DevAddr
            ZigData["SensorId"] = zig.SensorId
            ZigData["SensorDataId"] = zig.SensorDataId
            ZigData["SensorData"] = zig.SensorDataGet
            DataQueue.put(ZigData)
            if zig.SensorDataId in SensorList:
                data = zig.SensorDataGet * SensorList[zig.SensorDataId][2]
                WeatherQueueList[zig.SensorDataId].put(data)

    return

def yeelink_data_send(thread_num):
    while True:
        try:
            data = DataQueue.get()
        except Queue.Empty:
            print "Queue Empty"
        #print "I get data",data
        tmp = data["DevAddr"]
        tmp = tmp << 8 | data["SensorId"]
        tmp = tmp << 8 | data["SensorDataId"]
        #print "tmp = 0x%x"  %(tmp,)
        if YeeDataPoint.has_key(tmp):
            device_id = YeeDataPoint[tmp][0]
            sensor_id = YeeDataPoint[tmp][1]
            #print "device_id = ", device_id
            #print "sensor_id = ", sensor_id 
            yeelink_destiny = "http://api.yeelink.net/v1.0/device/" + device_id + "/sensor/" + sensor_id + "/datapoints"
            print "Yeelink URL",yeelink_destiny
            if DataAdj.has_key(data["SensorDataId"]):
                sensor_data["value"] = data["SensorData"] * DataAdj[data["SensorDataId"]]
            else:
                sensor_data["value"] = data["SensorData"]
            print "Sensor Data = ",sensor_data["value"]
            jdata = json.dumps(sensor_data)
            try:
                req = urllib2.Request(yeelink_destiny, None, header)
            except:
                print "Request Error"
            try:
                response = urllib2.urlopen(req,jdata)
            except urllib2.URLError as e:
                print "UrlError",e
            except urllib2.HTTPError as e:
                print "Http Error Happen"
                print e.read()
        else:
            print "Yeelink has no such datapoint address"
        #print "Send Thead! Thread Number = ",thread_num
        sleep(1)
    return

def weibo_weather_message():
    while True:
        for i in WeatherQueueList:
            while not WeatherQueueList[i].empty():
                SensorList[i][3] = WeatherQueueList[i].get()
            SensorList[i][3] = WeatherQueueList[i].get()
        WeatherSituationMess = "天气情况："
        for i in SensorList:
            SensorMessage = SensorList[i]
            WeatherSituationMess += SensorMessage[0] + str(SensorMessage[3]) + SensorMessage[1] + ","
        WeatherSituationMess = "我去年买两个表，这个时间点" + WeatherSituationMess + "那今天是个xx天啊！"
        MessageQueue.put(WeatherSituationMess)
        sleep(2572)


def post_weibo(client):
    MessageToPost = MessageQueue.get()
    try:
        MessagePostBack = client.statuses.update.post(status= MessageToPost)
        for i in MessagePostBack:
            print i,
            print ":",
            print MessagePostBack[i]
    except:
        print "Post Weibo Error"
    return

def main():
    client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    url = client.get_authorize_url()
    print url    
    code_get = raw_input("print code:")
    r = client.request_access_token(code_get)
    access_token = r.access_token
    expires_in = r.expires_in
    client.set_access_token(access_token, expires_in)

    #thread
    weibo_weather_message_thread = Thread(target=weibo_weather_message)
    thread_list.append(weibo_weather_message_thread)

    post_weibo_thread = Thread(target=post_weibo, args =(client,))
    thread_list.append(post_weibo_thread)

    receive_thread = Thread(target=sensor_data_receive)
    thread_list.append(receive_thread)

    #start send data
    for i in range(0,4):
        send_thread = Thread(target=yeelink_data_send,args=(i,))
        thread_list.append(send_thread)

    for i in thread_list:
        i.start()

    for i in thread_list:
        i.join()

if __name__ == '__main__':
    main()