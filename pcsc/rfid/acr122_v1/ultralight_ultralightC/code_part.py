### PART  () ###
### PART 1 (init context + establish a connection) ###

#import the smartcard library
from smartcard.System import readers

#get reader list
r=readers()

#no reader connected
if len(r) == 0:
    print "No available reader"
    exit()

#reader connection
connection = r[0].createConnection()
connection.connect()

### PART 2 (list function) ###
#>>>l = [11, 22, 33]
#>>>l = l + [4]
#>>>l
#[1, 2, 3, 44]
#>>l[0]
#11
#>>l[3]
#44

### PART 3 (get firmware version) ###
data, sw1, sw2 = connection.transmit([0xff,0x0,0x48,0x1,0x0])

for c in data:
    print chr(c)
print chr(sw1)
print chr(sw2)

### PART 4 (polling) ###
#send tag request
data, sw1, sw2 = connection.transmit([0xff, 0x0, 0x0, 0x0, 0x4, 0xd4, 0x4a, 0x2, 0x0, 0x0])

#check error code
if sw1 != 0x61:
    print "polling error"
    exit()

#get polling answer
data, sw1, sw2 = connection.transmit([0xff,0xC0,0x0,0x0,sw2])

#check error code
if sw1 != 0x90 and sw2 != 0x00:
    print "get Response error"
    exit()

if len(data) < 3:
    print "not enought data"
    exit()

#is there at least one tag on the reader ?
if data[2] < 1:
    print "no tag on the reader"
    exit()

### PART 5 (transfert function) ###
def transfer(connection, tag_apdu):
    pn53x_apdu = [0xd4, 0x40, 0x01]
    pn53x_apdu.extend(tag_apdu)
    
    send_data = [0xff, 0x0, 0x0, 0x0, len(pn53x_apdu),]
    send_data.extend(pn53x_apdu)
    send_data.append(0x0) #data expected
    
    #send request
    data, sw1, sw2 = connection.transmit(send_data)

    #check error code
    if sw1 != 0x61:
        print "to chip error"
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

### PART 6 (hexa function) ###
#>>>hex(55)
#'0x37'
#>>>0x37
#55
#>>>int("0x37", 16)
#0x55


### PART 7 (read data) ###
sector_to_read = 0x04
data = transfer(connection, [0x30, sector_to_read])
print data

# but this is ugly => convert to characters
# advice: extract in a function
string_data = ""
for octet in data:
    string_data += chr(octet)

print string_data

### PART 8 (write data) ###

FIRST_USER_MEMORY_PAGE = 4
LAST_USER_MEMORY_PAGE = 39

# second version of transfer, with a guard
def transfer(connection, tag_apdu):
    # preserve the tags: prevent writing readonly and write-once memory
    write_command = 0xa0
    allowed_memory_pages = range(FIRST_USER_MEMORY_PAGE, LAST_USER_MEMORY_PAGE + 1)

    if tag_apdu[0] == write_command and tag_apdu[1] not in allowed_memory_pages:
        print "Ouch! Attempted to write non-user memory. Your apdu: " + str(tag_apdu)
        exit()
        
    pn53x_apdu = [0xd4, 0x40, 0x01]
    pn53x_apdu.extend(tag_apdu)
    
    send_data = [0xff, 0x0, 0x0, 0x0, len(pn53x_apdu),]
    send_data.extend(pn53x_apdu)
    send_data.append(0x0) #data expected
    
    #send request
    data, sw1, sw2 = connection.transmit(send_data)

    #check error code
    if sw1 != 0x61:
        print "to chip error"
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

sector_to_write = 0x4
data = [0x4F, 0x54, 0x53, 0x0A]
padding = [0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00] 
full_apdu = [0xa0, sector_to_write] + data + padding
transfer(connection, full_apdu)
print "wrote data"
# data should be the empty list, because no data is sent back from the reader
# this is a read, after all

### PART 9 () ###

## Vcard

#VERSION:2.1 !!!

# basically works like:
# <field name>:<field part 1>;<field part 2>;...

# let's write

#BEGIN:VCARD
#N:Potter;Harry;;Mr;
#ADR;DOM;PARCEL;HOME:;;Privet Drive;Little Whinging;Surrey;;United Kingdom
#EMAIL;INTERNET:harry.potter@hogwarts.edu
#ORG:hogwarts
#TITLE:wizard
#ROLE:student
#END:VCARD

# in python, statements continue until last ([{ is closed
# + using this form (intead of triple-quoted strings) to explicit the line terminator
vcard = ( "BEGIN:VCARD\n"
        + "N:Potter;Harry;;Mr;\n"
        + "ADR;DOM;PARCEL;HOME:;;4, Privet Drive;Little Whinging;Surrey;;\n"
        + "TITLE:wizard\n"
        + "ROLE:student\n"
        + "END:VCARD\n"
        )

# if you are used to python, rewrite the following using slices!
# <ugly warning>you should not program like this in python</ugly warning>

# split vcards characters in blocs of 4 octets
blocks = []
for block_number in range(len(vcard) / 4):
    index = block_number * 4
    blocks += [[ord(vcard[index]), ord(vcard[index+1]), ord(vcard[index+2]), ord(vcard[index+3])]]

# finish last block
last_block = []
for index in range(len(blocks) * 4, len(vcard)):
    last_block += [ord(vcard[index])]

# add last block if needed
if last_block != []:
    blocks += [last_block]

# verify we will be able to write all in user memory
if len(blocks) > LAST_USER_MEMORY_PAGE - FIRST_USER_MEMORY_PAGE:
    print "vcard is too large for the user memory of the card!"
    print "number of required blocs: " + str(len(blocks))
    print "number of 4 byte user memory blocs: " + str(LAST_USER_MEMORY_PAGE - FIRST_USER_MEMORY_PAGE)
    exit()


# 
# write each block to the card


### PART 10 () ###

### PART 11 () ###

### PART 12 () ###

