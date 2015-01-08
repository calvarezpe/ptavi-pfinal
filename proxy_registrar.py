#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import socket
import sys
import SocketServer
import os.path
import time

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

def WriteLog (Mensaje):
    hora = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
    log.write(hora + " " + Mensaje + "\r\n")

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
            method_list = ['Register', 'Invite', 'Ack', 'Bye']
            head = line.split("\r\n")[0]
            head_list = head.split(" ")
            sip = head_list[1].split(":")[0]
            aLog = "Received from " + self.client_address[0] + ":"
            aLog += str(self.client_address[1]) + ":" + head
            WriteLog(aLog)
            if len(head_list) == 3 and head_list[2] == "SIP/2.0" and sip == "sip":
                if method in method_list:
                    if method == 'Register':
                        elements = line.split()
                        address = (elements[1].split(":"))[1]
                        expires = int(elements[-1])
                        if expires > 0:
                            port_client = elements[1].split(":")[2]
                            self.addresses[address] = (self.client_address[0], port_client, time.time(), float(expires))
                            aEnviar = "SIP/2.0 200 OK"
                            self.wfile.write(aEnviar + "\r\n\r\n")
                            aLog = "Sent to " + self.client_address[0]
                            aLog += ":" + str(self.client_address[1])
                            aLog += ": " + aEnviar
                            WriteLog(aLog)
                        elif expires == 0:
                            if address in self.addresses:
                                del self.addresses[address]
                                aEnviar = "SIP/2.0 200 OK"
                                self.wfile.write(aEnviar + "\r\n\r\n")
                                aLog = "Sent to " + self.client_address[0]
                                aLog += ":" + str(self.client_address[1])
                                aLog += ": " + aEnviar
                                WriteLog(aLog)
                        else:
                            aEnviar = "SIP/2.0 404 User Not Found"
                            self.wfile.write(aEnviar + "\r\n\r\n")
                            aLog = "Sent to " + self.client_address[0] + ":"
                            aLog += str(self.client_address[1]) + ": "
                            aLog += aEnviar
                            WriteLog(aLog)
                        # Escribimos en el fichero
                        self.register2file()

                    if method == 'Invite':
                        address_invited = line.split()[1].split(":")[1]
                        if not address_invited in self.addresses:
                            aEnviar = "SIP/2.0 404 User Not Found"
                            self.wfile.write(aEnviar + "\r\n\r\n")
                            aLog = "Sent to " + self.client_address[0] + ":"
                            aLog += str(self.client_address[1]) + ": "
                            aLog += aEnviar
                            WriteLog(aLog)
                        elif address_invited in self.addresses:
                            UAServerIP = self.addresses[address_invited][0]
                            UAServerPort = self.addresses[address_invited][1]
                            print 'lo mandamos a ', UAServerIP, '-', UAServerPort
                            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            my_socket.connect((UAServerIP, int(UAServerPort)))
                            print 'Vamos a mandar: ', line
                            aLog = "Sent to " + UAServerIP + ":" + UAServerPort
                            aLog += ": " + line.split("\r\n")[0]
                            WriteLog(aLog)
                            try:
                                # Reenviamos al UAServer el invite
                                my_socket.send(line) 
                                # Reenviamos al UAClient que realiza el invite
                                data = my_socket.recv(1024)
                                mens = data.split("\r\n")
                                aLog = "Received from "
                                aLog += UAServerIP + ":" + UAServerPort
                                aLog += ": " + mens[0] + " "
                                aLog += mens[1] + " " + mens[2]
                                WriteLog(aLog)
                                self.wfile.write(data)
                                aLog = "Send to " + self.client_address[0]
                                aLog += ":" + str(self.client_address[1])
                                aLog += ": " + mens[0] + " " + mens[1]
                                aLog += " " + mens[2]
                                WriteLog(aLog)
                            except socket.error:
                                Error = 'Error: no user agent server listening'
                                print Error
                                self.wfile.write(Error)
                            my_socket.close()
                    if method == 'Ack':
                        address_invited = line.split()[1].split(":")[1]
                        UAServerIP = self.addresses[address_invited][0]
                        UAServerPort = self.addresses[address_invited][1]
                        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        my_socket.connect((UAServerIP, int(UAServerPort)))
                        try:
                            my_socket.send(line)
                            mens = line.split("\r\n")
                            aLog = "Sent to " + UAServerIP + ":" 
                            aLog += UAServerPort + ": " + mens[0]
                            WriteLog(aLog)
                        except socket.error:
                            Error = 'Error: no user agent server listening'
                            print Error
                        my_socket.close()

                    if method == 'Bye':
                        address_invited = line.split()[1].split(":")[1]
                        if not address_invited in self.addresses:
                            aEnviar = "SIP/2.0 404 User Not Found"
                            self.wfile.write(aEnviar + "\r\n\r\n")
                            aLog = "Sent to " + self.client_address[0]
                            aLog += ":" + str(self.client_address[1])
                            aLog += ": " + aEnviar
                            WriteLog(aLog)
                        elif address_invited in self.addresses:
                            UAServerIP = self.addresses[address_invited][0]
                            UAServerPort = self.addresses[address_invited][1]
                            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            my_socket.connect((UAServerIP, int(UAServerPort)))
                            try:
                                my_socket.send(line)
                                mens = line.split("\r\n")
                                aLog = "Sent to " + UAServerIP + ":"
                                aLog += UAServerPort + ": " + mens[0]
                                WriteLog(aLog)
                                data = my_socket.recv(1024)
                                mens2 = data.split("\r\n")
                                aLog = "Received from " + UAServerIP + ":"
                                aLog += UAServerPort + ": " + mens2[0]
                                WriteLog(aLog)
                                self.wfile.write(data)
                                aLog = "Sent to " + self.client_address[0]
                                aLog += ":" + str(self.client_address[1])
                                aLog += ": " + mens2[0]
                                WriteLog(aLog)
                                
                            except socket.error:
                                Error = 'Error: no user agent server listening'
                                print Error
                            my_socket.close()
                      
                elif not method in method_list:
                   self.wfile.write('SIP/2.0 405 Method Not Allowed\r\n\r\n')
            else:
                self.wfile.write('SIP/2.0 400 Bad Request\r\n\r\n')

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

    # Fichero log
    log = open(list_tags[2]['path'], 'a')

    # Creamos servidor de sip y escuchamos
    serv = SocketServer.UDPServer(("", int(list_tags[0]['puerto'])), 
    SIPRegisterHandler)
    print 'Server ', list_tags[0]['name'], ' listening at port ', 
    print list_tags[0]['puerto'] 
    WriteLog('Starting...')
    serv.serve_forever()
    WriteLog('Finishing')
