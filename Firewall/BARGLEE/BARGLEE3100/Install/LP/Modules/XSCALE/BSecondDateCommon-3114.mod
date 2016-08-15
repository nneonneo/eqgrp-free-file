Entry: EntryPoint
File: BSecondDateCommon-3114.exe
Name: SecondDate-Common
Version: 0x03010104
Priority: 99
ID: 0x70101
Chain: 0x10000000
Activate: activateHandler
Deactivate: deactivateHandler
Install: installHandler
Uninstall: uninstallHandler
getconfig: getConfig
reconfigure: reconfigure
persistence: full
Command: cmdHandler
MUNGE
FINAL

<interface>
<menu>

# This retrieves the SecondDate settings (crypto variable, node id, magic)
  <menuItem>
    <itemText>Retrieve the SecondDate Implant Settings</itemText>
    <miniProg>
      <progName>SecondDateCommon-miniprog</progName>
      <handler>cmdHandler</handler>
      <argList>
        <arg>--task get</arg>
      </argList>
    </miniProg>
  </menuItem>

# This adusts the SecondDate implant settings
  <menuItem>
    <itemText>Update the SecondDate Implant Settings</itemText>
    <queryList>
      <query>Enter the new key (32 ASCII hex chars [0-9][a-f]):</query>
      <query>Enter the new node ID (prefixed with 0x):</query>
      <query>Enter the new magic value (prefixed with 0x):</query>
    </queryList>
    <miniProg>
      <progName>SecondDateCommon-miniprog</progName>
      <handler>cmdHandler</handler>
      <argList>
        <arg>--key</arg>
        <arg>--id</arg>
        <arg>--magic</arg>
	   <arg>--task set</arg>
      </argList>
    </miniProg>
  </menuItem>

# This enables SecondDate
  <menuItem>
    <itemText>Enable SecondDate</itemText>
    <miniProg>
      <progName>SecondDateCommon-miniprog</progName>
      <handler>cmdHandler</handler>
      <argList>
        <arg>--task enable</arg>
      </argList>
    </miniProg>
  </menuItem>

# This disables SecondDate
  <menuItem>
    <itemText>Disable SecondDate</itemText>
    <miniProg>
      <progName>SecondDateCommon-miniprog</progName>
      <handler>cmdHandler</handler>
      <argList>
        <arg>--task disable</arg>
      </argList>
    </miniProg>
  </menuItem>

</menu>
</interface>
