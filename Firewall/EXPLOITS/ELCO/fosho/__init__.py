#!/usr/bin/env python2.7

import logging
import sys
import os
import types
import socket
import readline
import copy
import traceback

from StringIO import StringIO
from cmd import Cmd
from argparse import ArgumentParser,ArgumentTypeError,SUPPRESS
from requests import Session,Request
from random import choice,seed
from string import ascii_letters
from time import time,strftime
from json import dump,load
from shlex import split
from urlparse import urlparse

##

##

##

##

try:   ##

    from http.client import HTTPConnection
except ImportError:
    from httplib import HTTPConnection
HTTPConnection.debuglevel=1

##

def randstr(l):
    ''''''

    return "".join([choice(ascii_letters) for i in range(0,l)])

def is_url(url):
    ''''''

    try:
        p = urlparse(url)
        if p.scheme not in ['http','https']:
            raise ArgumentTypeError("Protocol must be either http or https (Ex: https://1.2.3.4:1234)")
        try:
            host,port = p.netloc.split(":")
            port = int(port)
            is_ip_addr(host)
        except:
            raise ArgumentTypeError("Must specify host IP and port. (Ex: https://1.2.3.4:1234)")
        return "%s://%s:%s" % (p.scheme,host,port)
    except:
            raise ArgumentTypeError("Invalid URL. Should be formatted as follows: https://1.2.3.4:1234")

def is_ip_addr(ip):
    ''''''

    try:
        socket.inet_aton(ip)
        return ip
    except:
        raise ArgumentTypeError("%r is not an IP address!" % ip)

def is_target(t):
    ''''''

    if t == None:
        return ""
    parts = t.split(":")
    try:
        ip = is_ip_addr(parts[0])
        if len(parts) > 1:
            port = int(parts[1])
        return t
    except Exception as e:
        raise ArgumentTypeError("%r is not a valid target!" % t)

##

def excmd(fn):
    ''''''

    def wrapped(self,*fnargs):
        try:
            args = []
            args.extend(self.required_all)
            fn_name = fn.__name__[3:]
            if hasattr(self,"required_"+fn_name):
                args.extend(getattr(self,"required_"+fn.__name__[3:]))
            self.prompt_for_settings(args)
            self.do_show()
            if self.ask:
                while 1:
                    res = raw_input("Do these settings look correct? (y[es]/N[o]/s[kip]/q[uit]) ")
                    if res.lower() in ["s","y"]:
                        break
                    elif res.lower() == "q":
                        return 1
                    else:
                        self.prompt_for_settings(args)
            print args
            print self.ns
            for name in args: 
                if not hasattr(self.ns,name) or not getattr(self.ns,name):
                    r = raw_input("Variable %s is not set. Enter IGNORE to continue anyways (warning: bad things will happen): " % name)
                    if r != "IGNORE":
                        return

                            
            if not self.ask or res.lower() == "y":
                res = None
                if hasattr(self,"mode") and hasattr(self,"build_%s_%s_payload"%(self.mode,fn_name)):
                    res = getattr(self,"build_%s_%s_payload"%(self.mode,fn_name))()
                elif hasattr(self,"build_%s_payload"%fn_name):
                    res = getattr(self,"build_%s_payload"%fn_name)()
                if res:
                    self.log.error("An error occurred while building the payload: %s" % res)
                    return
                res = fn(self,*fnargs)
                self.payload = None
            else:
                self.log.warning("Action cancelled. Fix settings and try again.")
        except Exception,e:
            self.log.error("Error occurred during exploit: %s" % e)
            self.log.error("Traceback: %s" % traceback.format_exc())
    wrapped.__name__ = fn.__name__
    return wrapped

##

class ConsoleHandler(logging.StreamHandler):
    ''''''

    def emit(self,record):
        myrecord = copy.copy(record)
        levelno = myrecord.levelno
        c = "+"
        if levelno >= 30:
            c = "-"
        myrecord.msg = "[%s] "%c + str(myrecord.msg)
        logging.StreamHandler.emit(self,myrecord)

class ColoredConsoleHandler(logging.StreamHandler):
    ''''''

    def emit(self,record):
        myrecord = copy.copy(record)
        levelno = myrecord.levelno
        if levelno >= 50: ##

            color = '\x1b[31m;' ##

        elif levelno >= 40: ##

            color = '\x1b[31m' ##

        elif levelno >= 30: ##

            color = '\x1b[33m' ##

        elif levelno >= 20: ##

            color = '\x1b[32m' ##

        elif levelno >= 10: ##

            color = '\x1b[35m' ##

        else:
            color = '\x1b[0m'
        c = "+"
        if levelno >= 30:
            c = "-"
        myrecord.msg = color + "[%s] "%c + str(myrecord.msg) + '\x1b[0m'
        logging.StreamHandler.emit(self,myrecord)

