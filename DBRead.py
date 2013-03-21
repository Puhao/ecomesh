import MySQLdb
from threading import *
from ZigSerial import ZigSerial
from time import *
    
port = '/dev/ttyAMA0'
baudrate = 115200
        
db = MySQLdb.connect(host="localhost", user="mesh", passwd="zigbee", db="ecomesh_db")
cur = db.cursor()

sql_insert = "INSERT INTO device_data(DevAddr, SensorId, SensorDataId, DataRcv) VALUES(%s, %s, %s, %s)"
sql_select = "SELECT DataRcv from device_data where DevAddr=%s && SensorId=%s && SensorDataId=%s order by DataId desc limit 1"


def main():
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
    SensorDataId = 2
    cur.execute(sql_select, [str(DevAddr), str(SensorId), str(SensorDataId)])
    result = cur.fetchone()
    print result
    for i in result:
        print i


    db.close()
if __name__ == '__main__':
    main()
