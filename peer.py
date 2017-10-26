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

import csv
import sys
import host
import connection
import socket
import message
import time
import heartbeat
import datetime
import threading
import logging
import select

#Tipos de Mensagens
HEARTBEAT = 0
URGENTE = 1

#Intervalo do Heartbeat
HB_PERIOD = 3

#Lista de Sockets de peers que solicitaram conexoes com este peer
sockList = {}

#Cria um array contendo todos os hosts dos arquivos txt e seus respectivos IPs
def lerHosts():
    f = open("hosts.txt", 'rb')
    reader = csv.reader(f)
    hosts = []
    for row in reader:
        h = host.Host(row) #Novo objeto da classe host
        hosts.append(h)
    f.close()
    return hosts

#Lista de peers da rede
hosts = lerHosts()

#Funcao que cria a tabela de heartbeats
def criaTabelaHbs():
    hbDic = {}
    for h in hosts:
        hbDic[h.getId()] = heartbeat.HeartbeatEntry(h.getId())
    if len(hbDic) > 0: #O lider inicial eh o primeiro da lista de hosts
        lider = hbDic[0]
        lider.setLider(1)
    return hbDic

#Tabela de Heartbeats
hbTable = criaTabelaHbs()

#Variavel que determina exit das threads
tExit = 0

def main():
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', filename='log.txt', level=logging.DEBUG)

    mensagemInicial()

    #Identifica peers na rede
    ip = connection.meuEnderecoIp()
    logging.info("Lendo a lista de hosts")
    logging.info("A lista de hosts possui " + str(len(hosts)) + " hosts")
    idPeer = connection.identificaPeer(hosts, ip)
    porta = connection.identificaPorta(hosts)
    if idPeer < 0:
        logging.error("O peer atual nao está na lista de hosts no arquivo hosts.txt")
        logging.error("Insira as informacoes deste host no arquivo e execute o programa novamente.\n")
        print("O peer atual nao está na lista de hosts no arquivo hosts.txt")
        print("Insira as informacoes deste host no arquivo e execute o programa novamente.\n")
        sys.exit()
    logging.info('Inicio da execucao no peer ' + str(idPeer) + ', que possui IP ' + str(ip))
    print("{}{}".format("Sou o PEER ",idPeer))
    print("----------")

    #Faz a conexao inicial deste peer com todos os demais
    logging.info("Abrindo socket de escuta para o peer " + str(idPeer))
    s = criaSocketServidor(porta, ip)
    logging.info("Socket de escuta para o peer " + str(idPeer) + " foi aberto")
    logging.info("Para o peer " + str(idPeer) + " foi criada uma thread de escuta e uma thread para solicitar a conexao com outros peers")
     #Cria uma thread para escutar, uma outra para se conectar aos outros hosts
     #e uma última para fazer a verificacao dos heartbeats
    criaThreads(idPeer, s)

    print("=====================")
    print("Programa Finalizado")
    logging.info("Programa Finalizado")

    return 1

#Funcao que abre um socket para escutar
#Parametros : a porta e o endereco ip para abrir o socket
def criaSocketServidor(porta, ip): #Socket para escutar requisicoes de conexao
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind((ip, porta))
	s.listen(5)
	return s

#Funcao que abre as threads para escutar, emparelhar os hosts e verificar os heartbeats
#Parametros : o id do peer atual e o socket de escuta para este peer
def criaThreads(idPeer, s):
    t1 = threading.Thread(target=escuta, args=[s, idPeer])
    t2 = threading.Thread(target=emparelhaHosts, args=[idPeer])
    t3 = threading.Thread(target=verificacaoHb, args=[idPeer])

    #Fazendo as threads terminarem quando a thread principal terminar
    t1.daemon = True
    t2.daemon = True
    t3.daemon = True

    t1.start()
    t2.start()

    #Loop para esperar emparelhamento de hosts terminar
    while True:
        time.sleep(1)
        if not t2.isAlive():
            break
    logging.info("Peer " + str(idPeer) + " iniciou o envio de heartbeats")
    t3.start()

    #Loop para controle de heartbeats terminar
    while True:
        time.sleep(1)
        if not t3.isAlive():
            break
    tExit = 1
    return 1

