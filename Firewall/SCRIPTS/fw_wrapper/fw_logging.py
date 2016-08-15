
import logging
import os
import ConfigParser

def getLogger(level,name,host,ip):
	config = ConfigParser.ConfigParser()
	config.read('fw_wrapper.cfg')

	log_dir = '/current/down/' 
	log_file = 'firewall_' + str(host) + '.' + str(ip) + '.log'
	
        if not os.path.exists(log_dir): # creates log dir
        	os.makedirs(log_dir)

	logger = logging.getLogger(name)
	logger.setLevel(level)
	
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s','%Y-%m-%d %H:%M:%S')

	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	
	fh = logging.FileHandler(os.path.join(log_dir,log_file))
	fh.setLevel(logging.DEBUG)
	fh.setFormatter(formatter)
	logger.addHandler(fh)

	return logger
