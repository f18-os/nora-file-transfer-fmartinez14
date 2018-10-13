#! /usr/bin/env python3
import sys, os, socket, params, time
from threading import Thread
from threading import Lock
import threading
from framedSock import FramedStreamSock

switchesVarDefaults = (
    (('-l', '--listenPort') ,'listenPort', 50001),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

progname = "echoserver"
paramMap = params.parseParams(switchesVarDefaults)

debug, listenPort = paramMap['debug'], paramMap['listenPort']

if paramMap['usage']:
    params.usage()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # listener socket
bindAddr = ("127.0.0.1", listenPort)
lsock.bind(bindAddr)
lsock.listen(5)


print("listening on:", bindAddr)

class ServerThread(Thread):
    requestCount = 0            # one instance / class
    test=0
    openFiles= {}
    def __init__(self, sock, debug):
        Thread.__init__(self, daemon=True)
        self.fsock, self.debug = FramedStreamSock(sock, debug), debug
        self.start()
    def run(self):
        currBuf = ""
        bufferIsComplete = False
        file_name= ""
        protocol= ""
        while True:
            payload = self.fsock.receivemsg()
            if not payload:
                if self.debug: print(self.fsock, "server thread done")
                return
            requestNum = ServerThread.requestCount
            # time.sleep(2)
            ServerThread.requestCount = requestNum + 1

            if not file_name: #If file name is empty, that means we are recieving parameters.
                tempVar = payload.decode()
                protocol, file_name = tempVar.split(" ")
                print(protocol + " " + file_name)
                self.fsock.sendmsg(payload)


            if protocol == "PUT":
                try:
                    getLock = self.openFiles[file_name]
                except:
                    self.openFiles[file_name] =  threading.Lock()
                with self.openFiles[file_name]:
                    ServerThread.test += 1;
                    while not bufferIsComplete:
                        tempStr = self.fsock.receivemsg()
                        sendBack = tempStr #Same logic as client , recieve the information until the delimeter or the buffer is less than 100.
                        tempStr = tempStr.decode()
                        print("Recieved: " + tempStr + " " + str(len(tempStr)))
                        if " !@#___!@# " in tempStr:
                            writeFile, delimeter = tempStr.split(" !@#___!@# ")
                            currBuf += writeFile
                            bufferIsComplete = True
                        if len(tempStr) < 100:
                            bufferIsComplete = True
                        else:
                            currBuf += tempStr
                            tempStr = ""

                        self.fsock.sendmsg(sendBack)

                    if currBuf and protocol == "PUT": #Write to file once buffer is complete.
                        print(file_name + " writing:" + currBuf)
                        with open("filesFolder/server/" + file_name, 'a+') as outputFile:
                            outputFile.write(currBuf)
                        currBuf = ""
                        outputFile.close()


            elif protocol== "GET": #Read file same as client and send 100 bytes at a time.
                try:
                    getLock = self.openFiles[file_name]
                except:
                    self.openFiles[file_name] =  threading.Lock()
                with self.openFiles[file_name]:
                    print(str(ServerThread.test) + " get")
                    with open("filesFolder/server/" + file_name, 'r') as outputFile:
                        currBuf += outputFile.read().strip()
                    outputFile.close()
                    currBuf += " !@#___!@# "
                    while currBuf:
                        sendMe = currBuf[:100]
                        print("sending: " + sendMe + " " + str(len(sendMe)))
                        self.fsock.sendmsg(str.encode(sendMe))
                        tempVar = self.fsock.receivemsg()
                        bytesToMove = len(tempVar.decode())
                        print("got back:" + tempVar.decode())
                        currBuf = currBuf[bytesToMove:] #Move buffer  by the amount of bytes recieved.
                    print("Sucessfully sent file.")

        print("Connection Terminated")

            # msg = ("%s! (%d)" % (msg, requestNum)).encode()
            # self.fsock.sendmsg(msg)


while True:
    sock, addr = lsock.accept()
    ServerThread(sock, debug)
