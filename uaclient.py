#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import socket
import sys

from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class SmallSMILHandler(ContentHandler):

    def __init__(self):
        self.account = ['username', 'passwd']
        self.uaserver = ['ip', 'puerto']
        self.rtpaudio = ['puerto']
        self.regproxy = ['ip', 'puerto']
        self.log = ['path']
        self.audio = ['path']
        self.tags = []

    def startElement(self, name, attrs):
        if name == 'account':
            dicc = {"name": "account"}
            for atributo in self.account:
                dicc[atributo] = attrs.get(atributo, "")
            self.tags.append(dicc)
        elif name == 'uaserver':
            dicc = {"name": "uaserver"}
            for atributo in self.uaserver:
                dicc[atributo] = attrs.get(atributo, "")
            self.tags.append(dicc)
        elif name == 'rtpaudio':
            dicc = {"name": "rtpaudio"}
            for atributo in self.rtpaudio:
                dicc[atributo] = attrs.get(atributo, "")
            self.tags.append(dicc)
        elif name == 'audio':
            dicc = {"name": "audio"}
            for atributo in self.audio:
                dicc[atributo] = attrs.get(atributo, "")
            self.tags.append(dicc)
        elif name == 'log':
            dicc = {"name": "log"}
            for atributo in self.log:
                dicc[atributo] = attrs.get(atributo, "")
            self.tags.append(dicc)
        elif name == 'regproxy':
            dicc = {"name": "regproxy"}
            for atributo in self.regproxy:
                dicc[atributo] = attrs.get(atributo, "")
            self.tags.append(dicc)

    def get_tags(self):
        return self.tags

if __name__ == "__main__":
   method_list = ['Register', 'Invite', 'Bye']
   if len(sys.argv) != 3:
      sys.exit('Usage: python uaclient.py config method option')
      
   method = sys.argv[2]
   if not method in method_list:
      sys.exit('Usage: python uaclient.py config method option')
   
   fich = open(sys.argv[1])
   parser = make_parser()
   sHandler = SmallSMILHandler()
   parser.setContentHandler(sHandler)
   parser.parse(fich)
   list_tags = sHandler.get_tags()
   print list_tags