#Funcao que permanece numa thread para escutar
#Parametros : o id do peer atual e o socket de escuta para este peer
def escuta(s, idPeer):
    global tExit
    try:
        while True and tExit == 0:
        #Aqui o peer escuta requsicoes de conexao. Caso haja uma nova, cria um socket e thread para
        #se comunicar com a máquina que solicitou
                auxsock, auxaddr = s.accept()
                idOrigem = connection.identificaPeer(hosts, auxaddr[0]) #ID do peer que enviou a requisicao
                logging.info("Socket de escuta do peer " + str(idPeer) + " recebeu requisicao de conexao do peer " + str(idOrigem))
                t = threading.Thread(target=handlerServidor, args=[auxsock, idPeer, idOrigem])
                t.start()
                logging.info("Socket de escuta do peer " + str(idPeer) + " aceitou a conexao com o peer " + str(idOrigem))

    except Exception as e:
        logging.error("Peer " + str(idPeer) + " falhou ao aceitar conexao")

    except KeyboardInterrupt:
        logging.warning("Peer " + str(idPeer) + " nao está mais escutando")
        s.close()
        sys.exit()

    return 1

#Funcao que trata o recebimento de mensagens
#Parametros : o socket de escuta para este peer,
#             o id do peer atual e o id do peer de origem da mensagem
def handlerServidor(s, idPeer, idOrigem): #Thread para se comunicar com a máquina que foi requisitada conexao
    global tExit
    try:
        while  True and tExit == 0:
            r, w, e = select.select((s,), (s,), (s,), 0) #Verifica se há dados para ler no socket usando a chamada de sistema select
            if r: #Se houver dados para leitura... (r = read)
                msg = s.recv(80)
                if len(msg) == 0: #Se há dados porehm a mensagem eh vazia, significa que o outro lado encerrou a conexao
                    s.shutdown(socket.SHUT_RDWR) #Fecha todas as instâncias deste socket
                    s.close()
                    logging.warning("Peer " + str(idPeer) + " finalizou conexao com o peer " + str(idOrigem) + ". Fechando os sockets")
                    break # Encerra a thread
                mensagem = message.Message(0,0,0) #Cria um objeto que instancia a classe Mensagem
                mensagem.desempacotar(msg)

                #Se for uma mensagem do tipo HEARTBEAT
                if(mensagem.getTipo() == HEARTBEAT):
                    print("Mensagem de HB recebida do Peer " + str(idOrigem))
                    logging.info("Mensagem de HB recebida do Peer " + str(idOrigem))
                    atualizaHeartbeat(mensagem.getOrigem())

                #Se for uma mensagem do tipo URGENTE
                if(mensagem.getTipo() == URGENTE):
                    print("Mensagem de URGENTE recebida do Peer " + str(idOrigem))
                    logging.info("Mensagem de URGENTE recebida do Peer " + str(idOrigem))
                    print("Vou convocar eleicoes!")
                    logging.info("Peer " + str(idPeer) + " convocou eleicoes")
                    convocaEleicoes()

    except KeyboardInterrupt:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        logging.warning("Peer " + str(idPeer) + " finalizou conexao com o peer " + str(idOrigem) + ". Fechando os sockets")
        sys.exit()

    except socket.error:
        s.close()
        logging.error("Erro no socket entre peer " + str(idPeer) + " e peer " + str(idOrigem) + ". Fechando socket")
        return 1

    except socket.timeout:
        s.close()
        logging.error("Erro no socket entre peer " + str(idPeer) + " e peer " + str(idOrigem) + ". Fechando socket")
        return 1
    return 1

#Funcao que registra a chegada de um heartbeat
#Parametros : o id do peer que enviou o heartbeat
def atualizaHeartbeat(idPeer): #Atualiza a tabela de heartbeats de idPeer utilizando o tempo atual
    print("atualizando HB do peer " + str(idPeer))
    hbEntry = hbTable[idPeer]
    hbEntry.setLastHeartbeat(time.time())
    hbEntry.valido = 1

#Funcao que remove um host da lista de hosts
#Parametros : o id do host a ser removido
def removeHost(id):
    for h in hosts:
        if h.id == id:
        	logging.info("Peer " + str(h.id) + " foi removido da lista de hosts")
        	hosts.remove(h)

