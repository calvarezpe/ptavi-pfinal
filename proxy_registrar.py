#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor proxy/registrar
"""

import SocketServer
import sys
import time
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XMLHandler(ContentHandler):
    """
    Handler para leer XML de configuración de Proxy
    """

    def __init__(self):
        #Diccionario de Listas con todo lo que puedo tener (sólamente para
        #buscar los nombres, no para guardar valores)
        self.UADicc = {
            'server': ['name', 'ip', 'puerto'],
            'database': ['path', 'passwdpath'],
            'log': ['path']
        }
        self.Atributos = {}
        #Diccionario donde guardamos los valores de los atributos

    def startElement(self, name, attrs):
        if name in self.UADicc:
            for Atributo in self.UADicc[name]:  # busco en la etiqueta=name
                Clave = name + '_' + Atributo
                #nombre de las entradas del diccionario
                if Clave == 'server_ip':
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



class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):
        """
        Manejador de los mensajes recibidos
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
                #log = open(LOG, 'a')  # Abrimos en modo append
                WordList = line.split(' ')
                if WordList[0] == "REGISTER":
                    User = WordList[1].split(':')[1]
                    Ip = self.client_address[0]
                    Port = self.client_address[1]

                    LineList = line.split('\r\n')
                    LogLine = " ".join(LineList)
                    log.write(self.Time() + ' Received from ' + Ip + ':' + 
                    str(Port) + ': ' + LogLine + '\r\n')

                    WordList2 = line.split('\r\n')
                    Expires = int(WordList2[1].split(' ')[1])
                    #Tiempo en el que expirará
                    Time = time.time()  # hora actual (en segundos)
                    TimeReg = Time  # hora a la que se ha registrado (ahora)
                    Data = [Ip, Port, TimeReg, Expires]
                    DiccUsers[User] = Data
                    #Añadimos la lista con los datos al diccionario de usuarios
                    for User in DiccUsers.keys():
                        TimeReg = DiccUsers[User][2]
                        Expires = DiccUsers[User][3]
                        TimeExp = TimeReg + Expires  # Hora a la que expirará
                        if Time >= TimeExp:
                            del DiccUsers[User]
                            #Lo eliminamos del diccionario
                    self.register2file()

                    OK = "SIP/2.0 200 OK"
                    print "Enviando:\r\n" + OK

                    LogLine = self.Time() + ' Sent to ' + Ip + ':' + str(Port)
                    LogLine += ': ' + OK + '\r\n'
                    log.write(LogLine)
                    #log.close()

                    self.wfile.write(OK + "\r\n\r\n")
                else:
                    print "Método desconocido"

    def register2file(self):
        """
        Editor de archivos txt de registro de usuarios
        """

        txt = open(DATABASE, 'w')
        txt.write('( User\t\t--\t\tIP\t--\tPort -- Register Time\t' +
        ' -- Expires )\n')
        for User in DiccUsers.keys():
            Ip = DiccUsers[User][0]
            Port = DiccUsers[User][1]
            TimeReg = DiccUsers[User][2]
            Expires = DiccUsers[User][3]
            TimeReg = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(TimeReg))
            #Lo pasamos a formato guay
            txt.write(User + '\t' + Ip + '\t' + str(Port) + '\t' + 
            TimeReg + '\t' + str(Expires) + '\n')
        txt.close()

    def Time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))


"""
Programa Principal
"""

if __name__ == "__main__":
    DiccUsers = {}  # Creo el diccionario de usuarios e IPs

    try:
        FichConfig = sys.argv[1]    #FICHERO XML
        # Comprobar que existe el archivo mp3
        if not os.access(FichConfig, os.F_OK):
            sys.exit('Usage: python proxy_registrar.py config')
    except IndexError:
        sys.exit('Usage: python proxy_registrar.py config')
    except ValueError:
        sys.exit('Usage: python proxy_registrar.py config')

    parser = make_parser()
    Handler = XMLHandler()
    parser.setContentHandler(Handler)
    parser.parse(open(FichConfig))
    Dicc = Handler.get_tags() # Diccionario con los atributos del fichero xml
    NAME = Dicc['server_name']
    IP = Dicc['server_ip']
    PORT = Dicc['server_puerto']
    DATABASE = Dicc['database_path']
    LOG = Dicc['log_path']

    log = open(LOG, 'w')
    log.write(SIPRegisterHandler.Time() + "Starting...")

    try:
        # Creamos servidor de eco y escuchamos
        serv = SocketServer.UDPServer(("", int(PORT)), SIPRegisterHandler)
        print "Server", NAME, "listening at port", PORT, "..."
        serv.serve_forever()
    except KeyboardInterrupt:
        print "\r\nFinishing."
        log.write(SIPRegisterHandler.Time() + "Finishing.")
        log.close()
        
