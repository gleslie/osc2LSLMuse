
#!/usr/bin/env python
import os, sys, inspect
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = '../lib/x64' if sys.maxsize > 2**32 else '../lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

import socket, OSC, re, time, threading, math

from pylsl import StreamInfo, StreamOutlet

# first create a new stream info (here we set the name to Muse-EEG, the content-type to EEG, 6 channels, 500 Hz, and float-valued data)
# The last value would be the serial number of the device or some other more or less locally unique identifier for the stream as far as available (you could also omit it but interrupted connections wouldn't auto-recover).
info = StreamInfo('Muse-EEG','EEG',6,500,'float32','MuseModel');
# next make an outlet
outlet = StreamOutlet(info)

receive_address = '127.0.0.1', 5001 #Mac Adress, Outgoing Port
send_address = '127.0.0.1', 9000 #iPhone Adress, Incoming Port

class PiException(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

##########################
#	OSC
##########################

# Initialize the OSC server and the client.
s = OSC.OSCServer(receive_address)
c = OSC.OSCClient()
c.connect(send_address)

s.addDefaultHandlers()

# define a message-handler function for the server to call.
def test_handler(addr, tags, stuff, source):
	print "---"
	print "received new osc msg from %s" % OSC.getUrlStr(source)
	print "with addr : %s" % addr
	print "typetags %s" % tags
	print "data %s" % stuff
	msg = OSC.OSCMessage()
	msg.setAddress(addr)
	msg.append(stuff)
	c.send(msg)
	print "return message %s" % msg
	print "---"

def museEEG_handler(add, tags, stuff, source):
    mysample = [stuff[0],stuff[1],stuff[2],stuff[3],stuff[4],stuff[5]]
    outlet.push_sample(mysample)

def junk_handler(add, tags, stuff, source):
    pass


# adding my functions
s.addMsgHandler("/muse/eeg", museEEG_handler)
s.addMsgHandler("/muse/eeg/quantization", junk_handler)
s.addMsgHandler("/muse/config", junk_handler)
s.addMsgHandler("/muse/version", junk_handler)
s.addMsgHandler("/muse/acc", junk_handler)
s.addMsgHandler("/muse/batt", junk_handler)
# just checking which handlers we have added
print "Registered Callback-functions are :"
for addr in s.getOSCAddressSpace():
	print addr

# Start OSCServer
print "\nStarting OSCServer. Use ctrl-C to quit."
st = threading.Thread( target = s.serve_forever )
st.start()

# Loop while threads are running.
try :
	while 1 :
		time.sleep(10)
 
except KeyboardInterrupt :
	print "\nClosing OSCServer."
	s.close()
	print "Waiting for Server-thread to finish"
	st.join()
	print "Done"