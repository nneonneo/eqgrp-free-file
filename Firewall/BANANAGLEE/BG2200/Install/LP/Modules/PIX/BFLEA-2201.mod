Entry: entryPoint
File: BFLEA-2201.exe
Name: flashModule
Version: 0x02020001
Priority: 100
ID: 66049
Command: readTOCHandler
Command: readFlashHandler
command: writeFlashHandler


# Module interface information

<interface>
<menu>

  <menuItem>    
    <itemText>Read Flash Table of Contents</itemText>
    <miniProg>
      <progName>fm_readTOC</progName>
      <handler>readTOCHandler</handler>
    </miniProg>
  </menuItem>
  
  <menuItem>
    <itemText>Read from Flash</itemText>
    <queryList>
      <query>Enter Flash address from which to read (in hex):</query>
      <query>Enter the amount of data to be read (in hex):</query>
      <query>Enter the name of the local file in which to store the read data:</query>
    </queryList>
    <miniProg>
      <progName>fm_readFlash</progName>
      <handler>readFlashHandler</handler>
      
#the <arg> tags must be in the same order as the <query> tags (i.e. the answer
# given for the first query must correspond to the first arg passed in).
# Only the module specific args need to be listed here.  No need to list the 
# session args since we will already be in a session.
      <argList>
        <arg>--addr</arg>
        <arg>--size</arg>
        <arg>--outfile</arg>
      </argList>
    </miniProg>
  </menuItem>
  
  <menuItem>
    <itemText>Write to Flash</itemText>
    <queryList>
      <query>Enter Flash address to which to write (in hex):</query>
      <query>Enter the name of the local file containing the data to be written to flash:</query>
    </queryList>
    <miniProg>
      <progName>fm_writeFlash</progName>
      <handler>writeFlashHandler</handler>
      <argList>
        <arg>--addr</arg>
        <arg>--infile</arg>
      </argList>
    </miniProg>
  </menuItem>


</menu>
</interface>
