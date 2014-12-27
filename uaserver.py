#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para la parte servidora de un UA
"""

import SocketServer
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from proxy_registrar import Log


class XMLHandler(ContentHandler):  # Importado al Client
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


def Reproducir(IpClient, mp3port, Song): # Importado al Client
    """
    Reproduce un fichero mp3
    """
    # iniciar RTP
    # aEjecutar es un string con lo que se ha de ejecutar en la shell
    aEjecutar = './mp32rtp -i ' + IpClient + ' -p ' + str(mp3port)
    aEjecutar += ' < ' + Song
    print "Vamos a ejecutar", aEjecutar
    os.system(aEjecutar)
    print "Transmisión de datos terminada"


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
                IpProxy = self.client_address[0]
                PortProxy = self.client_address[1]

                LineList = line.split('\r\n')
                LogLine = " ".join(LineList)
                Log(LOG, 'Receive', LogLine, IpProxy, PortProxy)

                if not Method in MethodList:
                    LogLine = "SIP/2.0 405 Method Not Allowed\r\n"
                    Log(LOG, 'Error', LogLine, '', '')
                    print "Enviando:\r\n" + LogLine
                    self.wfile.write('SIP/2.0 405 Method Not Allowed\r\n\r\n')
                    break  # Se detiene. Error específico.

                if Method == "INVITE":
                    DiccData['PortRTP'] = WordList[-2]  # Penúltimo dato
                    DiccData['IpClient'] = WordList[4].split('\r\n')[0]
                    #Datos para transmitir mp3 cuando llegue el ACK
                    
                    LogLine = 'SIP/2.0 100 Trying\r\n'
                    Log(LOG, 'Send', LogLine, IpProxy, PortProxy)
                    print "Enviando:\r\n" + LogLine
                    self.wfile.write(LogLine + '\r\n')

                    LogLine = 'SIP/2.0 180 Ringing\r\n'
                    Log(LOG, 'Send', LogLine, IpProxy, PortProxy)
                    print "Enviando:\r\n" + LogLine
                    self.wfile.write(LogLine + '\r\n')

                    LogLine = 'SIP/2.0 200 OK\r\n'  
                    # Añadimos SDP (con nuestro puerto rtp)
                    Description = LineList[3] + '\r\n'  # v
                    Description += 'o=' + NAME + ' ' + IP + '\r\n'  # o
                    Description += LineList[5] + '\r\n'  # s
                    Description += LineList[6] + '\r\n'  # t
                    Description += 'm=audio ' + str(RTP_PORT) + ' RTP\r\n'
                    Body = LineList[1] + '\r\n\r\n' + Description
                    LogLine += Body
                    Log(LOG, 'Send', LogLine, IpProxy, PortProxy)
                    print "Enviando:\r\n" + LogLine
                    self.wfile.write(LogLine + '\r\n')

                elif Method == "ACK":
                    Reproducir(DiccData['IpClient'], DiccData['PortRTP'], SONG)

                elif Method == "BYE":
                    LogLine = 'SIP/2.0 200 OK\r\n'
                    Log(LOG, 'Send', LogLine, IpProxy, PortProxy)
                    print "Enviando:\r\n" + LogLine
                    self.wfile.write(LogLine + '\r\n')

                else:
                    LogLine = "SIP/2.0 400 Bad Request\r\n"
                    Log(LOG, 'Error', LogLine, '', '')
                    print "Enviando:\r\n" + LogLine
                    self.wfile.write(LogLine + '\r\n')
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
    NAME = Dicc['account_username']
    IP = Dicc['uaserver_ip']
    PORT = Dicc['uaserver_puerto']
    RTP_PORT = Dicc['rtpaudio_puerto']
    LOG = Dicc['log_path']
    SONG = Dicc['audio_path']

    #Diccionario con los datos del cliente que quiere recibir mp3 por RTP
    DiccData = {'PortRTP' : ' ', 'IpClient' : ' '}

    Log(LOG, 'Start', '', '', '')

    try:
        # Creamos servidor de eco y escuchamos
        serv = SocketServer.UDPServer(("", int(PORT)), EchoHandler)
        print "Listening..."
        serv.serve_forever()
    except KeyboardInterrupt:
        print "\r\nFinishing."
        Log(LOG, 'Finish', '', '', '')
