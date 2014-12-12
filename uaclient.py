#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XMLHandler(ContentHandler):
    """
    Handler para leer XML de configuración de User Agents
    """

    def __init__(self):
        #Diccionario de Listas con todo lo que puedo tener (sólamente para
        #buscar los nombres, no para guardar valores)
        self.UADicc = {
            'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']
        }
        self.Atributos = {}
        #Diccionario donde guardamos los valores de los atributos

    def startElement(self, name, attrs):
        if name in self.UADicc:
            for Atributo in self.UADicc[name]:  # busco en la etiqueta=name
                Clave = name + '_' + Atributo
                #nombre de las entradas del diccionario
                if Clave == 'uaserver_ip':
                    self.Atributos[Clave] = attrs.get(Atributo, "127.0.0.1")
                    print 'AAAA', self.Atributos[Clave]
                    #NO FUNCIONA!!!!!! NO PONE 127....
                else:
                    self.Atributos[Clave] = attrs.get(Atributo, "")
                #Esta funcion guarda el valor de Atributo, si existe en esa
                #etiqueta, y si no, guarda un string vacío ("").
                #Así que hacemos un if para que cuando el
                #atributo sea el ip del server y esté vacío, ponga 127.0.0.1
           

    def get_tags(self):
        return self.Atributos


# Cliente UDP simple.

try:
    FichConfig = sys.argv[1]    #FICHERO XML
    if not os.access(FichConfig, os.F_OK):  # Devuelve True si está el fichero
        sys.exit('Usage: python uaclient.py config method option')
    Method = sys.argv[2].upper()
    option = sys.argv[3]
except IndexError:
    sys.exit('Usage: python uaclient.py config method option')
except ValueError:
    sys.exit('Usage: python uaclient.py config method option')

parser = make_parser()
Handler = XMLHandler()
parser.setContentHandler(Handler)
parser.parse(open(FichConfig))
Dicc = Handler.get_tags() # Diccionario con los atributos del fichero xml
print Dicc
NAME = Dicc['account_username']
print NAME
SERVER = Dicc['uaserver_ip']
print SERVER
PORT = Dicc['uaserver_puerto']
print PORT
# Contenido que vamos a enviar
Line = Method + ' sip:' + NAME + '@' + SERVER + ' SIP/2.0\r\n'

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((SERVER, int(PORT)))

try:
    print "Enviando: " + Line
    my_socket.send(Line + '\r\n')
    data = my_socket.recv(1024)
except:
    sys.exit('Error: No server listening at ' + SERVER + ' port ' + PORT)
    #PONERLO EN EL LOG
print 'Recibido -- \r\n', data
ListaTexto = data.split('\r\n')
if Method == "INVITE":
    if ListaTexto[2] == 'SIP/2.0 200 OK':
        Method = "ACK"
        Line = Method + ' sip:' + NAME + '@' + SERVER + ' SIP/2.0\r\n'
        print "Enviando: " + Line
        my_socket.send(Line + '\r\n')
# Si estamos en BYE directamente nos salimos tras imprimir data

print "Terminando socket..."

# Cerramos todo
my_socket.close()
print "Fin."
