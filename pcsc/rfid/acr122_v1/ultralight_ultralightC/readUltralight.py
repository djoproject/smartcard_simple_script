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
    
    #print reader list
    print "reader(s) : ",r
    
    #reader connection
    connection = r[0].createConnection()
    connection.connect()
    
    if DEBUG:
        print "poling"
    
    #poll
        #0xff : class
        #0x0  : instruction (Direct Transmit)
        #0x0  : arg1
        #0x0  : arg2
        #0x04 : parameter length
        #0xd4 : pn532 : ToChip
        #0x4a : pn532 : InListPassiveTarget
        #0x1  : pn532 : max tag (1 or 2)
        #0x0  : pn532 : brTy (see documentation)
        #0x0  : data to retrieve 
    data, sw1, sw2 = connection.transmit([0xff, 0x0, 0x0, 0x0, 0x4, 0xd4, 0x4a, 0x2, 0x0, 0x0])
    if DEBUG:
        print data, "%02x"%sw1, "%02x"%sw2
    
    #check error code
    if sw1 != 0x61:
        print "polling error"
        exit()
    
    if DEBUG:
        print sw2," bytes to retrieve"
    
    #get response
        #0xff : class
        #0x0  : instruction (GetResponse)
        #0x0  : arg1
        #0x0  : arg2
        #0x0  : parameter length
        #sw2  : data to retrieve
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
    if DEBUG:
        print "tag on the reader: ", data[2]
    offset = 3
    for i in range(0,data[2]):
        if len(data) < offset+7:
            print "not enought data"
            exit()
        
        print "tag id: ",data[offset]
        print "anticolision data: ",data[offset+1:offset+4]
        print "UID length: ",data[offset+4]
        
        #TODO check UID length
        
        print "UID: ",data[offset+5:offset+5+data[offset+4]]
        offset = offset+5+data[offset+4]
        print
        
    return connection
        
def transmit(tag_apdu, tag = 1):
    #TODO check tag, must be 1 or 2
    
    pn53x_apdu = [0xd4, 0x40, tag]
    pn53x_apdu.extend(tag_apdu)
    
    send_data = [0xff, 0x0, 0x0, 0x0, len(pn53x_apdu),]
    send_data.extend(pn53x_apdu)
    send_data.append(0x0) #data expected
    
    #send data
    data, sw1, sw2 = connection.transmit(send_data)
    if DEBUG:
        print data, "%02x"%sw1, "%02x"%sw2
    
    #check error code
    if sw1 != 0x61:
        print "polling error"
        exit()
    
    if DEBUG:
        print sw2," bytes to retrieve"
    
    #retrieve response
    data, sw1, sw2 = connection.transmit([0xff,0xC0,0x0,0x0,sw2])
    if DEBUG:
        print data, "%02x"%sw1, "%02x"%sw2
    
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
        ver += chr(c)
    ver += chr(sw1)
    ver += chr(sw2)
    print ver

if __name__ == "__main__":    
    #init connection
    connection = init()
    
    
    #print reader version
    getReaderVersion(connection)
    
    #read each sector
    for i in range(0,41, 4):
        print i," : ", transmit([0x30,i])
    
    
