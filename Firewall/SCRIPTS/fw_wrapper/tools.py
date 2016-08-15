import sys
import fw_logging
import ConfigParser
import logging
import os
import shutil
import datetime
import random
import shelve
import subprocess
import netaddr
import zipfile

def unzip(logger, path, root):
	os.chdir(root)
	zip = zipfile.ZipFile(path)
	for f in zip.namelist():
		if f.endswith('/'):
			os.makedirs(f)
		else:
			zip.extract(f)

def cidr(sfile,logger,ip):
	if '/' in ip:
		addCIDR(sfile,logger,ip)
	elif ' ' in ip:
		host = ip.split(' ')[0]
		net = ip.split(' ')[1]
		if checkIP(host) == False:
			logger.error('you did not provide a valid IP: ' + str(host))
			return
		if checkIP(net) == False:
			logger.error('you did not provide a valid netmask: ' + str(netmask))
			return

		def get_net_size(netmask):
		        binary_str = ''
		        for octet in netmask:
                		binary_str += bin(int(octet))[2:].zfill(8)
		        return str(len(binary_str.rstrip('0')))

		ipaddr = host.split('.')
		netmask = net.split('.')

		net_start = [str(int(ipaddr[x]) & int(netmask[x]))
                	for x in range(0,4)]

		a = '.'.join(net_start) + '/' + get_net_size(netmask)

		addCIDR(sfile,logger,a)
	else:
		if checkIP(ip) == True:
			addCIDR(sfile,logger,ip + '/32')
		else:
			self.logger.error('you did not provide valid input: ' + str(ip))

def addCIDR(sfile,logger,ip):
	a = ip.split('/')[0]
        b = ip.split('/')[1]
        if checkIP(a) == False:
        	logger.error('you did not provide a valid IP: ' + a)
                return
        if int(b) > 32:
                logger.error('you did not provide a valid cidr: ' + b)

        ips = netaddr.IPNetwork(ip)

        return_list = []

        for i in ips:
                if i == ips.network:
        	        pass
                elif i == ips.broadcast:
                        pass
                else:
                        return_list.append(i)

        if int(b) == 32:
                return_list.append(a)

        if sfile.has_key('iprange') == False:
                sfile['iprange'] = return_list
        else:
                t = sfile['iprange']
                for i in return_list:
        	        t.append(i)
                sfile['iprange'] = t

        return

	

def resetAuto(sfile,logger):
	if sfile['auto_end'] == True:
		sfile['rules'] = []
	sfile['auto'] = False
	sfile['auto_start'] = False
	sfile['auto_end'] = False
	sfile['auto_PTK'] = False
	logger.debug('reset all auto fields')

def intToHEX(string):
	if str(string[:1]) == '0x':
		return string
	else:
		hex(int(string))

def checkTunnelRule(sfile,logger):
	counter = 0
	
	current_rule = sfile['current_rule']

	if sfile['mode'] == 'simple':
		if current_rule['attk_source'] == '':
			logger.error('the attackers source has not been specified')
			counter += 1
		if current_rule['attk_dest'] == '':
			logger.error('the attackers destination has not been specified')
			counter += 1
		if current_rule['tgt_source'] == '':
			logger.error('the targets source had not been specified')
                        counter += 1
		if current_rule['tgt_dest'] == '':
                        logger.error('the targets destination has not been specified')
                        counter += 1
		if current_rule['attk_int'] == '':
 			logger.error('the attackers interface has not been specified')
			counter += 1
		if current_rule['tgt_int'] == '':
			logger.error('the targets interface has not been specified')
                        counter += 1

	if counter > 0:
        	logger.critical('missing required parameters needed for upload')
            	return False
       	else:
		return True

def show_settings(sfile, option, logger):

	logger.info('Current settings')
        logger.info('----------------')
        if option == '':
        	logger.info('Hostname: ' + str(sfile['hostname']))
                logger.info('Target: ' + str(sfile['target']))
                logger.info('LP IP: ' + str(sfile['lp']))
                logger.info('Implant IP: ' + str(sfile['implant']))
                logger.info('IDKey: ' + str(sfile['idkey']))
                logger.info('Source Port: ' + str(sfile['sport']))
                logger.info('Destination Port: ' + str(sfile['dport']))
        else:
                list = sfile.keys()
		for i in list:
        	        logger.info(i + ' : ' + str(sfile[i]))

