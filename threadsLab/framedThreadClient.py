#! /usr/bin/env python3

# Echo client program
import socket, sys, re
import params
from framedSock import FramedStreamSock
from threading import Thread
import time


switchesVarDefaults = ( #Default parameters
    (('-s', '--server'), 'server', "127.0.0.1:50001"),
    (('-f', '--fileName') , 'file_name', "fileFromClient.txt"),
    (('-p', '--protocol') , 'protocol', "PUT"),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )


progname = "framedClient"
paramMap = params.parseParams(switchesVarDefaults)

server, file_name, protocol, usage, debug  = paramMap["server"], paramMap["file_name"], paramMap["protocol"], paramMap["usage"], paramMap["debug"]
#Default variables and parameters.


if usage:
    params.usage()


try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)

class ClientThread(Thread):
    def __init__(self, serverHost, serverPort, debug):
        Thread.__init__(self, daemon=False)
        self.serverHost, self.serverPort, self.debug = serverHost, serverPort, debug
        self.start()
    def run(self):
       s = None
       currBuf = ""
       bufferIsComplete = False
       for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
           af, socktype, proto, canonname, sa = res
           try:
               print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
               s = socket.socket(af, socktype, proto)
           except socket.error as msg:
               print(" error: %s" % msg)
               s = None
               continue
           try:
               print(" attempting to connect to %s" % repr(sa))
               s.connect(sa)
           except socket.error as msg:
               print(" error: %s" % msg)
               s.close()
               s = None
               continue
           break

       if s is None:
           print('could not open socket')
           sys.exit(1)

       fs = FramedStreamSock(s, debug=debug)
       print(protocol + " " + file_name) #Prints and send commands.
       sendParameters = protocol + " " + file_name
       fs.sendmsg(str.encode(sendParameters))
       allSet = fs.receivemsg()

       try:
           if protocol == "PUT":
               with open("filesFolder/client/" + file_name, 'r') as outputFile:
                   currBuf += outputFile.read()
               outputFile.close() #Writes to buffer and closes file. Adding delimeter at end.
               currBuf += " !@#___!@# "
               while currBuf:
                   sendMe = currBuf[:100]
                   print("sending: " + sendMe + " " + str(len(sendMe))) #Sends packets at 100 bytes at a time and then closes the socket. Move buffer by the amount of bytes recieved back.
                   fs.sendmsg(str.encode(sendMe))
                   tempVar = fs.receivemsg()
                   bytesToMove = len(tempVar.decode())
                   print("got back:" + tempVar.decode())
                   currBuf = currBuf[bytesToMove:]

               # s.close()
               print("Sucessfully sent file.")

           elif protocol== "GET":
               while not bufferIsComplete:
                   tempStr = fs.receivemsg()
                   sendBack = tempStr
                   tempStr = tempStr.decode() #Recieve the information until the buffer is complete.
                   print("Recieved: " + tempStr + " " + str(len(tempStr)))
                   if " !@#___!@# " in tempStr:
                       writeFile, delimeter = tempStr.split(" !@#___!@# ")
                       currBuf += writeFile #if delimeter is found, stop.
                       bufferIsComplete = True
                   if len(tempStr) < 100: #Or if buffer is less than a 100.
                       bufferIsComplete = True
                   else:
                       currBuf += tempStr

                   fs.sendmsg(sendBack)

               if currBuf and protocol == "GET":
                   print(file_name + " writing:" + currBuf)
                   with open("filesFolder/client/" + file_name, 'a+') as outputFile:
                       outputFile.write(currBuf)
                   currBuf = "" #Write to file once sending from server is complete.
                   outputFile.close()
       except Exception as e:
           print(e)
           # print("There has been an error, please try again with an existing file.")

       # print("sending hello world")
       # fs.sendmsg(b"hello world")
       # print("received:", fs.receivemsg())
       #
       # fs.sendmsg(b"hello world")
       # print("received:", fs.receivemsg())

for i in range(1):
    ClientThread(serverHost, serverPort, debug)
