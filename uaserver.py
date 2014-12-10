#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

#git commit -m "update" pr.xml proxy_registrar.py ua1.xml ua2.xml uaclient.py uaserver.py

import SocketServer
import sys
import os


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
                IP_CLIENT = str(self.client_address[0])
                if not Method in MethodList:
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
                    # iniciar RTP
                    # aEjecutar es un string con lo que se ha de ejecutar
                    # en la shell
                    aEjecutar = './mp32rtp -i ' + IP_CLIENT + ' -p 23032 < ' + SONG
                    print "Vamos a ejecutar", aEjecutar
                    os.system(aEjecutar)
                    print "Enviando: Transmisión de datos terminada"
                elif Method == "BYE":
                    print "Enviando: SIP/2.0 200 OK"
                    self.wfile.write('SIP/2.0 200 OK\r\n\r\n')
                else:
                    print "Enviando: SIP/2.0 400 Bad Request"
                    self.wfile.write('SIP/2.0 400 Bad Request\r\n\r\n')
                    # Error general


if __name__ == "__main__":
    try:
        IP = sys.argv[1]
        PORT = sys.argv[2]
        SONG = sys.argv[3]
        # Comprobar que existe el archivo mp3
        if not os.access(SONG, os.F_OK):  # Devuelve True si está en la carpeta
            sys.exit('Usage: python server.py IP port audio_file')
    except IndexError:
        sys.exit('Usage: python server.py IP port audio_file')
    except ValueError:
        sys.exit('Usage: python server.py IP port audio_file')

    MethodList = ["INVITE", "ACK", "BYE"]
    # Creamos servidor de eco y escuchamos
    serv = SocketServer.UDPServer(("", int(PORT)), EchoHandler)
    print "Listening..."
    serv.serve_forever()
