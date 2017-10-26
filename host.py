#!/usr/bin/python

class Host(object):
    def __init__ (self):
        self.id = 0
        self.ip = "127.0.0.1"
        self.porta = 5665

    #Extrai da linha do arquivo lido, as colunas que contem infos dos hosts
    def __init__ (self, row):
        self.setId(row[0])
        self.setIp(row[1])
        self.setPorta(row[2])

    #Tipo
    def getId(self):
        return self.id

    def setId(self, id):
        self.id = int(id) #converte char pra int

    #IP do host
    def getIp(self):
        return self.ip

    def setIp(self, ip):
        self.ip = ip

    #Porta
    def getPorta(self):
        return self.porta

    def setPorta(self, porta):
        self.porta = int(porta)