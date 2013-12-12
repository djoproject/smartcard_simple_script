### PART  () ###
### PART 1 (init context + establish a connection) ###

#import the smartcard library
from smartcard.System import readers

#Get reader list … wait, what is a list?
r=readers()

#Check the length of the list… the what ?
if len(r) == 0:
    print "No available reader"
    exit()

#reader connection
connection = r[0].createConnection()
connection.connect()


### PART 2 (list function) ###

list1 = []
list2 = [4, 2, 6, 10, -3]
list3 = [0, "hello", 3, 10]

list4 = [0, list3, list1, "really?"]
print list4

for item in list2:
    print item


### PART 3 (get firmware version) ###
# Create the message list
mess = [255, 0, 72, 1, 0]

# Transmit the message to the Reader
# Get the returned information in data, sw1 and sw2.
data, sw1, sw2 = connection.transmit(mess)

#Output the data we retrieved
for c in data:
    print chr(c)
print chr(sw1)
print chr(sw2)

#Output the data we retrieved like a boss 
line = ""
for c in data + [sw1, sw2]: # using list combination here, wooot!
    line = line + chr(c)
print line


### PART 4 (polling) ###
# Polling: send tag request
data, sw1, sw2 = connection.transmit([255, 0, 0, 0, 4, 212, 74, 2, 0, 0])

#check error code, don’t ask us why 97
if sw1 != 97:
    print "polling error"
    exit()


#get polling answer
data, sw1, sw2 = connection.transmit([255, 192, 0, 0, sw2])

#check error code # skipped

#Check if the message returned is as full as we’d expect
if len(data) < 3:
    print "That’s weird, we were expecting more data"
    exit()

#is there at least one tag on the reader ?
if data[2] < 1:
    print "no tag on the reader"
    exit()


### PART 5 (transfert function) ###
def sendAndGet(connection, tag_apdu):
    #The chip APDU
    chip_apdu = [212, 64, 1]
    
    #The reader APDU takes into account the combined length
    # of the chip apdu plus the tag apdu
    # It appears in his last element: len(chip_apdu + tag_apdu) 
    reader_apdu = [255, 0, 0, 0, len(chip_apdu + tag_apdu)]
    
    #The whole message :
    mess = reader_apdu + chip_apdu + tag_apdu
    
    #send whole message
    data, sw1, sw2 = connection.transmit(mess)
    
    #retrieve response
    #remember: sw2 gives us the size of the answer to expect
    data, sw1, sw2 = connection.transmit([255, 192, 0, 0, sw2])
    
    # Return the interesting part of the data
    return data[3:]


### PART 6 (hexa function) ###
# part 3.b

#Converting a value into its hexadecimal value
hex(55) # returns the string "Ox37"

#converting an hexadecimal string representation into an int
int("0xA7", 16) # returns the integer 167

#use this to directly write integers in hexadecimal notation
0xA7 # also gives the integer 167


### PART 7 (read data) ###
address = 0x04
data = sendAndGet(connection, [0x30] + address)

string_data = ""
for octet in data:
    string_data += chr(octet)

print string_data


### PART 8 (write data) ###

FIRST_USER_MEMORY_PAGE = 4
LAST_USER_MEMORY_PAGE = 35

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
        print "to chip error:" + str(sw1)
        exit()

    #retrieve response
    data, sw1, sw2 = connection.transmit([0xff,0xC0,0x0,0x0,sw2]) 

    #check error code
    if sw1 != 0x90 and sw2 != 0x00:
        print "get Response error: " + str(sw1) + " " + str(sw2)
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

### PART 9 (Writing a vcard) ###

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
        + "ADR;DOM;PARCEL;HOME:;;4, Privet Drive;Little Whinging;Surrey;;UK\n"
        + "ROLE:student\n"
        + "END:VCARD\n"
        )

# if you are used to python, rewrite the following using slices!
# <ugly warning>you should not program like this in python</ugly warning>

# split vcards characters in blocks of 4 octets
blocks = []
for block_number in range(len(vcard) / 4):
    index = block_number * 4
    blocks += [[ord(vcard[index]), ord(vcard[index+1]), ord(vcard[index+2]), ord(vcard[index+3])]]

# finish last incomplete block if needed
if len(blocks) * 4 != len(vcard):
    # use zeroes to complete last block
    last_block = [0x00, 0x00, 0x00, 0x00]
    # add remaining data
    for index in range(len(blocks) * 4, len(vcard)):
        index_in_last_block = index - len(blocks) * 4
        last_block[index_in_last_block] = [ord(vcard[index])]
    blocks += [last_block]


# verify we will be able to write all in user memory
if len(blocks) > LAST_USER_MEMORY_PAGE - FIRST_USER_MEMORY_PAGE:
    print "vcard is too large for the user memory of the card!"
    print "number of required memory pages: " + str(len(blocks))
    print "number of 4 byte user memory pages: " + str(LAST_USER_MEMORY_PAGE - FIRST_USER_MEMORY_PAGE)
    exit()


# write each block to the card
page_number=4
for block in blocks:
    padding = [0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00] 

    full_apdu = [0xa0, page_number] + block + padding
    transfer(connection, full_apdu)
    page_number += 1
    
print "vcard written"

### PART 10 (Read a vcard from the RFID tag) ###

# dump all the user memory to a string
tag_data = ""
# we can read 4 pages at a time, hence the extra 'step' parameter
sector_numbers = range(FIRST_USER_MEMORY_PAGE, LAST_USER_MEMORY_PAGE + 1, 4)
for sector_number in sector_numbers:
    for octet in transfer(connection, [0x30, sector_number]):
        tag_data += chr(octet)


# stupid vcard parsing algorithm:
# a main loop over the lines
# print lines between the first encountered BEGIN:VCARD END:VCARD
found_vcard = False
for line_with_ending in tag_data.splitlines():
    # remove line_with_ending ending characters
    line = line_with_ending.rstrip("\r\n")

    if line.upper().startswith("BEGIN:VCARD"):
        found_vcard = True
        continue

    if not found_vcard:
        continue

    if line.upper().startswith("END:VCARD"):
        # stop processing if we reached the end of the vcard
        break

    print line

### PART 11 () ###

### PART 12 () ###

