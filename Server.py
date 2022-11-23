# -*- coding: utf-8 -*-
#!/usr/bin/env python2
###############################################################################
# Назначение: Сервер передачи данных точного времени
###############################################################################
import sys, os

from dpa.lib.initLocale import initLocale
initLocale()
from dpa.lib.convertCyrillic import convertCyrillic
_ = convertCyrillic("UTF-8")
del initLocale, convertCyrillic ##############################################

from dpa.server.Application import Application, getApplication
from dpa.server.HTTPDispatcher import HTTPRequestPathDispatcher
from dpa.server.HTTPHandler import HTTPHandler
from dpa.server.Server import QueuedThreadingTCPServer
from dpa.server.XMLRPCProcessor import XMLRPCProcessor
from dpa.server.Task import PeriodicTask

# import dpa.lib.log as log # Windows
# import dpa.lib.logConfig as logConfig # Windows
from dpa.lib import log, logConfig # Linux
from dpa.lib.Config import Config
from dpa.lib.configlib import ConfigParseError
from dpa.lib.PathProvider import PathProvider, atSERVER, alOPT_VENDOR

# from XMLNMP.XMLNMPProcessor import XMLNMPProcessor
from XMLNMP.XMLNMPCommon import enumerated

from socket import socket as Socket, AF_INET, SOCK_DGRAM
import time
import json
import subprocess
from models import *
from ServerAPI import ServerAPI
from ServerAgent import ServerAgent

## from serialize import serialize
## from dpa.client.AuthManager import StaticAuthManager
## from ITCSLib.ITCSErrors import esMEDIATOR, esTC, esOTC
## from ITCSLib.ITCSXMLRPCProxy import ITCSXMLRPCConcurrentProxy


def switchToConst():     # Переход на константу
    mainApp = getApplication()
    mainApp.cntJson = None # Показатель того, что используется: модель либо константа. Здесь - переключение на константу
    sendTask = mainApp.getTask('sendJsonData')
    sendTask._args[3] = mainApp.deltaConst # Вместо значения из кортежа (из Json) подаём на вход sendData константу из конфига
    # sendTask._args[4] = 'constant'
    mainApp.modelType = 'constant' # Меняем тип модели на "константа"
    mainApp.isStarted = True # Включение индикатора первого пакета в новой модели

def sluiceCheck(socket, destIP):    # Проверка шлюза на доступность
    mainApp = getApplication()
    try:
        os.system('arp -d ' + destIP) # Удаление из arp-таблицы записи об IP-адресе приёмника (ему соответствует mac-адрес шлюза)
        # os.system('arp -an ' + destIP) #test
        socket.sendto('', (destIP, 10000)) # Отправка проверочного сообщения
        arpTable = subprocess.check_output(['arp', '-an', destIP]) # Проверка arp-таблицы на то, обновилась она или нет
        # raise Exception('test') #test
        if arpTable.split(' ')[3] == '<incomplete>': # Если удаленная запись в arp-таблице не появилась снова, значит шлюз не доступен
            mainApp.sluiceConnStatus = '{} - {}'.format(time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(time.time())), False)
            return 0
    except Exception as e:
        mainApp.sluiceConnStatus = '{} - {}'.format(time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(time.time())), 'CheckError')
        raise Exception('Не удаётся проверка связи со шлюзом однонаправленной передачи данных: "{}"'.format(str(e)))


