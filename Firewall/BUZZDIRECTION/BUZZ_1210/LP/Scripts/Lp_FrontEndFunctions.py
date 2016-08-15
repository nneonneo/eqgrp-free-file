#!/usr/bin/env python

import socket
import Lp_UserInterface
import time
import sys

class Lp_FrontEndFcns:
    def __init__(self,sock,lFile):
        self.lpSock=sock
        self.log=lFile
        self.proc = 0

    def setProc(self, processor):
        self.proc = processor

    #Return values:
    #    0: success, if no rpc was created
    #    -1: error occured that does not require the lp to exit
    #    -2: exit lp after returning
    #    else: id number of rpc created by this call
    def cmdGeneric(self,fName, argDict,promptConfirmDict):
        
        command=argDict['command']
        self.lpSock.sendto((command+"\n"),('127.0.0.1',Lp_UserInterface.BACKEND_PORT))
        
        numRpcs=0
        rpcId=-1
        retCode = 0
        
        #If this call did not specify a string to terminate on, set the default
        if ('endOnString' in argDict) == 0 or argDict['endOnString'] == []:
            argDict['endOnString']='DONE'

        #If this call did not provide an error string, set it to []
        if ('errors' in argDict) == 0:
            argDict['errors']={}

        while 1:
            try:
                fromBack=self.__lpRecv(1024)
            except KeyboardInterrupt:
                return -1

            if fromBack==-1:
                if fName=='Core.uninstallForever':
                    print "Did not receive confirmation of uninstallForever."
                    self.log.write("Did not receive confirmation of uninstallForever.\n")
                    return -2
                else:
                    print "Did not receive a response from back end."
                    self.log.write("Did not receive a response from back end.\n")
                    return -1
            elif fromBack.find('SEND')>=0:
                print fromBack,
                sys.stdout.flush()
                rpcId=int(fromBack[fromBack.find('#')+1:fromBack.find(",")])
                if fName == 'Core.load':
                    self.lpSock.sendto('SEND%d,%s:%s'%(rpcId,fName,argDict['modfile']),
                                       ('127.0.0.1',Lp_UserInterface.RPC_DISPATCH_PORT))

                elif fName == 'Core.unload':
                    self.lpSock.sendto('SEND%d,%s:%s'%(rpcId,fName,argDict['iface']),
                                       ('127.0.0.1',Lp_UserInterface.RPC_DISPATCH_PORT))

                else:
                    self.lpSock.sendto('SEND%d,%s:'%(rpcId,fName),
                                       ('127.0.0.1',Lp_UserInterface.RPC_DISPATCH_PORT))
                continue

            #Any function can send a BAD INPUT message, so this is handled
            #explicitly
            elif fromBack.find('BAD INPUT')>=0:
                print fromBack.rstrip(),
                self.log.write(fromBack)
                fromBack=self.__lpRecv(1024)
                print (": "+fromBack)
                self.log.write((": "+fromBack))
                return -1

            #catch any error messages registered by the current function
            elif (fromBack.rstrip() in argDict['errors']):
                try:
                    errorMsg = argDict['errors'][fromBack.rstrip()]
                    if errorMsg != '':
                        print errorMsg
                except KeyError:
                    print fromBack

                retCode = -1
                continue
            elif fromBack.find(str(argDict['endOnString']))>=0:
                if rpcId>0:
                    return rpcId
                else:
                    return retCode
  
            #get the response for this backend prompt from the dictionary, or
            #prompt the user if the dictionary has no entry
            else:
                try:
                    response=argDict[fromBack.rstrip()]
                    if response=="":
                        toDisplay = (fromBack.rstrip()+": ")
                        try:
                            dispStringList = argDict['cursesPrompts']
                            
                            for disp in dispStringList:
                                if (fromBack.rstrip()).find(disp[0])>=0:
                                    toDisplay = disp[1]
                        except KeyError:
                            pass

                        response=raw_input(toDisplay)
                        #Replace empty string with single space to prevent back
                        #end from hanging.
                        if response=='':
                            response=' '
                        self.log.write(toDisplay)
                        self.log.write((response+'\n'))

                    if fromBack.rstrip() in promptConfirmDict:
                        if response==promptConfirmDict[fromBack.rstrip()]:
                            confirm=raw_input('Are you sure you want to send %s for prompt %s?\nY/N: '%
                                              (response, fromBack.rstrip()))
                            if confirm!='y' and confirm!='Y':
                                return -1

                    self.lpSock.sendto((response+"\n"),('127.0.0.1',Lp_UserInterface.BACKEND_PORT))
                    argDict[fromBack.rstrip()]=response

                except KeyError:
                    print "Received an unrecognized response from Back End: %s"%fromBack
                    return -1
                except KeyboardInterrupt:
                    print
                    return -1
        
    def cmdCall(self,printBlock):
      
        while 1:
            print "------------Loaded Modules------------"
            mChoice=self.__getModChoice(printBlock)
    
            if mChoice==0:
                self.cmdGeneric('port',{'command':"!port",'outport':"1338"},{})
                return

            self.cmdGeneric('port',{'command':"!port",'outport':"1336"},{})
            print "----------Available Functions----------"
            fChoice=self.__getFunctionChoice(mChoice)
        
            if fChoice<=0:
                continue
            else:
                break
                
        self.cmdGeneric('port',{'command':"!port",'outport':"1338"},{})
        self.lpSock.sendto("!call\n",('127.0.0.1',1337))
        pattern=["ciface",
                "cprov",
                "cfunc",
                "BAD INPUT"]    
    
        while 1:
            index=-1
            
            index=self.__getPatternIndex(pattern)
                
            if index==-1:
                continue
            elif index==-2:
                break
            elif index==0:
                self.lpSock.sendto((str(mChoice)+"\n"),('127.0.0.1',1337))
                continue
            elif index==1:
                self.lpSock.sendto("1\n",('127.0.0.1',1337))
                continue
            elif index==2:
                self.lpSock.sendto((str(fChoice)+"\n"),('127.0.0.1',1337))
                break
            elif index==3:
                self.__printBadInput()
                break
        
        res=self.__handlePrompts()        
        return res    
            
    def __getPatternIndex(self,pattern):
        fromBack=self.__lpRecv(1024)
        if fromBack==-1:
            print "Did not receive a response from back end."
            return -2

        for entry in pattern:
            if fromBack.find(entry)>=0:
                index=pattern.index(entry)
                return index
    
    def __getModChoice(self,printBlock):
    
        res = self.cmdGeneric('mods',{'command':'!mods'},{})
        printBlock.sendto('!!#REG_BLOCK%d'%res,('127.0.0.1',Lp_UserInterface.RPC_DISPATCH_PORT))
        result = printBlock.recv(1024)
            
        print "Enter 0 to return."
        
        while 1:
            mChoice=raw_input("Enter Module Choice: ")
            try:
                mChoice=int(mChoice)
            except ValueError:
                print "Invalid module selection."
                continue
            
            if mChoice>=0:
                return mChoice
            else:
                print "Invalid module selection."
                continue
    
    def __getFunctionChoice(self,modChoice):
        fCount=-3
        self.lpSock.sendto("!list\n",('127.0.0.1',1337))
        pattern=["iface",
                "prov",
                "BAD INPUT"]    
        
        while 1:
            index=-1
            
            index=self.__getPatternIndex(pattern)
                
            if index==-1:
                continue
            elif index==-2:
                break
            elif index==0:
                self.lpSock.sendto((str(modChoice)+"\n"),('127.0.0.1',1337))
            elif index==1:
                self.lpSock.sendto("1\n",('127.0.0.1',1337))
                line=self.__lpRecv(1024)
                if line==-1:
                    return line
                while line.find("func")<0:
                    line=self.__lpRecv(1024)
                    if line==-1:
                        return line
                while line.find("DONE")<0:
                    fCount+=1
                    print line,
                    line=self.__lpRecv(1024)
                    if line==-1:
                        return line
                    
                if fCount<1:
                    print "No Available Functions."
                    raw_input("Press Enter to return to modules")
                    return -1
                print "Enter 0 to return to modules."
                break
            elif index==2:
                self.__printBadInput()
                return -1
                
        while 1:
            fChoice=raw_input("Enter Function Choice: ")
            try:
                fChoice=int(fChoice)
            except ValueError:
                print "Invalid function selection."
                continue
            
            if fChoice>=0:
                return fChoice
            else:
                print "Invalid module selection."
                continue    
    
    def __handlePrompts(self):
        line=self.__lpRecv(1024)
        if line==-1:
            return line
        rpcNum=0
        while line.find("DONE")<0:
            
            if line.find("BAD INPUT")>=0:
                print line,
                line=self.__lpRecv(1024)
                if line==-1:
                    return line
                continue
            elif line.find("bad file")>=0:
                print line,
                line=self.__lpRecv(1024)
                return -1
            elif line.find('SEND')>=0:
                print line,
                rpcNum=line[line.find('#')+1:line.find(',')]
                rpcNum=int(rpcNum)
                line=self.__lpRecv(1024)
                continue
            elif line.find("Route")>=0 or line.find("SEND")>=0:
                print line,
                line=self.__lpRecv(1024)
                if line==-1:
                    return line
                continue
                
            res=raw_input(line.rstrip()+": ")
            if res=="":
                continue
            self.lpSock.sendto((res+"\n"),('127.0.0.1',1337))
            line=self.__lpRecv(1024)
            if line==-1:
                return line
                
        return rpcNum
    
    def __lpRecv(self,bytes):
        try:
            line=self.lpSock.recv(bytes)
            return line
        except socket.timeout:
            print "Socket timed out."
            return -1
    
    def __printBadInput(self):
        print "Bad Input: ",
        badInVar=self.lpSock.recv(1024)
        
        print badInVar
        
