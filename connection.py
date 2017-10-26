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
import socket
import host
import netifaces as ni

#Busca identificar o id do host atual (que executa o programa) dentro do hosts.txt
#Parâmetros : a lista de hosts e o endereço IP do peer atual
#Retorna o id do host identificado
def identificaPeer(hosts, meuIp):
    for h in hosts:
        if h.getIp() == meuIp:
            return h.getId()
    return -1 #Isso não pode acontecer

#Como todos os hosts usam a mesma porta, retorna a porta do primeiro host da lista
#Parâmetros : a lista de hosts
def identificaPorta(hosts):
    try:
        return hosts[0].getPorta()
    except:
        return -1 #Isso não pode acontecer

#Descobre o ip desta máquina através do nome da interface de rede
def meuEnderecoIp():
	ni.ifaddresses('eth0')
	ip = ni.ifaddresses('eth0')[2][0]['addr']
	return ip
