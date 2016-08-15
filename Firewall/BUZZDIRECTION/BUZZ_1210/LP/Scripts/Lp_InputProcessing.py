
import Lp_XmlParser
import Lp_Defines
import Lp_CursesDriver
from datetime import datetime
import socket
import textwrap
import time
import sys
import os
import cmd

BLOCKER_PORT      = Lp_Defines.BLOCKER_PORT
RPC_DISPATCH_PORT = Lp_Defines.RPC_DISPATCH_PORT
PRINT_PORT        = Lp_Defines.PRINT_PORT
BACKEND_PORT      = Lp_Defines.BACKEND_PORT
FRONTEND_PORT     = Lp_Defines.FRONTEND_PORT

#Parses input and executes the appropriate command.
class InputProcessor(cmd.Cmd):
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
        self.globalCount = 0

        self.functionList = ['quit','exit']
        
        cmd.Cmd.__init__(self)

    def setDefaultOutDir(self):
        self.defaultOutDir = Lp_XmlParser.parseDefaultDir()
    
    def preloop(self):
        self.logFile.write(self.prompt)
        self.do_help("")
                    
    #This function is executed immediatly before the command entered by the user is handled by the
    #cmd class.  For a command that is a key in the function dictionary, the user input is handled
    #by the genericCmd function.
    #Arguments:
    #   line: The string entered by the user
    #Return:
    #   The name of the cmd class function to call.  If the call is a known
    #   function, then '' is returned, since the function call was already handled.
    def precmd(self,line):

        #Hardcoded check to prevent abort from being called by user
        if line.find('abort')==0:
            print "*** Unknown syntax: %s"%line
            return ""

        self.logFile.write("%s %s\n"%(self.prompt,line))
        usrIn=line.split(" ")
        
        if usrIn[0].find(".")<=0:
            return line

        fName=self.__resolveFuncName(usrIn[0])

        if fName=='quit':
            return 'quit'
         
        for mod in self.Modules:
            #Is the commanded function a key in the dictionary for the module 'mod'?
            if fName in self.Modules[mod]:
                oldDict={}
                oldDict=self.Modules[mod][fName].copy()
                cmdRes=self.genericCmd(mod,usrIn)

                if cmdRes>=0 and fName=='Core.uninstallForever':
                    self.lpSock.settimeout(60)
                    try:
                        burnConf = self.lpSock.recv(1024)
                        while burnConf.find('RECV RPC')<0:
                            burnConf = self.lpSock.recv(1024)

                        retCode = burnConf[burnConf.find('rc=')+3:len(burnConf)-1]
                        if retCode == '0':
                            print "uninstallForever Successful"
                            self.logFile.write("uninstallForever Successful.\n")
                            return 'abort'
                        else:
                            print "uninstallForever rpc returned an error: %s"%retCode
                            self.lpSock.setblocking(1)
                            return ''
                        
                    except socket.timeout:
                        print "Did not receive confirmation of uninstallForever."
                        self.logFile.write("Did not receive confirmation of uninstallForever.\n")
                        self.lpSock.setblocking(1)
                        return 'abort'
            
                elif cmdRes>=0 and fName=="Core.upgrade":
                    upgradeRes = self.handleUpgrade(cmdRes)

                    #if the upgrade failed and upgradeRes is an rpc error
                    #code, don't terminate the LP.  This is bad, so the user may 
                    #want to try something else before exiting.
                    if upgradeRes == 'abort':
                        return upgradeRes

                if cmdRes == -2:
                    line = 'abort'
                    break

                self.Modules[mod][fName]=oldDict
                return ""
            
        return line

    #Removes a module from the module dictionary after a successful unload.
    #Arguments:
    #   toUnload: the iface number of the module to delete
    #   okToDelete: rpc result number from the unload rpc.  Must be 0 to delete
    #               the module
    #Return:
    #   none
    def deleteMod(self,toUnload,okToDelete):
        if okToDelete > 0:
            return
        keys=self.Modules.keys()
        for key in keys:
            if self.Modules[key]['iface'] == toUnload[0]:
                for fName in self.Modules[key].keys():
                    try:
                        self.functionList.remove(fName)
                    except ValueError:
                        #dont worry if it wasnt in the list.  the Modules[key]
                        #dictionary may have keys other than the function names
                        pass
                    
                del self.Modules[key]
                del self.helpDict[key]

    #Prints the command that can be used to create a tunnel via the command line.
    #Arguments:
    #   tunnelCommand: the command string to create a tunnel via the command
    #                  line.
    #   okToPrint: the result of the tunnel creation rpc.  Must be 0 to print.
    #Return:
    #   none
    def printTunnelCmd(self,tunnelCommand,okToPrint):
        if okToPrint==0:
            print tunnelCommand[0]

    def get_names(self):
        return self.functionList

    def completenames(self, text, *ignored):
        return [a for a in self.get_names() if a.startswith(text)] 
    
    #Handles user input if the commanded function has an entry in the function dictionary.
    #Arguments:
    #    mod:  the module that contains this function
    #    usrIn:  raw input that the user entered at the command prompt
    #Return:
    #    -1 if an error occured while executing the command, but the Lp should
    #       not exit
    #    -2 if an error occured and the LP should now exit
    #    0 if no error occured
    #    rpc error number if an rpc error occured.
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
                    return -1
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
            
        if self.Modules[mod][fName]['curses']=="true" and len(usrIn)==1:
            return self.handleCursesForm(usrIn, fName, mod)

        if self.Modules[mod][fName]['useDirList']=='1' and len(usrIn)==1:
            res = self.handleDirListing(fName,mod)
            if 0 != res:
                return res

        if self.Modules[mod][fName]['useSwitch']=='1' and len(usrIn)==1:
            res = self.handleSwitch(fName,mod)
            if 0 != res:
                return res
           
        if self.Modules[mod][fName]['printFunc'] != [] and len(usrIn)==1:
            self.printFunctionOut(self.Modules[mod][fName]['printFunc'])

        if self.Modules[mod][fName]['useDefaultDir'] != [] and len(usrIn) == 1:
            argument = self.Modules[mod][fName]['useDefaultDir']     
            self.Modules[mod][fName][argument] = self.defaultOutDir

        if self.Modules[mod][fName]['useBubblewrapXml'] == '1':
            path = raw_input(self.Modules[mod][fName]['bubblePrompt'])
            res = Lp_XmlParser.parseBubblewrapXml(path,self.Modules[mod][fName])
            if res == -1:
                print "Error parsing the provided Bubblewrap xml."
                return res

        if self.Modules[mod][fName]['checkForCfg'] == '1':
            res = self.handleLoadConfig(fName, mod)
            if 0 != res:
                return res

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

    def printTree(self,base,dict,di,map):
        try:
            vals = dict.keys()
            for val in vals:
                print di*'\t'+val
                if os.path.isdir(os.path.join(base,val)):
                    for dt in dict[val]:
                        self.printTree(os.path.join(base,val),dt,di+1,map)
        except AttributeError:
            print di*'\t'+str(self.globalCount)+': '+dict
            map[self.globalCount] = os.path.join(base,dict)
            self.globalCount = self.globalCount+1

    def recurseDir(self, dir, dict, depth, ex):
        ents = os.listdir(dir)
        dict[dir.split('/')[-1]] = []
        for ent in ents:
            if os.path.isdir(os.path.join(dir,ent)):
                newDict = {ent:[]}
                dict[dir.split('/')[-1]].append(newDict) 
                self.recurseDir(os.path.join(dir,ent),newDict,depth+1, ex)
            else:
                if ent.find(ex)>=0:
                    dict[dir.split('/')[-1]].append(ent) 

    def buildListing(self, baseDir, recurse, ex):
        dirListing={}
        dirListing[baseDir] = []
        subDirs = os.listdir(baseDir)
        for item in subDirs:
            if os.path.isdir(os.path.join(baseDir,item)) and recurse == '1':
                self.recurseDir(os.path.join(baseDir,item),dirListing,1,ex)
            else:
                dirListing[baseDir].append(item)

        return dirListing
        
    #Handles loading a module config before loading a module.  Looks in the same directory
    #as the module for a file called <modname>.cfg.  If it exists, calls the lcfg backend
    #command.  The module loading blocks until lcfg returns
    #Arguments:
    #   fName:  the name of the function the user is trying to execute
    #   mod:    the name of the module that provides fName
    #Return:
    #    0: success
    #    -1: error occured
    def handleLoadConfig(self,fName,mod):
        #See if the modules dir has <modname>.cfg
        #Note that for now this flag will only be set for load commands
        #modfile key was previously set in the dirlisting
        pathToMod = self.Modules[mod][fName]['modfile']
        modName = pathToMod.split('/')[-1]
        cfgName = modName[:-3]+'.cfg'
        dirToList = pathToMod[:pathToMod.rfind('/')]
        listing = os.listdir(dirToList)
        for f in listing:
            if f == cfgName:
                nameSplit = modName.split('_')
                modName=nameSplit[0]
                iface=Lp_XmlParser.parseIface(modName,self.architecture, self.lpArch)
                major = nameSplit[1].split('.')
                major = major[0]
                lcfgArgs = {'command':'!lcfg','cfg':os.path.join(dirToList,cfgName),
                            'major':major,'iface':str(iface)}
                res = self.functions.cmdGeneric('lcfg',lcfgArgs,{})
                if res < 0:
                    print "Failed to load the module config file:\n%s"%os.path.join(dirToList,cfgName)
                    return res

                self.printBlocker.sendto('!!#REG_BLOCK%d'%res,('127.0.0.1',RPC_DISPATCH_PORT))
                result = self.printBlocker.recv(1024)

        return 0

    #Handles setting multiple function parameters based on a single user input.  Switch options
    #are pulled from the function xml.
    #Arguments:
    #   fName:  the name of the function the user is trying to execute
    #   mod:    the name of the module that provides fName
    #Return:
    #    0: success
    #    -1: error occured
    def handleSwitch(self,fName,mod):
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
                            return -1
                    break

            return 0

        except KeyboardInterrupt:
            print
            return -1
           
    #Handles setting a function argument using a directory listing.  If the recurse option is set
    #in the function xml, it will generate a recursive listing starting at the baseDir.  If the 
    #showIfaceNumber option is set, it will list a module's number as the required input to 
    #select a module.  Otherwise, it will list directory items serialy and the user inputs the
    #appropriate number.  The parameter specifed as promptToSet in the function xml will be set to
    #the full path to the selected directory entry.
    #Arguments:
    #   fName:  the name of the function the user is trying to execute
    #   mod:    the name of the module that provides fName
    #Return:
    #    0: success
    #    -1: error occured
    def handleDirListing(self,fName,mod):
        try:
            dirListParams=self.Modules[mod][fName]['dirListParams']
            directory=dirListParams['baseDir']
            if dirListParams['prependCWD']=='1':
                directory='%s%s'%(os.getcwd(),directory)

            dirListing = self.buildListing(directory,dirListParams['recurse'],dirListParams['fileEx'])
            moduleIndexes={}
            while 1:
                print dirListParams['prePrint']
                try:
                    if dirListParams['showIfaceNumbers']=='1':            
                        if dirListParams['appendImplantArch']=='1':
                            archStr = self.architecture
                        else:
                            archStr = ''

                        projects = dirListing.keys()
                        for project in projects:
                            if len(dirListing[project]) > 0:
                                print "%s:"%project
                            arches = dirListing[project]
                            for archDict in arches:
                                thisArch = archDict.keys()[0]
                                if thisArch == self.architecture:
                                    for module in archDict[thisArch]:
                                        modName=module.split(dirListParams['modNameSplitChar'])[0]
                                        iface=Lp_XmlParser.parseIface(modName,self.architecture, self.lpArch)
                                        if iface<0:
                                            print "Unable to find iface number for %s."%modName
                                            print "Ensure the xml file for this module is located in the proper directory."
                                        else:
                                            print "\t%d: %s"%(iface,module)

                                            #Create the mapping of iface number to path to module 
                                            #This allows user to enter iface number to select mod
                                            moduleIndexes[iface]=os.path.join(directory,project,thisArch,module)
                                            
                    else:
                        self.printTree(directory,dirListing,0,moduleIndexes)
                        self.globalCount = 0

                    input=raw_input(dirListParams['listPrompt'])
                    input = int(input)
                    selection=moduleIndexes[input]
                    self.Modules[mod][fName][dirListParams['promptToSet']]=selection
                    break

                except (IndexError, ValueError, KeyError):
                    print "\nInvalid selection.\n"

            if dirListParams['requireXml']=='1':
                modStripped = selection.split('/')[-1]
                path = selection.split('/')[:-1]
                modPath = '/'+os.path.join(*path)
                modStripped=modStripped.split(dirListParams['modNameSplitChar'])[0]
                modFd=open(os.path.join(modPath,(modStripped+'.xml')))
                modFd.close()

            return 0

        except IOError:
            print 'No xml configuration file found for this module.'
            return -1
        except OSError:
            print "%s not found."%directory
            self.logFile.write("%s not found.\n"%directory)
            
        except KeyboardInterrupt:
            print
            return -1       

    #Handles a curses form.  Generates the form and executes the appropriate
    #commands with the information returned from the forms.
    #Arguments:
    #   userIn: the line entered by the user
    #   fName:  the name of the function the user is trying to execute
    #   mod:    the name of the module that provides fName
    #Return:
    #    0: success, if no rpc was created
    #    -1: error occured that does not require the lp to exit
    #    -2: exit lp after returning
    #    else: id number of rpc created by this call
    def handleCursesForm(self, userIn, fName, mod):
        self.logFile.write('Curses form entered.\n')
        arguments=[]
        formType=''
        
        if fName=='Tunnel.redirTunnel':
            formType='redir'
        elif fName=='Tunnel.outTunnel':
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
            
            if arg!=[] and validArg==True:            
                
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
                if fName=='Tunnel.redirTunnel' or fName=='Tunnel.outTunnel':
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
                        return -1
                
                res=self.functions.cmdGeneric(fName,self.Modules[mod][fName],{})
            
                if fName=='Tunnel.redirTunnel' or fName=='Tunnel.outTunnel':
                    self.printTunnelCmd([tunnelCmd],0)
               
            elif arg!=[] and validArg!=True:
                print "Error.  Input not provided for %s."%validArg
                self.logFile.write("Error.  Input not provided for %s.\n"%validArg)

        return res

    #Handles the upgrade command.  Continuously sends the stat command until
    #the upgrade rpc is no longer listed as active.
    #Arguments:
    #   cmdRes: the rpc number of the upgrade rpc
    #Return:
    #   'abort' is the upgrade was successfull or was aborted
    #   The rpc result number if the upgrade rpc returned an error
    def handleUpgrade(self, cmdRes):
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
            print "Upgrade rpc returned error: %s"%rpcRes
            self.logFile.write("Upgrade rpc returned error: %s"%rpcRes)
            self.functions.cmdGeneric('port',{'command':'!port','outport':str(PRINT_PORT),
                                              'endOnString':'DONE'},{})
            self.lpSock.setblocking(1)
            return rpcRes

    #Calls a function which prints information to the user and blocks until the
    #print completes.  This is used whenever the front end needs to finish 
    #printing the ouput of a function before the user is allowed to perform any
    #other actions.
    #Arguments:
    #   func: the name of the function to call
    def printFunctionOut(self,func):
        self.printBlocker.sendto('!!#TURN_OFF_PRINTING',('127.0.0.1',RPC_DISPATCH_PORT))
        
        if func=='mods':
            print "******************Loaded Modules*****************"
            self.logFile.write("******************Loaded Modules*****************\n")
            res = self.functions.cmdGeneric('mods',{'command':'!mods'},{})
            self.printBlocker.sendto('!!#REG_BLOCK%d'%res,('127.0.0.1',RPC_DISPATCH_PORT))
            result = self.printBlocker.recv(1024)

        elif func=='listTunnels':
            res = self.functions.cmdGeneric('listTunnels',{'command':'!call','ciface':'34',
                                                           'cfunc':'2','cprov':'1'},{})
            
            self.printBlocker.sendto('!!#REG_BLOCK%d'%res,('127.0.0.1',RPC_DISPATCH_PORT))
            result = self.printBlocker.recv(1024)

        self.printBlocker.sendto('!!#TURN_ON_PRINTING',('127.0.0.1',RPC_DISPATCH_PORT))
        
    def parseXml(self, mod, requireLpEx):
        ret = Lp_XmlParser.parseMod(self.helpDict, self.Modules, mod, self.architecture, self.lpArch, self.fMaps, 
                                    requireLpEx, self.functions, 0)

        if ret != None:
            for entry in ret:
                self.functionList.append(entry)
        
    #The call command can be used to browse loaded modules and call any function from any loaded module.
    #It is intended as an advanced/developer command, and therefore will not be shown by help.  
    #It can be called by entering 'call' at the lp prompt. 
    #Arguments:
    #   line: the string inputed by the user
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
    
    #Prints help information to the user.  If no arguments are provided, it
    #prints the commands available from each loaded module.  If a module name
    #or module iface number is entered, prints the functions available for that 
    #module.  If a function number of name is entered, prints the configured
    #help message for that functions.
    #Arguments:
    #   line: the string inputed by the user
    def do_help(self,line):
        usrIn=line.split(" ")
        if line=="":
            toSort= {}
            sorted = []
            print "****Available Commands****"
            self.logFile.write("****Available Commands****\n")
            keys=self.helpDict.keys()
            for key in keys:
                toSort[int(self.helpDict[key]['iface'])] = key

            sorted = self.__sortIfaces(toSort)
            for mod in sorted:
                self.__printModuleFunctions(mod)
                
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
                    ifaceNum=Lp_XmlParser.parseIface(modStr, self.architecture, self.lpArch)
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
    
    def __sortIfaces(self,ifaceList):
        toSort = ifaceList.keys()
        toSort = sorted(toSort)

        toReturn = []
        for item in toSort:
            toReturn.append(ifaceList[item])

        return toReturn

    #Binding for help command        
    def do_h(self,line):
        self.do_help(line)
        
    #Exits the LP without printing modules after receiving confirmation of burn.
    def do_abort(self,line):
        print "Goodbye"
        return True
    
    #Prints modules loaded and then exits the LP    
    def do_exit(self,line):
        #Display loaded modules on exit.  
        try:
            self.printFunctionOut('mods')
            res=self.functions.cmdGeneric('term',{'command':'!term','endOnString':'DONE'},{})
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
            if fName != 'iface':
                num=self.helpDict[modKey][fName]['fnum']
                fMaps[int(str(num).split('.')[1])]=fName
                fNums.append(int(str(num).split('.')[1]))

        fNums=sorted(fNums)
        for num in fNums:
            toReturn.append(fMaps[num])

        return toReturn
    
    #Checks if there are any empty strings in a list returned by CursesDriver
    def __checkArg(self,toCheck):
        for element in toCheck:
            if element[1]=='':
                return element[0]
                
        return True
        
    def __resolveFuncName(self,name):
        try:
            function=self.fMaps[name]
        except KeyError:
            function=name
            
        return function

    #Prints the functions available from a loaded module.
    def __printModuleFunctions(self,modName):
        fKeys=self.helpDict[modName].keys()
        #every helpDict entry has an iface key, so only print the module 
        #if there is something in addition to this
        if len(fKeys)<=1:
            return

        iface = self.helpDict[modName]['iface']
        print 'Module %s: %s'%(str(iface),modName)
        self.logFile.write('Module: %s\n'%modName)
        sortedfKeys=self.__sort(modName,fKeys)
        for fKey in sortedfKeys:
            if self.helpDict[modName][fKey]['nodisplay']!="true":
                shortName = fKey.split(".")
                if len(shortName)>1:
                    shortName = shortName[1]
                else:
                    shortName = shortName[0]
                disp="   %s: %s"%(self.helpDict[modName][fKey]['fnum'],shortName)
                print disp
                self.logFile.write((disp+'\n'))
        print
 
