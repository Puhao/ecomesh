# -*- coding: utf-8 –*- 
from weibo import *

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

import datetime
import xively

API_KEY = "gUhV5JqXypy6dkjjxCXMsMMv90Kdp0REa2GrJqjdaQum5mZ9"
DEBUG = True
# initialize api client
api = xively.XivelyAPIClient(API_KEY)

# function to return a datastream object. This either creates a new datastream,
# or returns an existing one
def get_datastream(feed,channel):
  try:
    datastream = feed.datastreams.get(channel)
    if DEBUG:
      print "Found existing datastream"
    return datastream
  except:
    if DEBUG:
      print "Creating new datastream"
    datastream = feed.datastreams.create(channel)
    return datastream



#At first, I just use the PL2303H USB-UART module to test the project
port = '/dev/ttyUSB0'
baudrate = 115200

zig = ZigSerial(port, baudrate)


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

XivelyQueue = Queue()

#thread list
thread_list = []

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

#xively Sensor Data datastream addr [FEED_ID, Channel]
XiveDataPoint = { 0x6d0501:["1768542106","temperature"],
                 0x6d0502:["1768542106","humidity"],
                 0x6d0305:["1768542106","illumination"],
                 0x6d0b0b:["1768542106","pressure"],
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

WeatherLock = Lock()

#接收无线传感网络数据
def sensor_data_receive():
    print "Start Getting the zigbee network data"
    while True:
        zig.pkt_rcv()
        if (zig.RcvFlag):
            ZigData = {}
            ZigData["DevAddr"] = zig.DevAddr
            ZigData["SensorId"] = zig.SensorId
            ZigData["SensorDataId"] = zig.SensorDataId
            ZigData["SensorData"] = zig.SensorDataGet
            if ZigData["SensorDataId"] in DataAdj:
                ZigData["SensorData"] = ZigData["SensorData"] * DataAdj[ZigData["SensorDataId"]]
            if DEBUG:
                print "Queue Put:", ZigData
            XivelyQueue.put(ZigData)
            DataQueue.put(ZigData)
            if zig.SensorDataId in SensorList:
                data = ZigData["SensorData"]
                SensorList[zig.SensorDataId][3] = data
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
            sensor_data["value"] = data["SensorData"]
            yeelink_destiny = "http://api.yeelink.net/v1.0/device/" + device_id + "/sensor/" + sensor_id + "/datapoints"
            if DEBUG:
                print "Yeelink URL",yeelink_destiny   
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

def xively_data_send():
    while True:
        data = XivelyQueue.get()
        if DEBUG:
            print "I get data:",data
        tmp = data["DevAddr"]
        tmp = tmp << 8 | data["SensorId"]
        tmp = tmp << 8 | data["SensorDataId"]
        #print "tmp = 0x%x"  %(tmp,)
        if tmp in XiveDataPoint:
            FEED_ID = XiveDataPoint[tmp][0]
            Channel = XiveDataPoint[tmp][1]
            feed = api.feeds.get(FEED_ID)
            datastream = get_datastream(feed,Channel)
            datastream.current_value = data["SensorData"]
            datastream.at = datetime.datetime.utcnow()
            try:
                datastream.update()
            except requests.HTTPError as e:
                print "HTTPError({0}): {1}".format(e.errno, e.strerror)
        sleep(1)
    return

def weather_info():
    for i in WeatherQueueList:
        while not WeatherQueueList[i].empty():
            SensorList[i][3] = WeatherQueueList[i].get()
        SensorList[i][3] = WeatherQueueList[i].get()
    WeatherSituationMess = "天气情况："
    for i in SensorList:
        SensorMessage = SensorList[i]
        WeatherSituationMess += SensorMessage[0] + str(SensorMessage[3]) + SensorMessage[1] + ","
    WeatherSituationMess += "就这么个样子。"
    return WeatherSituationMess

def weibo_weather_message():
    while True:
        WeatherLock.acquire()
        WeatherSituationMess = weather_info()
        WeatherSituationMess = "我去年买两个表，这个时间点" + WeatherSituationMess
        WeatherLock.release()
        MessageQueue.put(WeatherSituationMess)
        sleep(12583)
    return

def find_dawn():
    DawnWait = True
    while True:
        if "020000" == strftime("%H%M%S",localtime()):
            DawnWait = True
        if strftime("%H%M%S",localtime()) == "040000":
            if DawnWait:
                DawnWait = False
                while(SensorList[0x05][3] < 3):
                    pass
                WeatherLock.acquire()
                WeatherSituationMess = weather_info()
                WeatherLock.release()
                Message = "我勒个去，天已经开始亮了啊！" + WeatherSituationMess + "开始有光照到阳台了！屌丝们，该起床洗洗干活啦o(╯□╰)o"
                MessageQueue.put(Message)
    return

def good_morning():
    while True:
        if "073030" == strftime("%H%M%S",localtime()):
            if (SensorList[0x05][3]) < 8000:
                Message = "早上光照不是很强，不会被晒死。"
            else:
                Message = "早上光照这么强，一个大晴天啊。"
            if (SensorList[0x02][3]) > 92:
                Message += "大早上湿度这么大，下雨了。"
            WeatherLock.acquire()
            Message += weather_info()
            WeatherLock.release()
            MessageQueue.put(Message)

def post_weibo(client):
    while True:
        MessageToPost = MessageQueue.get()
        try:
            MessagePostBack = client.statuses.update.post(status= MessageToPost)
            if DEBUG:
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
    find_dawn_thread = Thread(target=find_dawn)
    thread_list.append(find_dawn_thread)

    good_morning_thread = Thread(target=good_morning)
    thread_list.append(good_morning_thread)

    weibo_weather_message_thread = Thread(target=weibo_weather_message)
    thread_list.append(weibo_weather_message_thread)

    post_weibo_thread = Thread(target=post_weibo, args =(client,))
    thread_list.append(post_weibo_thread)

    receive_thread = Thread(target=sensor_data_receive)
    thread_list.append(receive_thread)

    xively_data_send_thread = Thread(target=xively_data_send)
    thread_list.append(xively_data_send_thread)

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