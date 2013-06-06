import MySQLdb
from threading import *
from ZigSerial import ZigSerial
from time import *
from struct import *
import socket
import crc16
    
SerialPort = '/dev/ttyAMA0'
baudrate = 115200
        
db = MySQLdb.connect(host="localhost", user="mesh", passwd="zigbee", db="ecomesh_db")
cur = db.cursor()

sql_insert = "INSERT INTO device_data(DevAddr, SensorId, SensorDataId, DataRcv) VALUES(%s, %s, %s, %s)"
sql_select = "SELECT DataRcv from device_data where DevAddr=%s && SensorId=%s && SensorDataId=%s order by DataId desc limit 1"

def CrcCal(crc, list):
    crc = 0;
    for i in list:
        crc = crc16.crc16xmodem(i, crc)
    return crc

def main():
    print "Creating Socket...."
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 51423
    host = "10.12.48.129"
    print "Conneting to ----"+host
    print "!"
    try:
        print "Conneted!"
        s.connect((host, port))
    except socket.error, e:
        print "Error happen, %s" %(e,)
        print "DataRead thread starting!"
    DevAddr = 100
    SensorId = 4
    SensorDataId = 1 
    #MySQLdb respect the data as string, so I have to convert the data into string to store in MySQL
    cur.execute(sql_select, [str(DevAddr), str(SensorId), str(SensorDataId)])
    result = cur.fetchone()
    print result
    for i in result:
        print i
    DataRcv = result[0]
    socket_pack = pack("BBBh", DevAddr, SensorId, SensorDataId, DataRcv)
    SensorDataId = 2
    s.sendall(socket_pack)
    cur.execute(sql_select, [str(DevAddr), str(SensorId), str(SensorDataId)])
    result = cur.fetchone()
    print result
    for i in result:
        print i


    db.close()
if __name__ == '__main__':
    main()