def sendData(socket, host, port, deltaTime): # Подготовка и отправка данных
    mainApp = getApplication()

    '''
    # вычисление номера пакета (с учётом текущей даты)
    date = time.strftime("%d.%m.%Y", time.localtime(time.time())) # вычисление текущей даты
    if (mainApp.date != date): # При смене суток
        mainApp.date = date
        mainApp.cnt = 1 # обнулить внутрисуточный счётчик
        packetID = date + "-%s" %mainApp.cnt # установка значения номера пакета
    elif (mainApp.date == date) and (mainApp.packID is None): # Штатная ситуация
        mainApp.cnt += 1 # внутрисуточный счётчик для контроля номера пакета (обнуляется каждые сутки)
        packetID = date + "-%s" %mainApp.cnt # установка значения номера пакета
    elif (mainApp.date == date) and (mainApp.packFailed is not None): # После потери связи
        packetID = mainApp.packFailed # установка значения номера пакета = сохранённому при пропаже связи
        mainApp.cnt = int(packetID.split('-')[1]) # откатить внутрисуточный счётчик
        mainApp.packFailed = None # отключить индикатор отсутствия связи
    '''

    try:
        if sluiceCheck(socket, host) == 0: raise Exception('Нет связи со шлюзом однонаправленной передачи данных') # Linux
        mainApp.sluiceConnStatus = '{} - {}'.format(time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(time.time())), True)
        if mainApp.isStarted: # Если включен индикатор первого пакета в новой модели, то отправляем пакет с названием модели. Иначе - без названия
            socket.sendto('{}, {:.9f}, {:.9f}, {}'.format(mainApp.packetID, time.time(), time.time()+deltaTime, mainApp.modelType), (host, port))  # отправка сообщения с номером пакета, метками времени синего сегмента, красного сегмента (рассчитанной), типом модели расчёта
            mainApp.isStarted = False
            # mainApp.isSwitched = False
        else:
            socket.sendto('{}, {:.9f}, {:.9f}'.format(mainApp.packetID, time.time(), time.time()+deltaTime), (host, port))  # отправка сообщения с номером пакета, метками времени синего сегмента, красного сегмента (рассчитанной)
        print 'Пакет под номером {} отправлен.'.format(mainApp.packetID)
        mainApp.pastPackID = mainApp.packetID # Номер последнего переданного пакета зпоминается (для API)
        mainApp.packetID = (mainApp.packetID + 1) %100 # Штатная ситуация - счётчик (номер пакета) итерируется от 0 до 99
        if mainApp.transmitStatus == 0:
            mainApp.agent.sendNotification('transmitStatusChange', {'transmitStatus':enumerated(1),}) # Посылка извещения о восстановлении возможности передачи данных
            mainApp.transmitStatus = 1
        # print deltaTime #test
    except Exception, err:
        # mainApp.packFailed = mainApp.packetID # включить индикатор отсутствия связи (номер непосланного пакета запоминается)
        if mainApp.cntJson is not None: # В случае модели
            stopMsg = 'Пакет под номером {}. Ошибка отправки: "{}".\nДля возобновления работы с расчётной моделью перезапустите программу.\nПроизведён автоматический переход на установленное вручную значение задержки.\n'.format(mainApp.packetID, str(err))
            switchToConst() # Переход дальнейших функций sendData на константу
        else:
            stopMsg = 'Пакет под номером {}. Ошибка отправки: "{}".\n'.format(mainApp.packetID, str(err))
        print '\n'+stopMsg
        log.error(mainApp.errorLoggerName, stopMsg+'\n')
        if mainApp.transmitStatus == 1:
            mainApp.agent.sendNotification('transmitStatusChange', {'transmitStatus':enumerated(0),}) # Посылка извещения о пропадании возможности передачи данных
            mainApp.transmitStatus = 0

    if mainApp.cntJson is not None: # В случае модели
        mainApp.cntJson += 1 # Счётчик итерируется по кортежу
        sendTask = mainApp.getTask('sendJsonData')
        try:
            sendTask._args[3] = float(mainApp.deltaTuple[mainApp.cntJson]) # Вместо кортежа из Json подаём на вход sendData одно значение из кортежа
        except Exception, err:
            stopMsg = 'Рассчитанные значения задержки окончились! Для возобновления работы с расчётной моделью перезапустите программу.\nПроизведён автоматический переход на установленное вручную значение задержки.\n'
            print '\n'+stopMsg
            log.error(mainApp.errorLoggerName, stopMsg+'\n')
            switchToConst() # Переход дальнейших функций sendData на константу


def sendModelDelta(sock, rHost, rPort, deltaFile, sendPause):
    mainApp = getApplication()

    try:
#        ''' #test
        with open(deltaFile, 'r') as fileJson:
		    parsed = json.loads(fileJson.read())
        for key in parsed.keys():
		    if key != "neighbors": # или: if parsed.keys() == ['neighbors',]:
			    raise Exception("Значения задержки в файле статистики рассчитаны не по модели k-ближайших соседей")
		    mainApp.cntJson = 0 # Счётчик для прохода по Json, а также показатель того, что используется: модель либо константа
		    deltas = parsed.values()
		    mainApp.deltaTuple = tuple(sorted(deltas[0].values()))
		    mainApp.addTask('sendJsonData', PeriodicTask(sendData, [sock, rHost, rPort, float(mainApp.deltaTuple[mainApp.cntJson])], pause=sendPause, interval=sendPause)) # на вход sendData подаётся кортеж значений задержки
		    """
		    for i in xrange(parsed.values().keys()): 
		        dT = parsed.values()[i]
		        sendData(sock, rHost, rPort, dT, model)
		        time.sleep(sendPause) 
		    print 'stopModel'
		    sys.exit('stopModel')
		    """
