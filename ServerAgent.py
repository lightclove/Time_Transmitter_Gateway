# -*- coding: utf-8 -*-
#!/usr/bin/env python2
###############################################################################
# Назначение: XMLNMP-Агент мониторинга
###############################################################################

from XMLNMP.XMLNMPCommon import UserType, Scalar, Notification, atREADONLY
from XMLNMP.XMLNMPAgent import XMLNMPAgent
from dpa.server.Application import getApplication

class ServerAgent(XMLNMPAgent):
    def __init__(self):
        super(ServerAgent, self).__init__()
        # self.mainApp = getApplication()
        self.serverStatus = 1
        self.transmitStatus = 1

    def declareObjects(self): # Объявление извещений и их параметров (в виде переменных)
        self.declareUserType(UserType('Working', 'Enumerated',
                                      ((0, 'false', 'Не работает'), (1, 'true', 'Работает'))))
        # Параметры извещений будут иметь одно из двух состояний: Работает, Не работает

        self.declareVariable(Scalar('serverStatus', 'Working', access=atREADONLY)) 
        self.declareNotification(Notification('serverStatusChange', ('serverStatus',)))

        self.declareVariable(Scalar('transmitStatus', 'Working', access=atREADONLY))
        self.declareNotification(Notification('transmitStatusChange', ('transmitStatus',)))

    def _get_serverStatus(self):
        return self.serverStatus

    def _get_transmitStatus(self):
        return self.transmitStatus
