#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import socket
import sys
import os.path

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
	# Comprobación de la linea de argumentos
   method_list = ['Register', 'Invite', 'Bye']
   if len(sys.argv) != 4:
      sys.exit('Usage: python uaclient.py config method option')
      
   method = sys.argv[2][0].upper() + sys.argv[2][1:].lower()
   if not method in method_list:
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
   
   #Socket
   SERVER_IP = str(list_tags[3]['ip'])
   if not SERVER_IP:
      SERVER_IP = '127.0.0.1'
   SERVER_PORT = int(list_tags[3]['puerto'])
   
   # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
   my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   my_socket.connect((SERVER_IP, SERVER_PORT))
   
   #Envio
   if method == 'Register':
      LINE = method + " sip:" + list_tags[0]['username'] + ':' 
      LINE += list_tags[1]['puerto'] + ' SIP/2.0\r\nExpires: ' + sys.argv[3]
      LINE += '\r\n\r\n'
      
   try:
      print "Enviando: " + LINE
      my_socket.send(LINE)
      data = my_socket.recv(1024) #RECIBO
      print 'Recibido -- ', data
      data_list = data.split(" ")
   except socket.error:
      print "Error: No server listening at ", SERVER_IP, " port ",
      print str(SERVER_PORT)

   # Cerramos todo
   my_socket.close()
