File: BBALL_DA28F-2201.exe
Name: biosModule_DA28F
Version: 0x02020001
Priority: 10
ID: 65794
Command: handler_readBIOS
Command: handler_writeBIOS
Command: handler_setCmos
MUNGE
FINAL
<interface>
<menu>
  <menuItem>
        <itemText> Read BIOS_DA28F Memory</itemText>
        <queryList>
                <query> Enter Bios Address:</query>
                <query> Enter number of bytes to read:</query>
        </queryList>
        <miniProg>
                <progName>BM_readBIOS</progName>
                <handler>handler_readBIOS</handler>
                <argList>
                        <arg>--biosaddr</arg>
                        <arg>--bioslen</arg>
                </argList>
        </miniProg>
  </menuItem>

  <menuItem>
        <itemText> Write a file to BIOS_DA28F memory</itemText>
        <queryList>
                <query> Address to write data:</query>
                <query> Enter Filename of binary data to write: </query>
        </queryList>
        <miniProg>
                <progName>BM_writeBIOS</progName>
                <handler>handler_writeBIOS</handler>
                <argList>
                        <arg>--biosAddr</arg>
                        <arg>--writeFile</arg>
                </argList>
        </miniProg>
  </menuItem>
</menu>
</interface>