##

class TeeStdout(object):
    ''''''

    def __init__(self,fd,debug=False):
        self.stdout = sys.stdout
        self.fd = fd
        sys.stdout = self
        self.debug = debug
    def write(self,text):
        ##

        if len(text) > 2000: text = text[:2000] + ("."*((len(text)-2000)%1000))
        self.fd.write(text)
        if self.debug:
            self.stdout.write(text)
    def flush(self):
        self.fd.flush()
        self.stdout.flush()

class ExitException(Exception):
    pass

##

class HTTPExploit(Session,Cmd):
    ''''''

    port = 80
    proto = "http"
    modes = ["nopen"]
    desc = "Ride the walrus!"
    name = "Generic HTTP Exploit"
    version = "" 
    excmds = ["touch","probe","survey","exploit","clean"]
    required_all = ["target"]
    required_exploit = ["binpath","callback","mode"]
    target_url = "/"
    host = ""
    timeout = 200
    cfg = "tool.cfg"
    logdir = "/current/down/fosho"
    interact = False
    guided = False

    proto_map = {"80":"http","443":"https"}
    def __init__(self,ns,parsers,multi=False,**kwargs):
        ''''''

        self.prompt = "(%s) > " % self.name
        self.ns = ns
        self.parsers = parsers
        self.payload = None
        self.action_help = {}
        self.action_types = {}

        for parser in self.parsers:
            for a in parser._actions:
                self.action_help[a.dest] = a.help
                self.action_types[a.dest] = a.type

        self.multi=multi
        self.payload=None

        if not ns.host:
            ns.__dict__['host'] = " "

        ##

        if not hasattr(ns,"mode") or not ns.mode:
            ns.__dict__['mode'] = self.modes[0]

        ##

        for key in ns.__dict__:
            if not ns.__dict__[key] and hasattr(self,key):
                ns.__dict__[key] = getattr(self,key)

        self.log = logging.getLogger(self.name)
        if not os.path.isdir("/current/down"):
            self.logdir = "logs"
        if not os.path.isdir(self.logdir):
            os.makedirs(self.logdir)
        self.logbase = strftime("%Y-%m-%d-%H%M%S") 
        self.logbase = os.path.join(self.logdir,self.logbase)
        hndl = logging.FileHandler(self.logbase+".log")
        hndl.setLevel(logging.DEBUG)
        self.log.addHandler(hndl)
        logging.getLogger("fosho.requests.packages.urllib3.connectionpool").addHandler(hndl)
        self.httplog = open(self.logbase+"_http.log","w")


        Session.__init__(self,**kwargs)
        self._apply_settings()
        Cmd.__init__(self)

    def cmdloop(self,**kwargs):
        ''''''

        try:
            Cmd.cmdloop(self,**kwargs)
        ##

        except ExitException as e:
            return
        except Exception as e:
            self.log.error("cmdloop caught error: %s" % e)
            self.continue_prompt("A critical error occurred. Would you like to keep this shell open?")
            self.cmdloop(**kwargs)

    def do_help(self, arg):
        ##

        ##

        ##

        ##

        ##

        ##

        ##

        ##

        ##


        if arg:
            ##

            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc=getattr(self, 'do_' + arg).__doc__
                    if doc:
                        self.stdout.write("%s\n"%str(doc))
                        return
                except AttributeError:
                    pass
                self.stdout.write("%s\n"%str(self.nohelp % (arg,)))
                return
            func()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]]=1
            names.sort()
            ##

            prevname = ''
            for name in names:
                if name[:3] == 'do_' and (name[3:] in names or                    name[3:] not in self.excmds):
                    if name == prevname:
                        continue
                    prevname = name
                    cmd=name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            self.stdout.write("%s\n"%str(self.doc_leader))
            self.print_topics(self.doc_header,   cmds_doc,   15,80)
            self.print_topics(self.misc_header,  help.keys(),15,80)
            self.print_topics(self.undoc_header, cmds_undoc, 15,80)

    def _do_prep(self):
        self.log.debug("Preparing to run specified command...")
        if hasattr(self,"prep"):
            self.prep()

    @excmd
    def do_touch(self,arg=None):
        ''''''

        res,resp = [],None
        if hasattr(self,"target_url") and self.target_url:
            resp = self.head(self.target_url)
            res.append("HEAD %s - %s" % (self.target_url,resp.status_code))
            for key,val in resp.headers.items():
                res.append("Header: %s -- %s" % (key,val))

        tres = self.touch(resp)
        if len(res) > 0:
            for i in res:
                self.log.info("Touch result: %s" % i)
        if type(tres) == type([]):
            for i in res:
                self.log.info("Touch result: %s" % i)
        elif tres:
            self.log.error("Touch returned an error")
            self.log.error("Reason given: %s" % res)

    @excmd
    def do_probe(self,arg=None):
        ''''''

        res = self.probe()
        if not res:
            self.log.info("Target is vulnerable. Safe to proceed.")
        else:
            self.log.error("Target appears not to be vulnerable.")
            self.log.error("Reason given: %s" % res)

    @excmd
    def do_survey(self,arg=None):
        ''''''

        res = self.survey()
        if not res:
            self.log.info("Survey complete.")
        else:
            self.log.error("Survey failed.")
            self.log.error("Reason given: %s" % res)

    @excmd
    def do_exploit(self,arg=None):
        ''''''

        res = self.exploit()
        if not res:
            self.log.info("Exploit complete. Got root?")
        else:
            self.log.error("Exploit failed")
            self.log.error("Reason given: %s" % res)

    @excmd
    def do_clean(self,arg=None):
        ''''''

        res = self.clean()
        if not res:
            self.log.info("Cleanup completed successfully.")
        else:
            self.log.error("Cleanup failed: %s" % res)

    def do_quit(self,arg):
        raise ExitException()

    def _save_session(self,fn):
        try:
            f = open(fn,"wb")
        except IOError:
            self.log.error("Couldn't open session file. Exiting...")
            return

        self.log.info("Saving session info to %s" % fn)

        ##

        for name in self.ns.__dict__:
            try:
                self.ns.__dict__[name] = getattr(self,name)
            except AttributeError:
                continue

        ##

        for name in ["func","config"]:
            if name in self.ns.__dict__:
                del self.ns.__dict__[name]

        dump(self.ns.__dict__,f)
        f.close()
        
        self.log.info("Log files saved to %s.log and %s_http.log" % 
                    (self.logbase,self.logbase))
    def _do_finish(self):
        if hasattr(self,"finish"):
            self.finish()

        if self.session:
            self._save_session(self.session)
        self._save_session(".last_session")

    def do_show(self,args=None):
        ''''''



        if args:
            args = args.strip()
            try:
                print "%s = %s :: %s" %                        (args,self.ns.__dict__[args],self.action_help[args])
            except KeyError:
                self.log.warning("Variable does not exist.")
        else:
            print "Exploit variables"
            print "========================="
            for key,val in self.ns.__dict__.items():
                if key not in self.action_help:
                    self.action_help[key] = 'No help available'
                if key not in ["func","config","load"]:
                    print "   %s = %s :: %s" % (key,val,self.action_help[key])

    def do_set(self,args):
        ''''''

        if args:
            args = split(args)
            if len(args) >= 2:
                if args[0] in self.ns.__dict__:
                    try:
                        self._update_var(args[0],args[1])
                    except ArgumentTypeError as e:
                        self.log.warning("Setting %s failed: %s" % (args[0],e))
                else:
                    self.log.warning("Variable %s does not exist" % args[0])
            else:
                self.log.warning("Inavlid command syntax. Please see help for usage.")
        self._apply_settings()

    def do_guided(self,args=None):
        ''''''

        for cmd in self.excmds:
            if cmd in dir(self):
                res = raw_input("About to execute %s. Continue, skip, interact, or quit? (C/s/i/q) " % cmd)
                if res.lower() == "s":
                    continue
                elif res.lower() == "q":
                    return
                elif res.lower() == "i":
                    self.cmdloop()
                    res = raw_input("Done interacting, about to execute %s. Continue, skip, or quit? (C/s/q) " % cmd)
                    if res.lower() == "s":
                        continue
                    if res.lower() == "q":
                        return
                    else:
                        if getattr(self,"do_"+cmd)(): return
                else:
                    if getattr(self,"do_"+cmd)(): return
        res = raw_input("Finished executing commands. Quit or enter interactive mode? (Q/i) ")
        if res.lower() == "i":
            self.cmdloop()
                

    def request(self,mthd,url,**kwargs):
        ''''''

        ##

        ##

        ##


        quiet = False
        if "quiet" in kwargs:
            quiet = kwargs['quiet']
            del kwargs['quiet']

        if quiet:
            l = logging.getLogger("fosho.requests.packages.urllib3.connectionpool")
            old = l.getEffectiveLevel()
            l.setLevel(logging.ERROR)

        if not self.multi:
            ##

            url = self.target+url

        self.log.debug("Requesting %s %s with following provided settings: %s" % (mthd,url,kwargs))

        ##

        ##

        ##


        if self.ns.host:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            if "host" not in kwargs['headers']:
                kwargs['headers']['Host'] = self.host
        kwargs['config']={}

        ##

        ##

        httplog = StringIO()
        stdout = sys.stdout
        t = TeeStdout(httplog,self.debug)

        try:
           resp = Session.request(self,mthd,url,**kwargs)
        except Exception as e:
            self._restore_stdout(httplog,stdout)
            if 'ignore_errors' in kwargs and kwargs['ignore_errors']:
                return
            if not quiet:
                self.log.error("Exception occurred during request: %s" % e)
            else:
                l.setLevel(old)
            ##

            raise e

        if quiet:
            l.setLevel(old)

        print "body: %s" % repr(resp.content)
        self._restore_stdout(httplog,stdout)
        return resp
        
    def prompt_for_settings(self,names):
        ''''''

        for name in names:
            try:
                res = getattr(self,"_get_"+name)()
            except AttributeError as e:
                res = None
            if not hasattr(self.ns,name):
                self.ns.__dict__[name] = None
            if not self.ask and not res:
                res = self.ns.__dict__[name]
            if not res and self.ask:
                res = raw_input("%s [%s]: " % (name,self.ns.__dict__[name]))
                if not res:
                    continue
            elif self.ask:
                res2 = raw_input("%s [%s]: " % (name,res))
                if res2.strip() != "":
                    res = res2
            ##

            self._update_var(name,res)
            self._apply_settings()

    def continue_prompt(self,msg,default="n"):
        ''''''

        other = "y" if default == "n" else "n"
        opts = "(y/n)".replace(default,default.upper())
        res = raw_input("%s %s " % (msg,opts))
        if res.lower() != "y":
            ##

            try:
                self._do_finish()
            except:
                pass
            sys.exit("Stopping exploit...")

    def get_etag(self,path):
        ''''''

        res = self.head(path)
        return self._parse_etag(res.headers['etag'])
    
   ##

   ##


    def _parse_etag(self,etag):
        ''''''

        return etag,"Could not parse etag"

    def _apply_settings(self):
        ''''''

        ##

        for key,val in self.ns.__dict__.items():
            if key in ['quiet','debug']:
                level = logging.DEBUG
                if self.ns.quiet:
                    level = logging.INFO
                self.log.setLevel(level)
                ##

                ##

                logging.getLogger("fosho.requests.packages.urllib3.connectionpool").setLevel(level)
                if key == "debug":
                    self.debug = val and not self.ns.quiet
            elif key not in ["config","func"]:
                setattr(self,key,val)
        ##


    def _update_var(self,key,val):
        ''''''

        ##

        if val == "False": val = False

        cur = self.ns.__dict__[key]
        ##

        if cur == None: cur = ""

        ##

        t = type(self.ns.__dict__[key])

        if key in self.action_types and self.action_types[key]:
            t = self.action_types[key]

        try:
            self.ns.__dict__[key] = t(val)
        except TypeError:
            self.ns.__dict__[key] = None

    def _restore_stdout(self,httplog,stdout):
        httplog.seek(0)
        for line in httplog.readlines():
            if line.split(":")[0] in ["send","reply","header","body"]:
                self.httplog.write(line)

        self.httplog.flush()
        sys.stdout = stdout

    @classmethod
    def add_args(cur,cls):
        ''''''

        parser = ArgumentParser(prog=sys.argv[0],description="%s %s - %s" % (cls.name,cls.version,cls.desc))
        subparsers = parser.add_subparsers(help="Exploit Commands")
        if cls.interact:
            inparse = subparsers.add_parser("interact",
                            help="Run tool in interactive mode")
            inparse.set_defaults(func=cls.cmdloop)
        if cls.guided:
            gdparse = subparsers.add_parser("guided",
                            help="Run tool in guided mode")
            gdparse.set_defaults(func=cls.do_guided)
        if hasattr(cls,"touch"):
            tparse = subparsers.add_parser("touch",
                    help="Touch target and return targeting information.")
            tparse.set_defaults(func=cls.do_touch)
        if hasattr(cls,"probe"):
            vparse = subparsers.add_parser("probe",
                    help="Check if target is vulnerable.")
            vparse.set_defaults(func=cls.do_probe)
        if hasattr(cls,"survey"):
            iparse = subparsers.add_parser("survey",
                    help="Gather useful information from target.")
            iparse.add_argument("-w","--outfile",type=str,
                    help="File to save target information to. (default: out.tar)")
            iparse.add_argument("-s","--script",type=str,
                    help="Survey script to run on server.")
            iparse.set_defaults(func=cls.do_survey)
        if hasattr(cls,"exploit"):
            eparse = subparsers.add_parser("exploit",
                    help="Exploit target.")
            eparse.add_argument("--mode",choices=cls.modes,
                    help="Mode to use against target")
            eparse.add_argument("-p","--binpath",default=None,
                    help="Path to tool being used.")
            eparse.add_argument("-c","--callback",type=is_target,
                    help="Callback IP:Port for tool (Example: 127.0.0.1:12345)")
            eparse.set_defaults(func=cls.do_exploit)
        if hasattr(cls,"clean"):
            cparse = subparsers.add_parser("clean",
                    help="Do clean after exploit.")
            cparse.set_defaults(func=cls.do_clean)

        ggroup = parser.add_argument_group("Generic Exploit Options")
        ggroup.add_argument("--quiet",action="store_true",
                    help="Disable verbose logging")
        ggroup.add_argument("--debug",action="store_true",
                    help="Enable debug output. (Warning: prepare for spam)")
        ggroup.add_argument("-a","--ask",action="store_true",
                    help="Enable confirmation prompting before running commands.")
        ggroup.add_argument("--color",action="store_true",
                    help="Enable log output colors.")
        ggroup.add_argument("-l","--loadlast",action="store_true",
                    help="Load last session used.")
        ggroup.add_argument("-s","--session",type=str,
                    help="Use specified session file.")
        ggroup.add_argument("-t","--target",type=is_url,
                    help="Target to exploit. (Ex: https://127.0.0.1:1234)")
        ##


        hgroup = parser.add_argument_group("HTTP Options")
        hgroup.add_argument("--timeout",type=int,
                    help="Socket timeout")
        hgroup.add_argument("--host",type=str,
                    help="Host header to use (default: empty")
        return parser,subparsers


