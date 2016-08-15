import threading
import Lp_UserInterface
import socket
import sys

class RpcDispatcher(threading.Thread):
    def __init__(self, processor):
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1',Lp_UserInterface.RPC_DISPATCH_PORT))
        self.rpcActions={}
        self.proc=processor
        self.enablePrinting=0
        self.lastRpcString=''
        threading.Thread.__init__(self)
        
    def run(self):
        while 1:
            input = self.sock.recv(1024)

            if input.find("SEND")>=0:
                
                #register the rpc action
                id = input[4:input.find(',')]
                function = input[input.find(',')+1:input.find(':')]
                if function == 'load':
                    file = input[input.find(':')+1:]
                    self.rpcActions[id]=(self.doLoadCallback,[file], id)

                elif function == 'unload':
                    iface = input[input.find(':')+1:]
                    self.rpcActions[id]=(self.doUnloadCallback,[iface], id)

                elif function == 'burn':
                    self.rpcActions[id]=(self.doBurnCallback,[], id)

                elif function == 'upgrade':
                    self.rpcActions[id]=(self.doUpgradeCallback,[], id)

                else:
                    self.rpcActions[id]=(0,[], id)

            elif input.find("RECV")>=0:
                self.lastRpcString = input
                
                #perform the rpc action, if there is a registered action
                id=input[input.find('#')+1:input.find(',')]
                retCode = input[input.find('rc=')+3:len(input)-1]
                if self.enablePrinting ==1:
                    print input,
                    print '\rLP> ',
                    sys.stdout.flush()

                if id in self.rpcActions and self.rpcActions[id][0] != 0:
                    self.rpcActions[id][0](self.rpcActions[id][1],
                                           self.rpcActions[id][2], retCode)

            elif input.find("!!#QUIT")>=0:
                self.sock.close()
                break
            elif input.find("!!#TURN_ON_PRINTING")>=0:
                self.enablePrinting = 1
            elif input.find("!!#TURN_OFF_PRINTING")>=0:
                self.enablePrinting = 0
            elif input.find('!!#REG_BLOCK')>=0:
                rpcId = input[12:]
                self.rpcActions[rpcId] = (self.endBlock,[],rpcId)

    def endBlock(self,emptyList,rpc, retCode):
        self.sock.sendto("END",('127.0.0.1',Lp_UserInterface.BLOCKER_PORT))
        del self.rpcActions[rpc]
            
    def doLoadCallback(self,modfile,rpc, retCode):
        if retCode == '0':
            self.proc.parseXml(modfile[0],1)
        del self.rpcActions[rpc]
        
    def doUnloadCallback(self,iface,rpc, retCode):
        if retCode == '0':
            self.proc.deleteMod(iface,0)
        del self.rpcActions[rpc]
        
    def doBurnCallback(self,emptyList,rpc, retCode):
        self.sock.sendto(self.lastRpcString,('127.0.0.1',Lp_UserInterface.FRONTEND_PORT))
        del self.rpcActions[rpc]
        
    def doUpgradeCallback(self,emptyList,rpc, retCode):
        self.sock.sendto(self.lastRpcString,('127.0.0.1',Lp_UserInterface.FRONTEND_PORT))
        del self.rpcActions[rpc]