#Funcao que determina um novo lider para os peers
def convocaEleicoes():
    logging.info("=========" + "ELEICOES" + "=========")
    print("=========" + "ELEICOES" + "=========")
    if len(hosts) > 0:
        liderId = hosts[0].getId()  #Pega o id do primeiro host da lista atualizada de hosts
        lider = hbTable[liderId]    #Atualiza a lideranca no dicionário (que ainda está desatualizado)
        lider.setLider(1)			#Esse host agora eh o lider
    else:
        return -1
    logging.info("Peer " + str(lider.getId()) + " eh o novo lider!")
    print("Peer " + str(lider.getId()) + " eh o novo lider!\n")
    return lider.getId()

#Funcao que verifica, periodicamente, os heartbeats recebidos
#Parametros : o id do peer atual
def verificacaoHb(idPeer):
    global sockList
    global hosts
    print("\nComeca a verificacao dos Heartbeats")
    print("-----------------------------------")
    print("O lider, inicialmente, eh o PEER 0")
    logging.info("O lider, inicialmente, eh o PEER 0")

    time.sleep(HB_PERIOD)
    removeKeysList = []
    while len(hbTable) > 1:
        hbEntries = hbTable.itervalues()
        #Compara cada peer da tabela de heartbeats de idPeer verificando se o tempo limite já foi ultrapassado
        for hbEntry in hbEntries:
            last = hbEntry.getLastHeartbeat()
            print("Peer " + str(hbEntry.getId()) + " comparando o tempo atual:" + str(time.time()) + " com o do heartbeat: " + str(last))
            logging.info("Peer " + str(hbEntry.getId()) + " comparando o tempo atual:" + str(time.time()) + " com o do heartbeat: " + str(last))
            #Se o tempo do último HB eh superior ao HB_PERIOD definido
            if ((time.time() - last > HB_PERIOD) and (hbEntry.getId() != connection.identificaPeer(hosts, connection.meuEnderecoIp()))):
                if(hbEntry.getLider() == 1):
                    print("\nMandarei uma mensagem URGENTE a todos! PEER " + str(hbEntry.getId()) +" era o LÍDER e desapareceu")
                    logging.warning("Mandar mensagem URGENTE a todos! PEER " + str(hbEntry.getId()) +" era o LÍDER e desapareceu")
                    removeKeysList.append(hbEntry.getId())   #Prepara para deletar da tabela de heartbeats
                    del sockList[hbEntry.getId()]            #Deleta da lista de socket
                    removeHost(hbEntry.getId())              #Deleta da lista de hosts
                    enviaMensagemParaTodos(URGENTE, idPeer)
                    logging.info("Peer " + str(idPeer) + " enviou mensagem do tipo URGENTE para todos os peers")
                    convocaEleicoes()

                else: #Se já ultrapassou HB_PERIOD e o peer nao eh o lider, remove da lista de hosts
                    print("\n=========" + "REMOCAO DE PEER" + "=========")
                    logging.info("=========" + "REMOCAO DE PEER" + "=========")
                    print("PEER "+ str(hbEntry.getId()) + " desapareceu e NAO eh o lider")
                    print("Remove peer " + str(hbEntry.getId()) + " da lista de peers\n")
                    logging.warning("PEER " + str(hbEntry.getId()) + " desapareceu e NAO eh o lider")
                    logging.warning("Removendo peer " + str(hbEntry.getId()) + " da lista de peers, pois nao recebi hearbeat do mesmo")
                    removeKeysList.append(hbEntry.getId())   #Prepara para deletar da tabela de heartbeats
                    del sockList[hbEntry.getId()]            #Deleta da lista de socket
                    removeHost(hbEntry.getId())              #Deleta da lista de hosts

        #Remove peers da tabela de Heartbeats
        for key in removeKeysList:
            del hbTable[key]

        removeKeysList = []
        time.sleep(HB_PERIOD)
    print("Não há mais peers além deste na conexão. O programa vai finalizar.)
    logging.info("Não há mais peers além deste na conexão. O programa vai finalizar.")
    return 1

#Funcao que envia uma mensagem para todos os sockets de clientes que foram abertos
#Parametros : o tipo da mensagem e o id do peer atual
def enviaMensagemParaTodos(tipo, idPeerOrigem):
    socketIds = sockList.keys()     #Chaves do dicionário de sockets
    sockets = sockList.itervalues() #Valores do dicionário de sockets
    i = 0
    for s in sockets:
        mensagem = message.Message(tipo, idPeerOrigem, socketIds.pop(i))
        msg = mensagem.empacotar()
        s.send(msg)
        i += 1

#Funcao que envia trata a solicitacao de uma conexao
#Parametros : o socket que foi aberto, o id do peer atual
#             e o id do peer que solicitou a conexao
def handlerCliente(s, idPeer, idDestino):
    logging.info("Inicio da troca de mensagens entre o peer " + str(idPeer) + " e o peer " + str(idDestino))
    try:
        while True and tExit == 0:
            time.sleep(HB_PERIOD - 1)
            stopHbs = sendHeartbeat(idPeer, idDestino, s)
            if(stopHbs == 1):
                #Para de enviar heartbeats
                return 1

            logging.info("Peer " + str(idPeer) + " enviou mensagem do tipo HEARTBEAT para o peer " + str(idDestino))

    except KeyboardInterrupt:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        logging.warning("Peer " + str(idPeer) + " finalizou conexao com o peer " + str(idDestino))
        sys.exit()

    except socket.error:
        s.close()
        logging.error("Erro no socket entre peer " + str(idPeer) + " e peer " + str(idDestino) + ". Fechando socket")
        return 1

    except socket.timeout:
        s.close()
        logging.error("Erro no socket entre peer " + str(idPeer) + " e peer " + str(idDestino) + ". Fechando socket")
        return 1
    return 1

#Funcao que envia um heartbeat para um peer
#Parametros : o id do peer atual, o id do peer do destino
#             e o socket aberto da conexao
def sendHeartbeat(idPeer, idDestino, s):
        msg = message.Message(HEARTBEAT, idPeer, idDestino)
        try:
            s.send(msg.empacotar())
        except socket.error:
            #print("Erro de broken pipe")
            s.close()
            logging.error("Fechando as conexoes entre o peer " + str(idPeer) + " e peer " + str(idDestino) + ". Fechando socket")
            return 1
        return 0

#Funcao que cria conexao inicial entre todos os hosts
#Parametros : o id do peer atual
def emparelhaHosts(idPeer):
    logging.info("Peer " + str(idPeer) + " vai se emparelhar com os outros hosts")
    hostsValidos = 1
    #Lista para saber quais hosts ja estao conectados, evitando que novas
    #tentativas de conexao aos mesmos sejam feitas
    hostsConectados = []
    listaThreads = []
    while hostsValidos < len(hosts):
        for h in hosts:
            idDestino = h.getId()
            if ((idDestino != idPeer) and (not(idDestino in hostsConectados))):
                try:
                    time.sleep(0.5)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    logging.info("Peer " + str(idPeer) + " solicitou conexao ao peer " + str(idDestino))
                    s.connect((h.getIp(), h.getPorta())) #Tenta se conectar ao destino (chamada bloqueante)
                    sockList[idDestino] = s  #Coloca novo socket com qual se conectou em uma lista de sockets
                    t = threading.Thread(target=handlerCliente, args=[s, idPeer, idDestino])
                    listaThreads.append(t)
                    print("Conectado com o peer " + str(idDestino))
                    hostsConectados.append(idDestino)
                    hostsValidos = hostsValidos + 1
                    logging.info("Peer " + str(idPeer) + " conseguiu se conectar ao peer " + str(idDestino))
                except Exception as e:
                    print("Aguardando conexao com o peer " + str(idDestino))
                    logging.error("Peer " + str(idPeer) + " ainda nao conseguiu se conectar ao peer " + str(idDestino))
    print("{}{}{}".format("Peer ", idPeer, " conseguiu se conectar com todos os outros peers"))
    logging.info("Peer " + str(idPeer) + " conseguiu se conectar com todos os outros peers")
    for t in listaThreads:
        t.start()
    return 0

def mensagemInicial():
    print("\nPROGRAMA N-PEER")
    print("===============")

if __name__ == "__main__":
    main()
