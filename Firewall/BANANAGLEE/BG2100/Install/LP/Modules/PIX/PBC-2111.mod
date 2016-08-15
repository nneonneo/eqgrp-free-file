File: PBC-2111.exe
Name: PBC-2111.exe
Version: 0x02010101
Priority: 99
ID: 777
Chain: 0x10000000
Activate: pbcAct
Deactivate: pbcDeact
Install: pbcIn
Uninstall: pbcUn
Command: pbcCommand
getconfig: pbcGetConfig
reconfigure: pbcReconfigure
MUNGE
FINAL

<interface>
<menu>
  <menuItem>
    <itemText>Pull Back Crypto</itemText>
    <miniProg>
      <progName>PbcMiniProg</progName>
      <handler>pbcCommand</handler>
    </miniProg>
  </menuItem>
   
</menu>
</interface>

