Entry: EntryPoint
File: BPATROL-2101.exe
Name: Profiler
Version: 0x02010001
Priority: 20
ID: 197121
Chain: 0x10000000
Install:prof_install
Activate: prof_act
Deactivate: prof_deact
Uninstall:prof_uninstall
getconfig:dumpConfig
reconfigure:reconfigure
Command: getprofHandler
Command: uploadfiltHandler
Command: uploadxtrtHandler
Command: getstatusHandler
Command: selectfiltHandler
Command: selectxtrtHandler
Command: rmfiltHandler
Command: rmxtrtHandler
Command: setmemHandler


<interface>
<menu>

  <menuItem>    
    <itemText>Get Profile</itemText>
    <queryList>
      <query>Enter the filename into which to write the profile:</query>
    </queryList>
     
    <miniProg>
      <progName>profiler_miniprog</progName>
      <handler>getprofHandler</handler>
      <argList>
	<arg>--arg2</arg>
        <arg>--name getprof</arg>
      </argList>
      
    </miniProg>
  </menuItem>
  
  <menuItem>
    <itemText>Upload Filter</itemText>
    <queryList>
      <query>Enter the ID of this filter(hex):</query>
      <query>Enter the filename from which to read the filter:</query>
    </queryList>

    <miniProg>
      <progName>profiler_miniprog</progName>
      <handler>uploadfiltHandler</handler>
      <argList>
	<arg>--arg1</arg>
	<arg>--arg2</arg>
        <arg>--name upload</arg>
      </argList>
    </miniProg>
  </menuItem>


  <menuItem>
    <itemText>Upload Extract</itemText>
    <queryList>
      <query>Enter the ID of this Extract(hex):</query>
      <query>Enter the filename from which to read the extract:</query>
    </queryList>

    <miniProg>
      <progName>profiler_miniprog</progName>
      <handler>uploadxtrtHandler</handler>
      <argList>
	<arg>--arg1</arg>
	<arg>--arg2</arg>
        <arg>--name upload</arg>
      </argList>
    </miniProg>
  </menuItem>
  

  <menuItem>
    <itemText>Get Status</itemText>

    <miniProg>
      <progName>profiler_miniprog</progName>
      <handler>getstatusHandler</handler>
      <argList>
        <arg>--name getstat</arg>
      </argList>
    </miniProg>
  </menuItem>


  <menuItem>
    <itemText>Select Filter</itemText>
    <queryList>
      <query>Enter the ID of Filter to select(hex):</query>
    </queryList>

    <miniProg>
      <progName>profiler_miniprog</progName>
      <handler>selectfiltHandler</handler>
      <argList>
	<arg>--arg1</arg>
        <arg>--name select</arg>
      </argList>
    </miniProg>
  </menuItem>


  <menuItem>
    <itemText>Select Extract</itemText>
    <queryList>
      <query>Enter the ID of Extract to select(hex):</query>
    </queryList>

    <miniProg>
      <progName>profiler_miniprog</progName>
      <handler>selectxtrtHandler</handler>
      <argList>
	<arg>--arg1</arg>
        <arg>--name select</arg>
      </argList>
    </miniProg>
  </menuItem>


  <menuItem>
    <itemText>Remove Filter</itemText>
    <queryList>
      <query>Enter the ID of Filter to remove(hex):</query>
    </queryList>

    <miniProg>
      <progName>profiler_miniprog</progName>
      <handler>rmfiltHandler</handler>
      <argList>
	<arg>--arg1</arg>
        <arg>--name remove</arg>
      </argList>
     </miniProg>
  </menuItem>

  <menuItem>
    <itemText>Remove Extract</itemText>
    <queryList>
      <query>Enter the ID of Extract to remove(hex):</query>
    </queryList>

    <miniProg>
      <progName>profiler_miniprog</progName>
      <handler>rmxtrtHandler</handler>
      <argList>
	<arg>--arg1</arg>
        <arg>--name remove</arg>
      </argList>
     </miniProg>
  </menuItem>

  <menuItem>
    <itemText>Set Profile Size </itemText>
    <queryList>
      <query>Enter the size, in bytes, of Profile on box(hex):</query>
    </queryList>

    <miniProg>
      <progName>profiler_miniprog</progName>
      <handler>setmemHandler</handler>
      <argList>
	<arg>--arg1</arg>
        <arg>--name setmem</arg>
      </argList>
     </miniProg>
  </menuItem>

</menu>
</interface>
