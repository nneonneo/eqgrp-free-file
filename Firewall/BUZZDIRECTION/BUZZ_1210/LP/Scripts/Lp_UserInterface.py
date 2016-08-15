#!/usr/bin/env python

import Lp_FrontEndFunctions
import Lp_CursesDriver
import Lp_XmlParser
import Lp_RpcDispatcher
import Lp_InputProcessing
import Lp_Defines

import shutil
import os
import sys
import socket
import time
import subprocess
import signal
import platform
import threading
from datetime import datetime

BLOCKER_PORT      = Lp_Defines.BLOCKER_PORT
RPC_DISPATCH_PORT = Lp_Defines.RPC_DISPATCH_PORT
PRINT_PORT        = Lp_Defines.PRINT_PORT
BACKEND_PORT      = Lp_Defines.BACKEND_PORT
FRONTEND_PORT     = Lp_Defines.FRONTEND_PORT

#Prints anything recieved from the backend on port 1338.  If an rpc
#confirmation is received, it sends the confirmation to the RPC Dispathcher. 
class PrintThread(threading.Thread):
    def __init__(self,processor,lFile):
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1',PRINT_PORT))
        self.sock.settimeout(.1)
        self.cmdLoop=processor
        self.log=lFile
        
        threading.Thread.__init__(self)
        
    def run(self):
        
        while 1:
            try:
                stringIn,addr=self.sock.recvfrom(1024)
                if stringIn.find('RECV')>=0:
                    self.sock.sendto(stringIn,('127.0.0.1',RPC_DISPATCH_PORT))
                elif stringIn == '!!#QUIT':
                    break
                else:
                    print stringIn,
                    self.log.write(stringIn)
                sys.stdout.flush()
            except:
                continue
        self.sock.close()
   
#Forces backend to ignore TERM signals sent to the front end on ctrl-c
def preexec_fcn():
    signal.signal(signal.SIGINT,signal.SIG_IGN)    

def setInitialOpenArgs(args):
    args['command'] = '!open'
    args['dstip'] = sys.argv[1]
    args['dstport'] = sys.argv[2]
    args['srcip'] = sys.argv[3]
    args['srcport'] = sys.argv[4]
    args['keyfile'] = sys.argv[5]
    args['endOnString'] = 'DONE'

def setLpexArgs(args,file):
    args['lpexfile'] = file

def setPortArgs(args,portNum):
    args['outport'] = str(portNum)

def loadLpexes(func,curDir,lpArch,proc):
    lpexPathList = []
    alreadyLoaded = []

    baseDir = os.path.join(curDir,'../Mods/App/')
    baseList = os.listdir(baseDir)
    
    archlist = []
    archents = []
    for subDir in baseList:
        archlist = os.listdir(os.path.join(baseDir,subDir))
        for arch in archlist:
            archents = os.listdir(os.path.join(baseDir,subDir,arch))
            for ent in archents:
                lpexPathList.append(os.path.join(baseDir,subDir,arch,ent))

    if lpArch == 'i386':
        lpexExtension = '.lx32'
    else:
        lpexExtension = '.lx64'
        
    lpexArgs = proc.Modules['Lp']['Lp.lpex']
    for lpex in lpexPathList:
        lpexName = lpex.split('/')[-1]
        if lpex.find(lpexExtension)>=0 and not lpexName in alreadyLoaded:
            print "%s..."%lpexName,
            setLpexArgs(lpexArgs,lpex)
            res = func.cmdGeneric('lpex',lpexArgs,{})
            if res ==0:
                print "done"
            else:
                print "failed"

            alreadyLoaded.append(lpexName)

    print ""
 
#Connects and prints the currently loaded modules and uptime.
#Arguments:
#    proc: the Lp Input Processing object
#    func: the Lp Front End Functions object
#    sock: the socket used to communicate with backend
#    outfile: the Lp log file
#    lpArch: the Lp architecture
#Return:
#    1 on success
#    -1 in fail
def showWelcome(proc,func,sock,outFile,lpArch):
    currentDirectory=os.getcwd()
    supportedArchs={'062':'x86_64','003':'i386','020':'ppc','021':'ppc64',
                    '002':'sparc','008':'mips_be','010':'mips_le',
                    '040':'arm','043':'sparcv9'}

    openArgs = proc.Modules['Lp']['Lp.open']
    setInitialOpenArgs(openArgs)

    res = func.cmdGeneric('open',openArgs, {})
    if res < 0:
        print "Failed to connect."
        return -1

    try:
        line=sock.recv(1024)
    except:
        print "Failed to connect."
        return -1

    lpexList = []
    allArches = []

    #load all lp extention files available
    print "Loading Lp Extensions:"
    loadLpexes(func,currentDirectory,lpArch,proc)
       
    #Parse xml files for preloaded modules and print currently loaded modules
    portArgs = proc.Modules['Lp']['Lp.port']
    setPortArgs(portArgs, FRONTEND_PORT)
    res = func.cmdGeneric('port',portArgs,{})
    if res != 0:
        print "Failed to set the output port."
        return -1

    res=func.cmdGeneric('mods',proc.Modules['Lp']['Lp.mods'],{})
    modsToParse = []
    
    print "******************Loaded Modules*****************",
    try:
        line=sock.recv(1024)
        while line.find("RECV")<0:
            print line,
            outFile.write(line)
            if line.find('name')<0 and line.find('--')<0 and line.find("Device")<0:
                modName=line[8:25]
                modName=modName.strip()
                module=(modName+'.mo')
                if len(module)>3:
                    modsToParse.append(module)
                if modName=='PlatCore':
                    platCoreArch=line[46:len(line)].strip()
                    try:
                        proc.setArch(supportedArchs[platCoreArch])
                    except KeyError:            
                        print "The reported architecture type of %s is not supported."%platCoreArch
                        
                        return -1

            line=sock.recv(1024)
                  
    except socket.timeout:
        print "Failed to receive module list."
        outFile.write("Failed to receive module list.")
        return -1
    except KeyboardInterrupt:
        return -1

    for module in modsToParse:
        proc.parseXml(module,0)

    portArgs = proc.Modules['Lp']['Lp.port']
    setPortArgs(portArgs, PRINT_PORT)
    res = func.cmdGeneric('port',portArgs,{})
    if res < 0:
        print "Failed to set the output port."
        return -1

    try:
        res = func.cmdGeneric('uptime',proc.Modules['Core']['Core.uptime'],{})
    except KeyError:
        print "Error: Core module xml not parsed correctly.  Uptime function was not found."
        return -1
    if res < 0:
        print "Failed to send the initial uptime command."
        return -1

    proc.printBlocker.sendto('!!#REG_BLOCK%d'%res,('127.0.0.1',RPC_DISPATCH_PORT))
    result = proc.printBlocker.recv(1024)

    return 1