def openTunnel(sfile,logger):

	if sfile['do_tunnel'] == False:
		logger.debug('user set tunnel to False')
		return
	else:
		updatePorts(sfile,logger)	

	if sfile.has_key('iprange') == False:
		logger.error('WARNING: no IP ranges have not been specified will default to the target IP but this is not good, please fix for the future in fw_wrapper.py')
		ip = sfile['target']
	else:
		if sfile['iprange'] == []:
	                logger.error('WARNING: no IP ranges have not been specified will default to the target IP but this is not good, please fix for the future in fw_wrapper.py')
        	        ip = sfile['target']
		else:
			ip = sfile['iprange'][random.randint(0,len(sfile['iprange']))]		
			logger.debug('using this ip: ' + str(ip))

	tunnel_open = str(sfile['echo']) + ' "u ' + str(sfile['dport']) + ' ' + str(ip) + ' ' + str(sfile['dport']) + ' ' + str(sfile['sport']) + '" | ' + str(sfile['nc']) + ' -w1 -u 127.0.0.1 1111' 
	logger.debug('running ' + str(tunnel_open))
	
	add_tunnel = subprocess.Popen(tunnel_open,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        tunnel_output_stdout = add_tunnel.stdout.read()
        tunnel_output_stderr = add_tunnel.stderr.read()

	logger.debug('stdout from tunnel: ' + str(tunnel_output_stdout))
        logger.debug('stderr frin tunnel: ' + str(tunnel_output_stderr))

	tunnel_number = 0

	for i in tunnel_output_stdout.split('\r\n'):
		if 'NOTICE' in i:
			if 'success' in i:
				tunnel_number = i.split(' ')[-1].rstrip('\r\n')

	#open tunnel did not work
	if tunnel_number == 0:
		for i in tunnel_output_stderr.split('\r\n'):
			if 'Connection refused' in i:
				logger.error('could not open tunnel, please verify that you ran -fwtunnel')

	return tunnel_number

def closeTunnel(sfile,tunnel_number,logger):

        if sfile['do_tunnel'] == False:
                logger.debug('user set tunnel to False')
                return

	tunnel_close = str(sfile['echo'] + ' "c ' + str(tunnel_number) + '" | ' + str(sfile['nc']) + ' -w1 -u 127.0.0.1 1111')

	delete_tunnel = subprocess.Popen(tunnel_close,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        logger.debug('running: ' + str(tunnel_close))

	tunnel_close_output_stdout = delete_tunnel.stdout.read()
        tunnel_close_output_stderr = delete_tunnel.stderr.read()

        logger.debug('stdout from tunnel: ' + str(tunnel_close_output_stdout))
        logger.debug('stderr from tunnel: ' + str(tunnel_close_output_stderr))

	for i in tunnel_close_output_stdout.split('\r\n'):
		if 'NOTICE' in i:
			if 'complete' in i:
				logger.debug('successfully closed tunnel ' + str(tunnel_number))
	
	for i in tunnel_close_output_stderr.split('\r\n'):
		if 'closed' in i:
			logger.error(str(i))

def shutdownTunnel(sfile,logger):

        if sfile['do_tunnel'] == False:
                logger.debug('user set tunnel to False')
                return

	close_all_tunnels = str(sfile['echo']) + ' "c 1 2 3 4 5 6" | ' + str(sfile['nc']) + ' -w1 -u 127.0.0.1 1111'
	shutdown_tunnel = str(sfile['echo']) + ' "q" | ' + str(sfile['nc']) + ' -w1 -u 127.0.0.1 1111'

	close_tunnel = subprocess.Popen(close_all_tunnels,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	logger.debug('running: ' + str(close_all_tunnels))

	close_tunnel_stdout = close_tunnel.stdout.read()
	close_tunnel_stderr = close_tunnel.stderr.read()

	logger.debug('stdout from tunnel: ' + str(close_tunnel_stdout))
        logger.debug('stdout from tunnel: ' + str(close_tunnel_stderr))

	shut_tunnel = subprocess.Popen(shutdown_tunnel,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	logger.debug('running: ' + str(shutdown_tunnel))

	shut_tunnel_stdout = shut_tunnel.stdout.read()
        shut_tunnel_stderr = shut_tunnel.stderr.read()

	logger.debug('stdout from tunnel: ' + str(shut_tunnel_stdout))
	logger.debug('stdout from tunnel: ' + str(shut_tunnel_stderr))

def checks(sfile,logger):
	'''Function to check to ensure that all correct variables are assigned
        before attempting to talk to the implant'''

        if sfile['idkey'] == 'idkey':
        	logger.error('idkey has not been specified')
		return False
		if os.pathi.isfile(sfile['idkey']) == False:
			logger.error('could not locate your IDKey')
	                return False
        elif sfile['lp'] == '':
                logger.error('lp ip has not been specified')
                return False
        elif sfile['implant'] == '':
                logger.error('implant ip has not been specified')
                return False
        elif sfile['sport'] == '':
                logger.error('source port has not been specified')
                return False
        elif sfile['dport'] == '':
                logger.error('destination port had not been specified')
                return False
        elif sfile['target'] == '':
                logger.error('target ip has not been specified')
                return False
        elif sfile['hostname'] == '':
                logger.error('target hostname has not been specified')
                return False
        else:
                logger.debug('all checks have passed')
                return True

def checkPort(port):
	return (int(port) > 0 and int(port) <= 65535)

def checkIP(ip):
	parts = ip.split('.')
        return (
        	len(parts) == 4
                and all(part.isdigit() for part in parts)
                and all(0 <= int(part) <= 255 for part in parts)
                )

def updatePorts(sfile, logger):
	
	logger.debug('updating ports')
	
	sfile['sport'] = newPort()
	sfile['dport'] = newPort()

	logger.debug('sport: ' + str(sfile['sport']))
	logger.debug('dport: ' + str(sfile['dport']))

def newPort():
	return random.randint(2000,65000)

def timeStamp():
	return str(datetime.datetime.now().year) + str(datetime.datetime.now().month) + str(datetime.datetime.now().day) + '_' + str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute) + str(datetime.datetime.now().second)

