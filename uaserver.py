#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import socket
import sys
import os.path
import SocketServer

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

class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            print "El cliente nos manda " + line
            method = line.split(" ")[0]
            if method == 'Invite':
               audio_port = line.split(" ")[-2]
               audio_ip = line.split(" ")[-3].split("\r\n")[0]
               if not list_tags[1]['ip']:
                  list_tags[1]['ip'] = '127.0.0.1'
               SDP = 'v=0\r\no=' + list_tags[0]['username'] + ' '
               SDP += list_tags[1]['ip'] + '\r\ns=misesion\r\nt=0\r\n'
               SDP += 'm=audio ' + list_tags[2]['puerto'] + ' RTP\r\n\r\n' 
               new_line = 'SIP/2.0 100 Trying\r\n\r\nSIP/2.0 180 Ringing'
               new_line += '\r\n\r\nSIP/2.0 200 OK\r\n'
               new_line += 'Content-Type: aplication/sdp\r\n\r\n' + SDP
               self.wfile.write(new_line)

if __name__ == "__main__":
	# Comprobación de la linea de argumentos
   if len(sys.argv) != 2:
      sys.exit('Usage: python uaclient.py config method option')

   if not os.path.exists(sys.argv[1]):
      sys.exit("El archivo " + sys.argv[1] + " no existe")
   
   # Obtención de datos del fichero xml
   fich = open(sys.argv[1])
   parser = make_parser()
   sHandler = SmallSMILHandler()
   parser.setContentHandler(sHandler)
   parser.parse(fich)
   list_tags = sHandler.get_tags()
   
   # Servidor
   serv = SocketServer.UDPServer(("", int(list_tags[1]['puerto'])), EchoHandler)
   print "Listening..."
   serv.serve_forever()