#        '''#test
#        mainApp.deltaTuple = deltaFile #test
#        mainApp.addTask('sendJsonData', PeriodicTask(sendData, [sock, rHost, rPort, mainApp.deltaTuple[mainApp.cntJson]], pause=sendPause, interval=sendPause)) #test
    except Exception, err:
        stopMsg = 'Ошибка чтения файла статистики "%s": "%s".\nДля возобновления работы с расчётной моделью перезапустите программу.\nПроизведён автоматический переход на установленное вручную значение задержки.\n' % (str(deltaFile), str(err))
        print('\n'+stopMsg)
        log.error(mainApp.errorLoggerName, stopMsg+'\n')
        delta = mainApp.deltaConst # Переход дальнейших функций sendData на константу
        mainApp.modelType = 'constant'
        mainApp.addTask('sendData', PeriodicTask(sendData, [sock, rHost, rPort, delta], pause=sendPause, interval=sendPause))


def Server(configFN):
    app = Application()
    app.pathProvider = PathProvider(appType=atSERVER, appLocation=alOPT_VENDOR, vendor='rubin')
    app.packetID = 0 # Номер пакета
    app.pastPackID = "None" # Номер последнего переданного пакета (для API)
    app.cntJson = None # Счётчик для прохождения по результатам модели
    app.isStarted = True # Индикатор первого пакета в новой модели
    app.transmitStatus = 1 # Возможность передачи данных (для XMLNMP-агента)
    # app.sluiceConnStatus = '{} - {}'.format(time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(time.time())), True)
    # app.date = time.strftime("%d.%m.%Y", time.localtime(time.time()))

    if not configFN:
        configFN = app.pathProvider.appConfigFile
    if not os.path.exists(configFN) or not os.path.isfile(configFN):
#        print _('\nФайл конфигурации "%s" не найден.\n') % configFN
        sys.exit(_('\nФайл конфигурации "%s" не найден.\n') % configFN)
    try:
        conf = Config(configFN)
    except ConfigParseError, ce:
#        print _('\nНевозможно прочитать файл конфигурации: "%s"\n') % ce.args[0]
        sys.exit(_('\nНевозможно прочитать файл конфигурации: "%s"\n' % ce.args[0]))

    if not os.path.exists(app.pathProvider.appLogDir) or not os.path.isdir(app.pathProvider.appLogDir): ##############################################
        os.mkdir(app.pathProvider.appLogDir) ##############################################
    try:
        logConfig.initLogFromConfig(conf, configPath='/log', logDir=app.pathProvider.appLogDir)
    except logConfig.LogConfigError, e:
