#!/usr/bin/python
# -*- coding: utf-8 -*-
import zlib
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

#Tipos de Mensagens
#0 - Heartbeat
#1 - Urgente; Para convocacao de uma nova eleicao

class Message(object):
    def __init__ (self):
        self.tipo = 0
        self.id_origem = 0
        self.id_destino = 0

    def __init__ (self, tipo, origem, destino):
        self.setTipo(tipo)
        self.setOrigem(origem)
        self.setDestino(destino)

    #Tipo
    def getTipo(self):
        return int(self.tipo)

    def setTipo(self, tipo):
        self.tipo = tipo #converte pra char

    #Peer de Origem
    def getOrigem(self):
        return int(self.id_origem) #converte pra int

    def setOrigem(self, origem):
        self.id_origem = origem #converte pra char

    #Peer de Destino
    def getDestino(self):
        return int(self.id_origem) #converte pra int

    def setDestino(self, destino):
        self.id_destino = destino #converte pra char

    #Empacotamento de mensagem para envio pelo socket
    def empacotar(self):
        return str(self.getTipo()) + str(self.getOrigem()) + str(self.getDestino())

    #Desempacotamento da mensagem recebida pelo socket
    def desempacotar(self, msg):
        self.setTipo(msg[0])
        self.setOrigem(msg[1])
        self.setDestino(msg[2])
        return self
