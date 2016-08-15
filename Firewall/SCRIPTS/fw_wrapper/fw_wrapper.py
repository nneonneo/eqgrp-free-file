#!/usr/src/Python-2.7.2/python
import tools
import bananaglee
import finder
import fw_logging
import tunnel

import cmd
import getpass
import ConfigParser
import sys
import os
import logging
import shelve
import shutil
from optparse import OptionParser

class Console(cmd.Cmd):

	def __init__(self, hostname, target, auto):
		cmd.Cmd.__init__(self)
		self.config = ConfigParser.ConfigParser()
                self.config.read('fw_wrapper.cfg')

		#set up logging
		name = 'fw_wrapper'
		self.logger = fw_logging.getLogger(logging.DEBUG,name,hostname,target)

		self.logger.info('welcome to ' + str(name) + ' please select your tool')
		
		#check to make sure running as root
		if getpass.getuser() != 'root':
			self.logger.critical('not running as root, bailing')
			sys.exit()	
		self.prompt = 'FW>>'
		self.hostname = hostname
		self.target = target
		self.logger.info('hostname: ' + str(self.hostname))
		self.logger.info('target: ' + str(self.target))
		self.logger.debug('calling finder')
		finder.finder(hostname,target)
		self.tool_versions = {}
		try:
			self.tools = self.config.get('main','tools')
		except:
			self.logger.exception('could not read the tools in main section of the config')
			sys.exit()
		
		try:
			self.log_dir = self.config.get('main','log_dir')
		except:
			self.logger.exception('could not read the log_dir in the main section of the config')
			sys.exit()
	
		try:
			self.root_path = self.config.get('main','root_path')
		except:
			self.logger.exception('could not read the root_path in the main section of the config')
			sys.exit()

		try:
			self.script_dir = self.config.get('main','script_dir')
		except:
			self.logger.exception('could not read script_dir in the main section of the config')
			sys.exit()

		try:
			self.fg_dir = self.config.get('main','fg_dir')
		except:
			self.logger.exception('could not read fg_dir in the main section of the config')

		try:
			self.bg_versions = self.config.get('bananaglee','versions').split(',')
		except:
			self.logger.exception('could not get the bananaglee versions')

		self.shelve_file = os.path.join(self.log_dir,'firewall_' + str(hostname) + '.' + str(target) + '.shelve')

		if os.path.isfile(self.shelve_file) == True:
			pass
		else:
			self.logger.error('Could not find your shelve file')
		
		try:
			self.sfile = shelve.open(self.shelve_file)	
		except:
			self.logger.exception('could not open the shelve file: ' + str(self.shelve_file))
			sys.exit()

		self.sfile['hostname'] = self.hostname
		self.sfile['target'] = self.target
		self.sfile['root_path'] = self.root_path
                self.sfile['script_dir'] = self.script_dir
                self.sfile['log_dir'] = self.log_dir
                self.sfile['fg_dir'] = self.fg_dir

		self.sfile['do_tunnel'] = True

		self.sfile['echo'] = self.config.get('main','echo')
		self.sfile['nc'] = self.config.get('main','nc')

		#check fg for files
		for root, subFolders, files in os.walk(self.fg_dir):
			for file in files:
				if '.zip' in file:
					if 'firewall' in file:
						self.logger.info('found ' + str(os.path.join(root,file)) + ' unzipping')
						tools.unzip(self.logger,os.path.join(root,file),root)

                for root, subFolders, files in os.walk(self.fg_dir):
                        for file in files:
				if '.key' in file:
					self.logger.info('found ' + str(os.path.join(root,file)) + ' moving to ' + str(os.path.join(self.root_path,'OPS')))
					shutil.copy(os.path.join(root,file),os.path.join(self.root_path,'OPS'))
				if '.shelve' in file:
					self.logger.info('found ' + str(os.path.join(root,file)) + ' moving to ' + str(self.log_dir))
					shutil.copy(os.path.join(root,file),self.log_dir)
				

                if auto[0] == True:
                        self.sfile['auto'] = True
			#auto has been set to true
                        if auto[1] == True and auto[2] == True:
                                self.logger.error('you specified auto with start and end')
                        elif auto[1] == True:
                                self.logger.info('going into auto mode for the start of the op')
				self.sfile['auto_start'] = True
				if self.sfile['tool'] == 'bananaglee':
					bananaglee_mod = bananaglee.BananaGlee(self.sfile, self.logger)
		                        bananaglee_mod.cmdloop()
	                elif auto[2] == True:
                                self.logger.info('going into auto mode for the end of the op')
				self.sfile['auto_end'] = True
				if self.sfile['tool'] == 'bananaglee':
	                                tunnel_mod = tunnel.Tunnel(self.sfile,self.logger)
        	                        tunnel_mod.cmdloop()
                        else:
                                self.logger.error('you specifed auto but did not tell me if it was the start or end of the op')
		else:
			self.sfile['auto'] = False

	#used to not run last command when nothing is given
	def emptyline(self):
		pass

	def complete_set_tunnel(self, text, line, begidx, endidx):
		options = ['True','False']
		return [i for i in options if i.startswith(text)]

	def do_set_tunnel(self, option):
		'''set_tunnel [True|False]
		sets if the script will handle tunneling for you'''
		if option.lower() == 'true':
			self.logger.info('Script will handle tunneling for you')
			self.sfile['do_tunnel'] = True
		elif option.lower() == 'false':
			self.logger.info('Script will not handle tunneling for you')
                        self.sfile['do_tunnel'] = False
		else:
			self.logger.error('You made an invalid selection')


	def complete_set_shelve(self, text, line, begidx, endidx):
		keys = self.sfile.keys()
		return [i for i in keys if i.startswith(text)]

	def do_set_shelve(self, option):
		'''set_shelve [KEY] [VALUE]
		sets KEY to VALUE in the shelve file'''
		self.logger.debug('user ran set_shelve')

		space = option.find(' ')
		if space == -1:
			self.logger.error('could not determine your key and value')
			return
		key = option[:space]
		value = option[space+1:]

		if key == '':
			self.logger.error('could not determine your key')
			return
		if value == '':
			self.logger.error('could not determine your value')
			return

		if self.sfile.has_key(key) == True:
			self.sfile[key] = value

			self.logger.info('Updating shelve file')
			self.logger.info('Key: ' + str(key))
			self.logger.info('Value: ' + str(value))
		else:
			self.logger.error('key does not exist, creating')
                        self.sfile[key] = value
                        self.logger.info('Key: ' + str(key))
                        self.logger.info('Value: ' + str(value))

	
	def do_show_settings(self, option):
		'''show_settings
		displays all of the current configuration settings'''
		self.logger.debug('user ran show_settings')

		tools.show_settings(self.sfile,option,self.logger)
	
	#need to redo to account for correct versions
	def do_show_tools(self, option):
		'''show_tools
		shows the support tools and versions'''
		self.logger.debug('user ran show_tools')

		for i in self.config.get('main','tools').split(','):
			self.logger.info('tool : ' + str(i))
			self.logger.info('versions : ' + str(self.config.get(i,'versions')))

	def complete_bananaglee(self, text, line, begidx, endidx):
		return [i for i in self.bg_versions if i.startswith(text)]

	def do_bananaglee(self, version):
		'''bananaglee [VERSION]
		selects the bananaglee VERSION to use'''
		self.logger.debug('user ran bananaglee')

		if version == '':
                        self.logger.error('please specify a version')
		elif version in self.bg_versions:
			self.logger.debug('selected bananaglee ' + str(version))
			self.sfile['tool'] = 'bananaglee'
			self.sfile['version'] = version
			bananaglee_mod = bananaglee.BananaGlee(self.sfile, self.logger)
			bananaglee_mod.cmdloop()
		else:
			self.logger.error('made an invalid selection: ' + str(version))

	def do_add_iprange(self, input):
		'''add_iprange [IP NETMASK] or [IP/CIDR]
		will all an IP range to use for tunneling'''
		self.logger.debug('user ran add_iprange')

		tools.cidr(self.sfile, self.logger, input)

		self.logger.debug('output from cidr')
		self.logger.debug(self.sfile['iprange'])

	def do_show_iprange(self, input):
		'''show_iprange
		will print out all the IPs to use for communication'''
		self.logger.debug('user ran show_iprange')

		if self.sfile.has_key('iprange') == False:
			self.logger.info('I do not have any IPs to use for communication')
		else:
			self.logger.info(self.sfile['iprange'])

	def do_delete_iprange(self, input):
		'''delete_iprange
		deletes all the IPs to use for communication'''
		self.logger.debug('user ran delete_iprange')

		if self.sfile.has_key('iprange') == False:
                        self.logger.info('I do not have any IPs to use for communication')
		else:
			self.logger.debug('current IPs in list: ')
			self.logger.debug(self.sfile['iprange'])
			self.logger.info('removing all IPs')
			self.sfile['iprange'] = []
			self.logger.debug('empty ip list: ' + str(self.sfile['iprange']))

	def do_exit(self, line):
		'''exit
		exits the program'''
                #reset auto
                self.sfile['auto'] = False
                self.sfile['auto_start'] = False
                self.sfile['auto_end'] = False
                self.logger.debug('exiting')
                self.logger.debug(self.sfile)
                self.sfile.close()
		sys.exit()

	def do_quit(self, line):
		'''quit 
		quits the current context'''
		#reset auto
		self.sfile['auto'] = False
		self.sfile['auto_start'] = False
		self.sfile['auto_end'] = False
		self.logger.debug('exiting')
		self.logger.debug(self.sfile)
		self.sfile.close()
		return True

if __name__ == '__main__':
	parser = OptionParser('usage: %prog [options]')
	parser.add_option('-H','--hostname',dest='hostname',type='string',help='Hostname of your target')
	parser.add_option('-t','--target',dest='target',type='string',help='Actual target IP')
	parser.add_option('--auto',dest='auto',action='store_true',help='Put script in auto mode requires --start or --end')
        parser.add_option('--start',dest='start',action='store_true',help='Tells auto mode that it is the start of the op')
        parser.add_option('--end',dest='end',action='store_true',help='Tells auto mode that it is the end of the op')

	(options, args) = parser.parse_args()
	if not options.hostname or not options.target:	
		parser.error('Incorrect number of arguments')
	hostname = options.hostname
	target = options.target
	auto = [options.auto, options.start, options.end]
	console = Console(hostname, target, auto)
	console.cmdloop()
