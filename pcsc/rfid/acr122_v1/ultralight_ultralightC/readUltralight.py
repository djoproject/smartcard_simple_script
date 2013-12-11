#!/usr/bin/python2.6
# -*- coding: utf-8 -*-

from smartcard.System import readers

DEBUG = False

def init():
    #get reader list
    r=readers()
    
    #no reader connected
    if len(r) == 0:
        print "No available reader"
        exit()

    #reader connection
    connection = r[0].createConnection()
    connection.connect()

    getReaderVersion(connection)

    data, sw1, sw2 = connection.transmit([0xff, 0x0, 0x0, 0x0, 0x4, 0xd4, 0x4a, 0x2, 0x0, 0x0])

    #check error code
    if sw1 != 0x61:
        print "polling error"
        exit()

    #get response
    data, sw1, sw2 = connection.transmit([0xff,0xC0,0x0,0x0,sw2])
    if DEBUG:
        print data, "%02x"%sw1, "%02x"%sw2
    
    #check error code
    if sw1 != 0x90 and sw2 != 0x00:
        print "get Response error"
        exit()

    if len(data) < 2:
        print "not enought data"
        exit()
        
    return connection
        
def transmit(tag_apdu, tag = 1):    
    pn53x_apdu = [0xd4, 0x40, tag]
    pn53x_apdu.extend(tag_apdu)
    
    send_data = [0xff, 0x0, 0x0, 0x0, len(pn53x_apdu),]
    send_data.extend(pn53x_apdu)
    send_data.append(0x0) #data expected
    
    #send data
    data, sw1, sw2 = connection.transmit(send_data)
    
    #check error code
    if sw1 != 0x61:
        print "polling error"
        exit()
    
    #retrieve response
    data, sw1, sw2 = connection.transmit([0xff,0xC0,0x0,0x0,sw2])
    
    #check error code
    if sw1 != 0x90 and sw2 != 0x00:
        print "get Response error"
        exit()
        
    if len(data) < 3:
        print "Not enough data"
        exit()
        
    return data[3:]

def getReaderVersion(connection):
    data, sw1, sw2 = connection.transmit([0xff,0x0,0x48,0x1,0x0])
    if DEBUG:
        print data, sw1, sw2
    
    ver = ""
    for c in data:
	print chr(c),
      
        #ver += chr(c)
    print chr(sw1),
    print chr(sw2)
    #print ver

if __name__ == "__main__":    
    #init connection
    connection = init()
    
    
    #print reader version
    getReaderVersion(connection)
    
    #read each sector
    print "page no\t  data"
    for i in range(0,41, 4):
        print str(i) + "-" + str(i+3) + "\t: " + str(transmit([0x30,i]))
    
    
