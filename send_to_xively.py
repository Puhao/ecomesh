# -*- coding: utf-8 –*- 
#one thread receive data,other thread send data to the yeelink website,multithread program
#use hash table to store the yeelink datapoint address, each data has one datapoint address
#把输出传送到yeelink，同时可以接受yeelink网站的继电器控制代码

from threading import *
from Queue import *
from ZigSerial import ZigSerial
from time import *

import datetime
import crc16
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

#xively Sensor Data datastream addr [FEED_ID, Channel]
XiveDataPoint = { 0x6d0501:["1768542106","temperature"],
                 0x6d0502:["1768542106","humidity"],
                 0x6d0305:["1768542106","illumination"],
                 0x6d0b0b:["1768542106","pressure"],
                 }

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

def queue_info():
    while True:
        print "Size:", XivelyQueue.qsize()
        data = XivelyQueue.get()
        print data
        sleep(3)
    return

def main():
    receive_thread = Thread(target=sensor_data_receive)
    thread_list.append(receive_thread)

    #start send data
    #send_thread = Thread(target=xively_data_send)
    #thread_list.append(send_thread)

    send_thread = Thread(target=queue_info)
    thread_list.append(send_thread)

    for i in thread_list:
        i.start()

    for i in thread_list:
        i.join()

    db.close()

if __name__ == '__main__':
    main()