#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco
en UDP simple
"""

import SocketServer
import sys
import time


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
                WordList = line.split(' ')
                if WordList[0] == "REGISTER":
                    User = WordList[1].split(':')[1]
                    IP = self.client_address[0]
                    Expires = int(WordList[3])  # Tiempo en el que expirará
                    Time = time.time()  # hora actual (en segundos)
                    TimeExp = Time + Expires  # Hora a la que expirará
                    Data = [IP, TimeExp]
                    DiccUsers[User] = Data
                    #Añadimos la lista con los datos al diccionario de usuarios
                    for User in DiccUsers.keys():
                        TimeExp = DiccUsers[User][1]
                        if Time >= TimeExp:
                            del DiccUsers[User]
                            #Lo eliminamos del diccionario
                    self.register2file()
                    print "Enviando: SIP/2.0 200 OK"
                    self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
                else:
                    print "Método desconocido"

    def register2file(self):
        """
        Editor de archivos txt de registro de usuarios
        """

        txt = open('registered.txt', 'w')
        txt.write('User\tIP\tExpires\n')
        for User in DiccUsers.keys():
            IP = DiccUsers[User][0]
            TimeExp = DiccUsers[User][1]
            TimeExp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(TimeExp))
            #Lo pasamos a formato guay
            txt.write(User + '\t' + IP + '\t' + TimeExp + '\n')
        txt.close()


"""
Programa Principal
"""

if __name__ == "__main__":
    DiccUsers = {}  # Creo el diccionario de usuarios e IPs
    listarg = sys.argv
    # Creamos servidor de eco y escuchamos
    serv = SocketServer.UDPServer(("", int(listarg[1])), SIPRegisterHandler)
    print "Lanzando servidor UDP de eco..."
    serv.serve_forever()
