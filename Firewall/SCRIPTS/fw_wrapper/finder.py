
import ConfigParser
import os
import logging
import fw_logging
import sys
import shelve

def finder(hostname,target):
        #set up logging
        name = 'finder'
        logger = fw_logging.getLogger(logging.DEBUG,name,hostname,target)

	#Parse out config file
        config = ConfigParser.ConfigParser()
        config.read('fw_wrapper.cfg')
	try:
		my_dir = config.get('main','script_dir')
	except:
		logger.exception('could not read my_dir in the main section of the config file')
		sys.exit()
	
	tool_file = file(os.path.join(my_dir,'tools.cfg'), 'w+')

	try:
		root_path = config.get('main','root_path')
	except:
		logger.exception('could not read the root_path in the main section of the config')
		sys.exit()

	try:
		tools = config.get('main','tools')
	except:
		logger.exception('could not read the tools section in the main config')
		sys.exit()

	try:
		log_dir = config.get('main','log_dir')
	except:
		logger.exception('could not read the log_dir section in the main config')
		sys.exit()

	try:
		fg_dir = config.get('main','fg_dir')
	except:
		logger.exception('could not read the fg_dir section in the main config')
		sys.exit()

	#do for each tool
	for i in tools.split(','):
		logger.debug('building dictonary for ' + str(i))
		#look up all version for that tool
		try:
			tool_versions = config.get(i,'versions')
		except:
			logger.exception('could not get the version from the ' + str(i) + ' section in the main config')
			sys.exit()

		#do for each version
		for j in tool_versions.split(','):
			logger.debug('building for version ' + str(j))
			toolversion = str(i) + str(j)
			#look up the folder for each version
			try:
				folder = config.get(toolversion,'folder')
			except:
				logger.exception('could not look up folder in ' + str(i) + str(j) + ' section in the main config')
				sys.exit()

			tool_dir = os.path.join(root_path, folder)
			tool_dict = {} 
			tool_file.write('[' + i + j + ']\r\n')
                        mod_list = []
			#do recursive dir and build dict
			for root, dirs, files, in os.walk(os.path.abspath(tool_dir)):
				for f in files:
                		        tool_dict[f] = os.path.join(root, f)
					#if tool is bananaglee parse out each mod file
					if i == 'bananaglee':
						if '.mod' in f:
							mod_file = f
							mod_path = os.path.join(root, f)
							with open(mod_path,'r') as a:
								output = a.readlines()
							commands = []
							for b in output:
								if b.startswith('Name') == True:
									name = b.split(' ')[1].rstrip('\r\n')
								elif b.startswith('ID') == True:
									id_tmp = b.split(' ')[1].rstrip('\r\n')
									if str(id_tmp[:2]) == '0x':
										id = id_tmp 
									else:
										id = hex(int(id_tmp))
								elif b.startswith('Command') == True:
									temp = b.split(' ')[1].rstrip('\r\n')
									commands.append(temp.rstrip('\r\n'))
							num_commands = len(commands)
							mod_list.append(str(name))
							#write parsed results to tools.cfg			
							tool_file.write(str(name) + '_commands = ' + str(commands) + '\r\n')
							tool_file.write(str(name) + '_num_commands = ' + str(num_commands) + '\r\n')
							tool_file.write(str(name) + '_ID = ' + str(id) + '\r\n')
							tool_file.write(str(name) + '_mod_file = ' + str(mod_file) + '\r\n')
							tool_file.write(str(name) + '_mod_path = ' + str(mod_path) + '\r\n')
							
			tool_file.write('modules = ' + str(mod_list) + '\r\n')					
			#lookup binaries that i need to know about
			try:
				binaries = config.get(toolversion,'binaries')
			except:
				logger.exception('could not look up binaries in the ' + str(toolversion) + ' section in the main config')
				sys.exit()
		
			#for each binary look up the full path and write out to tools.cfg	
			for k in binaries.split(','):
				try:
					binary = config.get(toolversion, k)
				except:
					logger.exception('could not lookup ' + str(k) + ' in ' + str(toolversion) + ' in the main config')
					sys.exit()

				tool_file.write(str(k) + ' = ' + tool_dict[str(binary)] + '\r\n')
	
	#find config files and move them to the logging directory		
        files_to_move = []
        for root, dirs, files in os.walk(os.path.abspath(fg_dir)):
                for f in files:
                        if 'firewall_' in f:
                                if f[-3:] == '.cfg':
                                        logger.debug('found: ' + os.path.join(root,f))
                                        files_to_move.append(os.path.join(root,f))

        #copy files to log_dir
        if len(files_to_move) > 0:
                for i in files_to_move:
                        shutil.copy2(i,log_dir)
                else:
                        logger.info('***no config files were found***')

