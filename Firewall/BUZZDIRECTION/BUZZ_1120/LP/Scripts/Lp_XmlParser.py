import os
import xml.dom.minidom
import Lp_FrontEndFunctions
import textwrap

def parseIface(args):
    mod=args[0]
    architecture=args[1]
    lpArch=args[2]
    curDir=os.getcwd() 
    modName=mod.split('/')[len(mod.split('/'))-1]
    modStripped=modName.split('_')[0]
    modStripped=modStripped.split('.')[0]
    try:
        if architecture=='':
            dom=xml.dom.minidom.parse((curDir+'/../Mods/Base/Buzzdirection/'+lpArch+'/'+modStripped+".xml"))
        else:
            dom=xml.dom.minidom.parse((curDir+'/../Mods/Base/Buzzdirection/'+architecture+'/'+modStripped+".xml"))

    except IOError:
        try:
            if architecture=='':
                dom=xml.dom.minidom.parse((curDir+'/../Mods/App/Buzzdirection/'+lpArch+'/'+modStripped+".xml"))
            else:
                dom=xml.dom.minidom.parse((curDir+'/../Mods/App/Buzzdirection/'+architecture+'/'+modStripped+".xml"))

        except IOError:
            try:
                dom=xml.dom.minidom.parse((curDir+'/Xml/'+modStripped+".xml"))
            except IOError:
                return -1

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

#Parse the xml file for the module specified in usrIn and populate the Modules dictionary
#Arguments:
#    usrIn:  user input which specifies the xml file to parse
#Return:
#    None
def parseMod(args, okToParse):
    helpDict=args[0]
    Modules=args[1]
    mod=args[2]
    architecture=args[3]
    lpArch=args[4]
    fMaps=args[5]
    requireLpEx=args[6]
    lpFuncs=args[7]
    
    if okToParse>0:
        return

    curDir=os.getcwd() 
    modName=mod.split('/')[len(mod.split('/'))-1]
    modStripped=modName.split('_')[0]
    modStripped=modStripped.split('.')[0]
    try:
        if architecture=='':
            dom=xml.dom.minidom.parse((curDir+'/../Mods/Base/Buzzdirection/'+lpArch+'/'+modStripped+".xml"))
        else:
            dom=xml.dom.minidom.parse((curDir+'/../Mods/Base/Buzzdirection/'+architecture+'/'+modStripped+".xml"))

    except IOError:
        try:
            if architecture=='':
                dom=xml.dom.minidom.parse((curDir+'/../Mods/App/Buzzdirection/'+lpArch+'/'+modStripped+".xml"))
            else:
                dom=xml.dom.minidom.parse((curDir+'/../Mods/App/Buzzdirection/'+architecture+'/'+modStripped+".xml"))

        except IOError:
            try:
                dom=xml.dom.minidom.parse((curDir+'/Xml/'+modStripped+".xml"))
            except IOError:
                return

    loadEx=1    
    #Make sure an ex file exists
    dirSplit=mod.split('/')
    if lpArch=='i386':
        lpEx='%s.lx32'%modStripped
    else:
        lpEx='%s.lx64'%modStripped
    fileLoc=''
    for i in range(1,len(dirSplit)-1,1):
        fileLoc=fileLoc+'/'+dirSplit[i]
    fileLoc+='/'+lpEx
    
    try:
        fdTest=open(fileLoc)
    except IOError:
        #If this is an application module and the xml file has functions, then complain that there is no lp ex file
        if requireLpEx==1 and len(dom.getElementsByTagName('function'))>0:
            print "Could not find an Lp extension for %s.  Functions from this module will be \nuncallable."%lpEx.split('.')[0],
            print "Ensure that an Lp extension is located in\nRelease/Mods/App/Buzzdirection/<arch>."
            return
        loadEx=0
        #return
        
    if loadEx==1:
        fdTest.close()
        lpFuncs.cmdGeneric('lpex',{'command':'!lpex','lpexfile':fileLoc, 'endOnString':'DONE'},{})
    Modules[modStripped]={}
    helpDict[modStripped]={}
    modDict=Modules[modStripped]
    ifaceNum=dom.getElementsByTagName('iface')[0].firstChild.data
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

        errorStr=f.getElementsByTagName('errorStr')
        if len(errorStr)>0:
            errorStr=errorStr[0].firstChild.data

        #Read required parameters
        try:
            fName=f.getElementsByTagName('name')[0].firstChild.data
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
        modDict[fName]['errorStr']=errorStr
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

    
