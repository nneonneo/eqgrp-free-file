File: IVL-2101.exe
Name: IVL
Version: 0x02010001
Priority: 99
ID: 999
Chain: 0x10000000
Activate: ivlAct
Deactivate: ivlDeact
Install: ivlIn
Uninstall: ivlUn
Command: ivlCommand
getconfig: ivlGetConfig
reconfigure: ivlReconfigure
MUNGE
FINAL

<interface>
<menu>
  <menuItem>
    <itemText>Pull Back Crypto</itemText>
    <miniProg>
      <progName>IvlMiniProg</progName>
      <handler>ivlCommand</handler>
    </miniProg>
  </menuItem>
   
</menu>
</interface>