class HTTPSExploit(HTTPExploit):
    name = "Generic HTTPS Exploit"
    proto = "https"
    port = 443

    @classmethod
    def add_args(cur,cls):
        parser,subparsers = HTTPExploit.add_args(cls)
        sgroup = parser.add_argument_group("SSL Options")
        sgroup.add_argument("--verify",action="store_true",default=False,
                help="Enable SSL verification")
        ##

        ##

        sgroup.add_argument("--cert",type=str,
                help="CA File",default=None)
        return parser,subparsers

def setup_logger(ns):
    level = logging.DEBUG
    if ns.quiet:
        level = logging.INFO
    logging.basicConfig(level=level)

    if ns.color:
        h = ColoredConsoleHandler()
    else:
        h = ConsoleHandler()

    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    root.addHandler(h)

    return root 
    
def load_config(fn,ns):
    try:
        conf = load(open(fn,"rb"))
        for key,val in conf.items():
            if key not in ns or (not ns.__dict__[key] and val):
                ns.__dict__[key] = val
        root = setup_logger(ns)
    except IOError:
        root = setup_logger(ns)
        if ns.session:
            root.warning("Configuration file %s not found. Creating empty config file." % ns.session)
    return root
    

def run_exploit(cls):
    ''''''

    

    parser,subparser = cls.add_args(cls)
    ns = parser.parse_args()

    ##

    root = None
    if ns.loadlast:
        load_config(".last_session",ns)
    if ns.session:
        load_config(ns.session,ns)
    if os.path.exists(cls.cfg):
        root = load_config(cls.cfg,ns)
    if not root:
        root = setup_logger(ns)
 
    s = time()
    seed(s)
    root.debug("Seeded PRNG with %s" % s)

    obj = cls(ns,[parser]+subparser.choices.values())
    obj._do_prep()
    types.MethodType(ns.func,obj,cls)()
    obj._do_finish()

def main():
    parser,subparsers = build_args(HTTPExploit)
    
    parser.parse_args()
if __name__=="__main__":
    main()
