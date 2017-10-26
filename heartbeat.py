#!/usr/bin/python
# -*- coding: utf-8 -*-
# ***************************************************************           
#     * Peer -- Programa para conectar n-peers.                 *   
#     *         Disciplina de Redes II - 2017/01                *
#               Professor Elias                                 *
#               UFPR                                            *   
#     * Autores:  Diego Graciano Roessle - GRR20148190          *   
#     *           Felipe Dotti           - GRR20151127          *       
#     *                                                         *   
#     * Uso:                                                    *   
#     *     Executar, em máquinas diferentes, o Programa        *
#           utilizando o comando "python2.7 peer.py" no terminal* 
#****************************************************************  
import time

class HeartbeatEntry(object):
    def __init__ (self):
        self.id = 0
        self.lider = 0
        self.last_heartbeat = time.time()

    def __init__ (self, id):
        self.setId(id)
        self.lider = 0
        self.last_heartbeat = time.time()

   	 #Id
    def getId(self):
        return self.id

    def setId(self, id):
        self.id = int(id) #converte char pra int

    #lider
    def getLider(self):
        return self.lider

    def setLider(self, valor):
        self.lider = int(valor) #converte char pra int

    #Ultimo heartbeat
    def getLastHeartbeat(self):
        return self.last_heartbeat

    def setLastHeartbeat(self, time):
        self.last_heartbeat = int(time)