if __name__=='__main__':
    try:
        functions=0
        processor=0
        printThread=0
        log=0
        lpSock=0
        out=0
        ark=platform.architecture()[0]
        if ark=='32bit':
            lpArk='i386'
        else:
            lpArk='x86_64'
        curDir=os.getcwd()
        out=open((curDir+'/back.log'),'w+')
        
        try:
            logFiles=os.listdir('%s/Logs'%os.getcwd())
        except OSError:
            os.mkdir('%s/Logs'%curDir)
            logFiles=os.listdir('%s/Logs'%os.getcwd())
            
        numLogs=len(logFiles)
        logFiles.sort()
        
        #If there are more than 20 log files, delete the oldest one.
        if numLogs>20 and sys.argv[6]=='1':
            try:
                os.remove('%s/Logs/%s'%(curDir,logFiles[0]))
            except OSError:
                print "Unable to remove oldest logfile."
        
        date='%s'%datetime.date(datetime.now())
        cTime='%s'%datetime.time(datetime.now())
        cTime=cTime[:cTime.find('.')]
        logname='%s_%s_lp.log'%(date,cTime)
        log=open('%s/Logs/%s'%(curDir,logname),'w+')

        lpSock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        lpSock.bind(('127.0.0.1',FRONTEND_PORT))

        try:
            oldBack = os.path.join(curDir,lpArk,'Backend.lp')
            newBack = os.path.join(curDir,lpArk,'Backend.running')
            shutil.copy(oldBack,newBack)
            backRet = subprocess.call([newBack],
                                       stdout=out,preexec_fn=preexec_fcn)
        except IOError:
            print "Unable to locate back end executatble.  This should be located in Lp/<LP Architecture>"
            out.close()
            ThreadExit=0
            lpSock.close()
            sys.exit(-1)

        if backRet != 0:
            print "Back end failed to execute correctly.  Return code: 0x%x"%backRet
            out.close()
            ThreadExit=0
            lpSock.close()
            sys.exit(-1)

        time.sleep(1)

        functions=Lp_FrontEndFunctions.Lp_FrontEndFcns(lpSock,log)

        processor=Lp_InputProcessing.InputProcessor(functions,log,lpArk,lpSock)
        processor.parseXml('Lp.mo',0)
        processor.setDefaultOutDir()

        functions.setProc(processor)
                
        printThread=PrintThread(processor,log)
        printThread.daemon=True
        printThread.start()

        rpcDispatch=Lp_RpcDispatcher.RpcDispatcher(processor)
        rpcDispatch.start()
        
        lpSock.sendto("!!#TURN_ON_PRINTING",('127.0.0.1',RPC_DISPATCH_PORT))

        res=showWelcome(processor,functions,lpSock,log,lpArk)
        if res>0:
            processor.cmdloop()
        else:
            res = functions.cmdGeneric('term',{'command':'!term','endOnString':'DONE'},{})
            if res < 0:
                print "Failed to send term command on exit.  Session may still be open."

        lpSock.sendto("!!#QUIT",('127.0.0.1',RPC_DISPATCH_PORT))
        lpSock.sendto("!!#QUIT",('127.0.0.1',PRINT_PORT))
        subprocess.call(['killall','Backend.running'])
        os.remove(newBack)
        out.close()
        log.close()
        lpSock.close()
    except KeyboardInterrupt:
        if functions!=0:
            res=functions.cmdGeneric('term',{'command':'!term','endOnString':'DONE'},{})
        if out !=0:
            try:
                out.close()
            except IOError:
                pass
            
        print "Goodbye"
        if log!=0:
            log.write('Goodbye\n')
            log.write('Session terminated at %s'%str(datetime.now()))
            log.close()
        lpSock.sendto("!!#QUIT",('127.0.0.1',RPC_DISPATCH_PORT))
        lpSock.sendto("!!#QUIT",('127.0.0.1',PRINT_PORT))
        subprocess.call(['killall','Backend.running'])
        os.remove(newBack)
        if lpSock != 0:
            lpSock.close()

