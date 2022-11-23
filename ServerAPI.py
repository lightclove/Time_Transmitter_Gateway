# -*- coding: utf-8 -*-
#!/usr/bin/env python2
###############################################################################
# Назначение: API Сервера передачи данных точного времени
###############################################################################
from dpa.server.Service import BaseService
from dpa.server.Application import getApplication

class ServerAPI(BaseService):
    def __init__(self):
        super(ServerAPI, self).__init__()
        self.mainApp = getApplication()

    def makeAPIDeclarations(self): # Объявление методов API
        self.declareAPI('ServerAPI', (
            'connCheck', # Метод проверки доступности передатчика
            'getSluiceConnStatus', # Метод, возвращающий результат последней проверки связи со шлюзом
            'getLastSentPacketID', # Метод, возвращающий номер последнего переданного пакета
            'getUsingModelType' # Метод, возвращающий тип модели, используемой для расчёта/предсказания значений задержки
            ))

    def connCheck(self):
        print 'Проверка связи с передатчиком от внешней мониторирующей системы прошла успешно.'
        return True

    def getSluiceConnStatus(self):
        print 'Получен запрос о доступности шлюза однонаправленной передачи данных.'
        return self.mainApp.sluiceConnStatus

    def getLastSentPacketID(self):
        print 'Получен запрос о номере последнего переданного пакета.'
        return self.mainApp.pastPackID

    def getUsingModelType(self):
        print 'Получен запрос о типе модели, используемой для расчёта/предсказания значений задержки.'
        return self.mainApp.modelType
