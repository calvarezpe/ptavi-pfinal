#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa de la parte cliente de un UA que abre un socket a un servidor
"""

import socket
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from proxy_registrar import Log
from uaserver import XMLHandler


"""
Programa Principal
"""

if __name__ == "__main__":
    try:
        FichConfig = sys.argv[1]    #Fichero XML
        if not os.access(FichConfig, os.F_OK):  # Devuelve True si está el fich
            sys.exit('Usage: python uaclient.py config method option')
        METHOD = sys.argv[2].upper()
        OPTION = sys.argv[3] # OJO AL METER MAL ESTO DETECTARLO LUEGO
    except IndexError:
        sys.exit('Usage: python uaclient.py config method option')
    except ValueError:
        sys.exit('Usage: python uaclient.py config method option')

    parser = make_parser()
    Handler = XMLHandler()
    parser.setContentHandler(Handler)
    parser.parse(open(FichConfig))
    Dicc = Handler.get_tags() # Diccionario con los atributos del fichero xml
    NAME = Dicc['account_username']
    UA_IP = Dicc['uaserver_ip']
    UA_PORT = Dicc['uaserver_puerto']
    RTP_PORT = Dicc['rtpaudio_puerto']
    PR_IP = Dicc['regproxy_ip']
    PR_PORT = Dicc['regproxy_puerto']
    LOG = Dicc['log_path']
    SONG = Dicc['audio_path']


    # Contenido que vamos a enviar

    if METHOD == 'REGISTER':
        Line = METHOD + ' sip:' + NAME + ':' + UA_PORT + ' SIP/2.0\r\n'
        Body = 'Expires: ' + OPTION + '\r\n'
    elif METHOD == 'INVITE':
        Line = METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n'
        Description = 'V=0\r\no=' + NAME + ' ' + UA_IP 
        + '\r\ns=Ciudad del Miedo\r\nt=0\r\nm=audio ' + RTP_PORT + ' RTP'
        Body = 'Content-Type: application/sdp' + '\r\n\r\n' + Description

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((PR_IP, int(PR_PORT)))

    print "Enviando: \r\n" + Line + Body
    LogLine = Line + Body
    LineList = LogLine.split('\r\n')  # Eliminamos los saltos de línea
    LogLine = " ".join(LineList)  # Ojo al uso de join. Pongo espacios.
    Log(LOG, 'Send', LogLine, PR_IP, PR_PORT)

    try:
        my_socket.send(Line + Body + '\r\n')
        data = my_socket.recv(1024)

    except socket.error:
        LogLine = 'Error: No server listening at ' + PR_IP + ' port ' + PR_PORT
        Log(LOG, 'Error', LogLine, '', '')
        sys.exit(LogLine)
    
    print 'Recibido: \r\n', data
    ListaTexto = data.split('\r\n')
    LogLine = " ".join(ListaTexto)
    Log(LOG, 'Receive',  LogLine, PR_IP, PR_PORT)

    if METHOD == "INVITE":
        if ListaTexto[2] == 'SIP/2.0 200 OK': # COMPROBAR
            Method = "ACK"
            Line = Method + ' sip:' + NAME + '@' + UA_IP + ' SIP/2.0\r\n'
            print "Enviando: \r\n" + Line
            ListaTexto = Line.split('\r\n')
            LogLine = " ".join(ListaTexto)
            Log(LOG, 'Send',  LogLine, PR_IP, PR_PORT)
            my_socket.send(Line + '\r\n')
    # Si estamos en BYE directamente nos salimos tras imprimir data

    print "Terminando socket..."

    # Cerramos todo
    my_socket.close()
    print "Fin."
