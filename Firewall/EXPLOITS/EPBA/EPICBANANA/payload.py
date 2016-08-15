from params import *


class Payload:
    def __init__(self, params):
        self.params = params

    ##
    def load_version_module(self):
        self.vers_module_name = "%s" % self.params.target_vers
        try:
            self.version_module = __import__(self.vers_module_name)
            return True
        except ImportError:
            print "can't find target version module!"
            return False

    ##
    def get_payload(self):
        return self.version_module.payload(self.params)
