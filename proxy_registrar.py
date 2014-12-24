#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor proxy/registrar
"""

import socket
import SocketServer
import sys
import time
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


def TimeGuay():
    """
    Devuelve la hora actual en formato Año-Mes-Día-Horas-Minutos-Segundos
    """

    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))


def Log(fich, mode, text, Ip, Port):
    """
    Escribe en un fichero en modo APPEND
    """

    txt = open(fich, 'a')
    if mode == 'Start':
        txt.write(TimeGuay() + " Starting...\r\n")
    elif mode == 'Finish':
        txt.write(TimeGuay() + " Finishing.\r\n")
    elif mode == 'Send':
        txt.write(TimeGuay() + ' Sent to ' + Ip + ':' + str(Port) + ': ' +
        text + '\r\n')
    elif mode == 'Receive':
        txt.write(TimeGuay() + ' Received from ' + Ip + ':' + str(Port) +
        ': ' + text + '\r\n')
    elif mode == 'Error':
        txt.write(TimeGuay() + ' ' + text + '\r\n')
    txt.close()


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

        print "\r\nEl cliente " + str(self.client_address) + " nos manda:"
        # Escribe dirección y puerto del cliente (de tupla client_address)
        while 1:
            # Leyendo mensaje a mensaje lo que nos envía el cliente
            line = self.rfile.read()
            if not line:
                break
            else:
                print line
                Ip = self.client_address[0]
                Port = self.client_address[1]

                LineList = line.split('\r\n')
                LogLine = " ".join(LineList)
                Log(LOG, 'Receive', LogLine, Ip, Port)

                WordList = line.split(' ')
                Method = WordList[0]
                if not Method in MethodList:
                    LogLine = "SIP/2.0 405 Method Not Allowed\r\n"
                    Log(LOG, 'Error', LogLine, '', '')
                    print "Enviando:\r\n" + LogLine
                    self.wfile.write(LogLine + '\r\n')
                    break  # Se detiene. Error específico.

                if Method == "REGISTER":
                    WordList2 = WordList[1].split(':')
                    User = WordList2[1]
                    PortServ = WordList2[2]
                    Expires = int(LineList[1].split(' ')[1])
                    #Tiempo en el que expirará
                    Time = time.time()  # hora actual (en segundos)
                    TimeReg = Time  # hora a la que se ha registrado (ahora)
                    Data = [Ip, PortServ, TimeReg, Expires]
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
                    Log(LOG, 'Send', OK, Ip, Port)
                    self.wfile.write(OK + "\r\n\r\n")

                elif Method == "INVITE":
                    WordList2 = WordList[1].split(':')
                    Name2 = WordList2[1]  # Al que va dirigido el INVITE
                    if Name2 in DiccUsers:
                    #devuelve True si existe la clave en el dicc, False si no
                        Ip2 = DiccUsers[Name2][0]  # Buscamos su Ip y
                        Port2 = DiccUsers[Name2][1]  # PuertoServ.
                        Found = True
                    else:
                        LogLine = 'SIP/2.0 404 User Not Found\r\n'
                        Log(LOG, 'Error', LogLine, '', '')
                        print "Enviando:\r\n" + LogLine
                        self.wfile.write(LogLine + '\r\n')
                        Found = False

                    if Found:
                        print "Reenviando mensaje a su destinatario\r\n"
                        Log(LOG, 'Send', LogLine, Ip2, Port2)

                        Data = self.Reenviar(Ip2, Port2, line)  # Contestación

                        print "Respuesta:\r\n" + Data
                        LineList = Data.split('\r\n')
                        LogLine = " ".join(LineList)
                        Log(LOG, 'Receive', LogLine, Ip2, Port2)

                        print "Reenviando respuesta al emisor del INVITE\r\n"
                        Log(LOG, 'Send', LogLine, Ip, Port)

                        self.wfile.write(Data)  # Devolvemos la contestación

                elif Method == 'ACK':
                    WordList2 = WordList[1].split(':')
                    Name2 = WordList2[1]  # Al que va dirigido el ACK
                    Ip2 = DiccUsers[Name2][0]  # Buscamos su Ip y
                    Port2 = DiccUsers[Name2][1]  # PuertoServ.

                    print "Reenviando mensaje a su destinatario\r\n"
                    Log(LOG, 'Send', LogLine, Ip2, Port2)

                    #no usamos Reenviar porque no vamos a esperar respuesta
                    my_socket = socket.socket(socket.AF_INET,
                    socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET,
                    socket.SO_REUSEADDR, 1)
                    my_socket.connect((Ip2, int(Port2)))
                    my_socket.send(line)

                elif Method == 'BYE':
                    WordList2 = WordList[1].split(':')
                    Name2 = WordList2[1]  # Al que va dirigido el ACK
                    if Name2 in DiccUsers:
                    #Puede que ya no esté, así que lo comprobamos
                        Ip2 = DiccUsers[Name2][0]
                        Port2 = DiccUsers[Name2][1]
                        Found = True
                    else:
                        LogLine = 'SIP/2.0 404 User Not Found\r\n'
                        Log(LOG, 'Error', LogLine, '', '')
                        print "Enviando:\r\n" + LogLine
                        self.wfile.write(LogLine + '\r\n')
                        Found = False

                    if Found:
                        print "Reenviando mensaje a su destinatario\r\n"
                        Log(LOG, 'Send', LogLine, Ip2, Port2)

                        Data = self.Reenviar(Ip2, Port2, line)  # Contestación

                        print "Respuesta:\r\n" + Data
                        LineList = Data.split('\r\n')
                        LogLine = " ".join(LineList)
                        Log(LOG, 'Receive', LogLine, Ip2, Port2)

                        print "Reenviando respuesta al emisor del BYE\r\n"
                        Log(LOG, 'Send', LogLine, Ip, Port)

                        self.wfile.write(Data)  # Devolvemos la contestación

                else:
                    LogLine = "SIP/2.0 400 Bad Request\r\n"
                    Log(LOG, 'Error', LogLine, '', '')
                    print "Enviando:\r\n" + LogLine
                    self.wfile.write(LogLine + '\r\n')
                    # Error general

    def register2file(self):
        """
        Editor de archivos txt de registro de usuarios
        """

        txt = open(DATABASE, 'w')
        txt.write('(\t User\t\t--\t\tIP\t--\tPort -- Register Time\t' +
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

    def Reenviar(self, Ip, Port, Data):
        """
        Función que reenvía datos a otro User Agent y recibe su respuesta 
        """

        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((Ip, int(Port)))

        my_socket.send(Data)
        return my_socket.recv(1024)  # Lo que nos contesta



"""
Programa Principal
"""

if __name__ == "__main__":
    DiccUsers = {}  # Creo el diccionario de usuarios e IPs
    MethodList = ["REGISTER", "INVITE", "ACK", "BYE"]

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

    Log(LOG, 'Start', '', '', '')


    try:
        # Creamos servidor de eco y escuchamos
        serv = SocketServer.UDPServer(("", int(PORT)), SIPRegisterHandler)
        print "Server", NAME, "listening at port", PORT, "..."
        serv.serve_forever()
    except KeyboardInterrupt:
        print "\r\nFinishing."
        Log(LOG, 'Finish', '', '', '')
        
