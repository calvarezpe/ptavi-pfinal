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
        fich = open(list_tags[1]['path'], "w")
        line = "User\tIP\tPort\tRegister time\tExpires\r\n"
        for address in self.addresses.keys():
            line += address + "\t" + self.addresses[address][0] + "\t"
            line += self.addresses[address][1] + "\t"
            line += str(self.addresses[address][2]) + "\t"
            line += str(self.addresses[address][3]) + "\r\n"
        fich.write(line)

   def handle(self):
      """
      Servidor proxy y registrar
      """
      while 1:
         # Comprobar si ha caducado alguno
         for address in self.addresses.keys():
            time_expires = self.addresses[address][2] + self.addresses[address][3]
            if time_expires < time.time():
               del self.addresses[address]

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
               port_client = elements[1].split(":")[2]
               self.addresses[address] = (self.client_address[0], port_client, time.time(), float(expires))
               self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
            elif expires == 0:
               if address in self.addresses:
                  del self.addresses[address]
                  self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
               else:
                  self.wfile.write("SIP/2.0 404 User Not Found\r\n\r\n")
            # Escribimos en el fichero
            self.register2file()

         if method == 'Invite':
            address_invited = line.split()[1].split(":")[1]
            if not address_invited in self.addresses:
               self.wfile.write("SIP/2.0 404 User Not Found\r\n\r\n")
               print "Usuario no registrado"
            elif address_invited in self.addresses:
               print "Comienza la fiesta"

               UAServerIP = self.addresses[address_invited][0]
               UAServerPort = self.addresses[address_invited][1]
               print 'lo mandamos a ', UAServerIP, '-', UAServerPort
               my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
               my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
               my_socket.connect((UAServerIP, int(UAServerPort)))
               print 'Vamos a mandar: ', line
               try:
                  my_socket.send(line)
               except socket.error:
                  print 'Error: no server listening'

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
