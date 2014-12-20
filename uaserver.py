#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para la parte servidora de un UA en UDP
"""

import SocketServer
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from proxy_registrar import Log


class XMLHandler(ContentHandler):  # importarlo al client
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
                    self.Atributos[Clave] = attrs.get(Atributo, "")
                    if self.Atributos[Clave] == "":
                        self.Atributos[Clave] = '127.0.0.1'
                else:
                    self.Atributos[Clave] = attrs.get(Atributo, "")
                #Esta funcion guarda el valor de Atributo, si existe en esa
                #etiqueta, y si no, guarda un string vacío ("").
                #Así que hacemos un if para que cuando el
                #atributo sea el ip del server y esté vacío, ponga 127.0.0.1
           

    def get_tags(self):
        return self.Atributos


def Reproducir(IpClient, mp3port): # IMPORTARLO LUEGO AL CLIENT
    """
    Reproduce un fichero mp3
    """
    # iniciar RTP
    # aEjecutar es un string con lo que se ha de ejecutar en la shell
    aEjecutar = './mp32rtp -i ' + IpClient + ' -p ' + str(mp3port)
    + ' < ' + SONG
    print "Vamos a ejecutar", aEjecutar
    os.system(aEjecutar)
    print "Enviando: Transmisión de datos terminada"


class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):
        """
        Servidor de recepción que contesta a peticiones INVITE del cliente
        descargando un archivo mp3, y a peticiones BYE
        """
        print "El cliente " + str(self.client_address) + " nos manda:"
        # Escribe dirección y puerto del cliente (de tupla client_address)
        while 1:
            # Leyendo mensaje a mensaje lo que nos envía el cliente
            line = self.rfile.read()
            if not line:
                break
            else:
                print line
                WordList = line.split(' ')
                Method = WordList[0]
                IpClient = str(self.client_address[0])
                if not Method in MethodList:  # TRATAR Y ESCRIBIR LOG
                    print "Enviando: SIP/2.0 405 Method Not Allowed"
                    self.wfile.write('SIP/2.0 405 Method Not Allowed\r\n\r\n')
                    break  # Se detiene. Error específico.
                if Method == "INVITE":
                    print "Enviando: SIP/2.0 100 Trying"
                    self.wfile.write('SIP/2.0 100 Trying\r\n\r\n')
                    print "Enviando: SIP/2.0 180 Ringing"
                    self.wfile.write('SIP/2.0 180 Ringing\r\n\r\n')
                    print "Enviando: SIP/2.0 200 OK"
                    self.wfile.write('SIP/2.0 200 OK\r\n\r\n')
                elif Method == "ACK":
                    mp3port = '23032' #OJO TAMBIEN PUEDE SER 23033
                    Reproducir(IpClient, mp3port)
                elif Method == "BYE":
                    print "Enviando: SIP/2.0 200 OK"
                    self.wfile.write('SIP/2.0 200 OK\r\n\r\n')
                else:
                    print "Enviando: SIP/2.0 400 Bad Request"
                    self.wfile.write('SIP/2.0 400 Bad Request\r\n\r\n')
                    # Error general


if __name__ == "__main__":
    try:
        FichConfig = sys.argv[1]    #FICHERO XML
        # Comprobar que existe el archivo mp3
        if not os.access(FichConfig, os.F_OK):
            sys.exit('Usage: python uaserver.py config')
    except IndexError:
        sys.exit('Usage: python uaserver.py config')
    except ValueError:
        sys.exit('Usage: python uaserver.py config')

    MethodList = ["INVITE", "ACK", "BYE"]

    parser = make_parser()
    Handler = XMLHandler()
    parser.setContentHandler(Handler)
    parser.parse(open(FichConfig))
    Dicc = Handler.get_tags() # Diccionario con los atributos del fichero xml
    IP = Dicc['uaserver_ip']
    PORT = Dicc['uaserver_puerto']
    LOG = Dicc['log_path']
    SONG = Dicc['audio_path']

    Log(LOG, 'Start', '', '', '')

    try:
        # Creamos servidor de eco y escuchamos
        serv = SocketServer.UDPServer(("", int(PORT)), EchoHandler)
        print "Listening..."
        serv.serve_forever()
    except KeyboardInterrupt:
        print "\r\nFinishing."
        Log(LOG, 'Finish', '', '', '')
