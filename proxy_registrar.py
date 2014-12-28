#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import socket
import sys
import SocketServer
import os.path
import time

from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class SmallSMILHandler(ContentHandler):

    def __init__(self):
        self.server = ['name', 'ip', 'puerto']
        self.database = ['path', 'paswdpath']
        self.log = ['path']
        self.tags = []

    def startElement(self, tag_name, attrs):
        if tag_name == 'server':
            dicc = {"tag_name": "server"}
            for atributo in self.server:
                dicc[atributo] = attrs.get(atributo, "")
            self.tags.append(dicc)
        elif tag_name == 'database':
            dicc = {"tag_name": "database"}
            for atributo in self.database:
                dicc[atributo] = attrs.get(atributo, "")
            self.tags.append(dicc)
        elif tag_name == 'log':
            dicc = {"tag_name": "log"}
            for atributo in self.log:
                dicc[atributo] = attrs.get(atributo, "")
            self.tags.append(dicc)

    def get_tags(self):
        return self.tags

class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
   """
   SIP server class
   """
   addresses = {}

   def register2file(self):
        """
        Escribe en un fichero la direccion, la ip y la hora limite
        """
        fich = open('register.txt', "w")
        line = "User\tIP\tPort\tExpires\r\n"
        for address in self.addresses.keys():
            time_reg = time.strftime('%Y-%m-%d %H:%M:%S', \
            time.gmtime(self.addresses[address][2]))
            line += address + "\t" + self.addresses[address][0] + "\t"
            line += self.addresses[address][1] + "\t" + time_reg + "\r\n"
        fich.write(line)

   def handle(self):
      """
      Servidor proxy y registrar
      """

      # Escribe dirección y puerto del cliente (de tupla client_address)
      print self.client_address
      while 1:
         # Leyendo línea a línea lo que nos envía el cliente
         line = self.rfile.read()
         if not line:
            break
         print "El cliente nos manda " + line
         method = line.split(" ")[0]
         if method == 'Register':
            elements = line.split()
            address = (elements[1].split(":"))[1]
            expires = int(elements[-1])
            if expires > 0:
               reg_time = float(expires) + time.time()
               port_client = elements[1].split(":")[2]
               self.addresses[address] = (self.client_address[0], port_client, reg_time)
               self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
            elif expires == 0:
               if address in self.addresses:
                  del self.addresses[address]
                  self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
               else:
                  self.wfile.write("SIP/2.0 404 User Not Found\r\n\r\n")
            
            for address in self.addresses.keys():
                if self.addresses[address][2] < time.time():
                    del self.addresses[address]
            print self.addresses
            self.register2file()

if __name__ == "__main__":
   # Comprobación de la linea de argumentos
   if len(sys.argv) != 2:
      sys.exit('Usage: python proxy_registrar.py config')
   if not os.path.exists(sys.argv[1]):
      sys.exit("El archivo " + sys.argv[1] + " no existe")

   # Obtención de datos del fichero xml
   fich = open(sys.argv[1])
   parser = make_parser()
   sHandler = SmallSMILHandler()
   parser.setContentHandler(sHandler)
   parser.parse(fich)
   list_tags = sHandler.get_tags()

   # Creamos servidor de sip y escuchamos
   serv = SocketServer.UDPServer(("", int(list_tags[0]['puerto'])), 
   SIPRegisterHandler)
   print 'Server ', list_tags[0]['name'], ' listening at port ', 
   print list_tags[0]['puerto'] 
   serv.serve_forever()
