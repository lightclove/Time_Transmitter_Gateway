# -*- coding: utf-8 -*-
#!/usr/bin/env python2
###############################################################################
#Назначение: Модуль инициализация программного шлюза передачи данных точного
#времени
###############################################################################
import sys

from dpa.lib.initLocale import initLocale
initLocale()
del initLocale

import warnings
warnings.filterwarnings("ignore", message=".*pep-0263.*", module='.*', category=DeprecationWarning, append=1)

from optparse import OptionParser
from Server import Server
from dpa.lib.daemonize import daemonize

if __name__ == '__main__':
###### parse command line parameters##############
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config", default='',
		    help="set path to config file")

    parser.add_option("-d", "--debug", dest="daemonize", default=True,
                  action="store_false",
                  help="run in debug mode (not became daemon)")

    (options, args) = parser.parse_args()
    if options.daemonize:
        daemonize(pidfile='/var/run/gateSend.pid')

##################### end parse ##################
    s=Server(options.config)
    if s:
      s.run()
    else:
      raise Exception, "Starting server failed"
