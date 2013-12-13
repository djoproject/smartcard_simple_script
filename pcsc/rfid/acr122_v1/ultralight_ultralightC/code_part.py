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
def send_and_get(connection, tag_apdu):
    #The chip APDU
    chip_apdu = [212, 64, 1]
    
    #The reader APDU takes into account the combined length
    # of the chip apdu plus the tag apdu
    # It appears in his last element: len(chip_apdu + tag_apdu) 
    reader_apdu = [255, 0, 0, 0, len(chip_apdu + tag_apdu)]

    #close message by indicating that we expect data back
    expect_data = [0]
    
    #The whole message :
    mess = reader_apdu + chip_apdu + tag_apdu + expect_data
    
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
data = send_and_get(connection, [0x30] + address)

string_data = ""
for octet in data:
    string_data += chr(octet)

print string_data

def read(connection, address):
    data = send_and_get(connection, [0x30] + address)
    return data
    
def data_to_string(data):
    string_data = ""
    for octet in data:
        string_data += chr(octet)
    return string_data
    
def read_string_on_tag(connection, address):
    return data_to_string(read(connection, address))



### PART 8 (write data) ###

def write_page(connection, address, data_to_write):
    startAddress = 0x4
    endAddress = 0x23
    
    # Exit if we are after the end, or before the start.
    if address > endAddress:
        print "too high address " + str(endAddress)
        exit()

    if address < startAddress:
        print "too low address " + str(endAddress)
        exit()

    # If you want to combine two conditions in a single if
    # you can link them with the keyword and. Try it!
    
    # You write page by page. So you can provide at most 4 bytes of data per call
    if len(data_to_write) > 4:
        print "too much data " + str(data_to_write)
        exit()
    
    #The protocol requires to add 0s to reach 16 bytes
    #missing positions in page to write will also be 0s
    data_to_send = data_to_write
    for i in range(len(data_to_send), 16):
        data_to_send += [0] 
    
    send_and_get(connection, [0xA0] + address + data_to_send)
    # no interesting data returned: this is a write



sector_to_write = 0x4
data = [0x4F, 0x54, 0x53] # intentionally too short
write_page(connection, sector_to_write, data)
print "wrote data: " + read_string_on_tag(sector_to_write)
# data should be the empty list, because no data is sent back from the reader
# this is a read, after all

### PART 9 (Writing a vcard) ###

## Vcard DROPPED!!!
## Still here to test arbitrary length reads


# Vcard basically works like:
# <field name>:<field part 1>;<field part 2>;...

# let's write Harry's

# in python, statements continue until last ([{ is closed
# + using this form (intead of triple-quoted strings) to explicit the line terminator
vcard = ( "BEGIN:VCARD\n"
        + "N:Potter;Harry;;Mr;\n"
        + "ADR;DOM;PARCEL;HOME:;;4, Privet Drive;Little Whinging;Surrey;;UK\n"
        + "ROLE:student\n"
        + "END:VCARD\n"
        )

def write(connection, starting_page, data):
    # write data, page (= 4 bytes) by page

    # range(0, len(data), 4) starts at 0, increments index by 4 until right before reaching len(data). 
    # Ex: [0, 4, 8, 12] if len(data) is 15
    for index in range(0, len(data), 4):

        # start at starting_page and divide by 4 since we write 4 bytes at once
        page = starting_page + index / 4

        # python is pure magic! strings can be sliced too!
        # sequence[slice_start:slice_end]
        page_data = data[index:index+4]

        # write page. Surprised?
        write_page(connection, page, page_data) 


write(connection, 0x4, vcard)        


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