#        print _('\nОшибка конфигурации системы журналирования: "%s"\n') % str(e)
        sys.exit(_('\nОшибка конфигурации системы журналирования: "%s"\n') % str(e))

    ## app.objects={}
    ## for odc in conf.enumerateGroups("objects"):
    ##     obj = conf.readStr("/objects/%s/name"%odc, '')
    ##     objClass = conf.readStr("/objects/%s/class"%odc, '')
    ##     if not (objClass, obj) in app.objects:
    ##         app.objects[(objClass, obj)]=None
    ## host = conf.readStr("/otc/host", '127.0.0.1')
    ## oPort = conf.readInt("/otc/port", 8205)
    ## login = conf.readStr("/otc/login", 'gate')
    ## password = conf.readStr("/otc/password", 'gate')
    ## proxy = ITCSXMLRPCConcurrentProxy("%s:%d" % (host, oPort), path="/client/", errorSource=esTC)
    ## am = StaticAuthManager()
    ## am.defaultLogin = login
    ## am.defaultPassword = password
    ## proxy.authManager = am
    ## proxy.query = "role=%s"%('ak',)
    ## app.odc = proxy

    # Чтение конфига
    sendPause = conf.readFloat("/sender/period_sec", 10)
    rHost = conf.readStr("/reciever/host", '127.0.0.1')
    rPort = conf.readInt("/reciever/port", 12345)
    model = conf.readStr("/compute_settings/model", 'constant')
    app.deltaConst = (conf.readFloat("/compute_settings/delay_usec", )) * pow(10, -6) # перевод величины задержки из мкс в с
    statFile = conf.readStr("/compute_settings/stat_file", '/home/user/stats.csv')
    ## app.Login = conf.readStr("login", '1')
    ## app.Password = conf.readStr("password", '1')
    APIInterface = conf.readStr("/API/interface", 'localhost')
    APIPort = conf.readInt("/API/port", 12346)
    MngHost = conf.readStr("/Manager/host", '127.0.0.1')
    MngPort = conf.readInt("/Manager/port", 11162)

    # Выбор модели для рассчёта/предсказания значений задержки передачи сообщения
    if (model == 'constant'): delta = app.deltaConst # Значение задержки берётся из конфига (константа)
    else:
	    if not os.path.exists(statFile) or not os.path.isfile(statFile):
	        stopMsg = _('Файл статистики "%s" не найден.\nДля возобновления работы с расчётной моделью перезапустите программу.\nПроизведён автоматический переход на установленное вручную значение задержки.\n') % statFile
	        print '\n'+stopMsg
	        log.error(app.errorLoggerName, stopMsg+'\n')
	        delta = app.deltaConst # Переход на режим работы с константой из конфига
	        model = 'constant' # -||-
	    elif (model == 'mean'): delta = mean(statFile) # Мат. ожидание
	    elif (model == 'linear'): delta = line(statFile) # Линейная регрессия
	    elif (model == 'neighbors'): delta = neighbors(statFile) # Метод k ближайших соседей
	    elif (model == 'forest'): delta = forest(statFile) # Случайный лес
	    else:
	        log.error(app.errorLoggerName, 'Неверное имя модели в конфигурационном файле "%s".\n\n' % configFN)
	        sys.exit('\nНеверное имя модели в конфигурационном файле "%s".\n' % configFN)

    sock = Socket(AF_INET, SOCK_DGRAM) # Открытие сокета

    ### Создание API
    xmlrpcProcessor = XMLRPCProcessor() # Инициализация обработчика данных протокола XML-RPC
    xmlrpcProcessor.addServiceAPI(ServerAPI(),'ServerAPI') # Добавление API к списку доступных API сетевого сервера (serv)

    disp = HTTPRequestPathDispatcher() # Инициализация диспетчера обработчиков HTTP-протокола
    disp.addProcessor("/client", xmlrpcProcessor) # Сопоставление значению path HTTP-запроса ("/agent") обработчик HTTP-протокола

    handler = HTTPHandler() # Инициализация обработчика HTTP-протокола конечного HTTP-сервера (serv)
    handler.processor = disp # Обработчиком HTTP-пакета назначается созданный ранее диспетчер
  
    serv = QueuedThreadingTCPServer((APIInterface,), APIPort, handler) # Инициализация для API параллельного сервера с очередью,
    # использующего в качестве протокола транспортного уровня протокол TCP
    # и осуществляющего обработку запросов в новых нитях управления
    serv.allowReuseAddress=True # Флаг разрешает создание сокетов даже в случае, если порт уже занят
    app.addServer('APIServer', serv) # Добавляет в приложение сетевой сервер (serv), доступ к которому осуществляется по указанному имени ('APIServer')
    ###

    app.agent = ServerAgent() # Инициализация XMLNMP-агента
    app.agent.addNotificationListener('%s:%s'%(MngHost, MngPort)) # Добавляет пару "ip-адрес:порт" в список "слушателей" извещений от XMLNMP-агента
    # xmlnmpAgentProcessor = XMLNMPProcessor(agent)

    # delta = (3600, 7200) #test1
    delta = '/home/user/Sender_lin/testModelResult.json' #test2 # Linux
    # delta = 'testModelResult.json' #test2 # Windows
    model = 'testModel' #test
    app.modelType = model
    if isinstance(delta, float): # Если задержка - константа или мат.ожидание, то сразу sendData()
        app.addTask('sendData', PeriodicTask(sendData, [sock, rHost, rPort, delta], pause=sendPause, interval=sendPause))
    else: # Если задержки - в файле Json, то разбор Json в sendModelDelta(), а оттуда уже запускается sendData()
        sendModelDelta(sock, rHost, rPort, delta, sendPause)

    log.info(app.loggerName, 'Сервер отсылает UDP-датаграммы на {}:{}.'.format(rHost, rPort))
    app.agent.sendNotification('serverStatusChange', {'serverStatus':enumerated(1),}) # Посылка извещения о запуске программы
    log.info(app.loggerName, 'Отправлено извещение о запуске программы.')

    def shutdown(): # Переопределение функции остановки приложения
        # print 'Notification has sent.'
        app.agent.sendNotification('serverStatusChange', {'serverStatus':enumerated(0),}) # Посылка извещения об остановке программы
        log.info(app.loggerName, 'Отправлено извещение об остановке программы.')
        app.shutDown()

    app.signalHandler.setHandler('SIGTERM', shutdown)
    app.signalHandler.setHandler('SIGINT', shutdown)

    return app
