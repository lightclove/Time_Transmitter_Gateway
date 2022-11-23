# Отображение и изменение таблиц преобразования IP-адресов в физические, используемые протоколом разрешения адресов (ARP).
# Комментарии по arp:
# ARP -s inet_addr eth_addr [if_addr]
# ARP -d inet_addr [if_addr]
# ARP -a [inet_addr] [-N if_addr] [-v]
# arp -d Удаляет узел, задаваемый inet_addr. Параметр inet_addr может содержать знак шаблона * для удаления всех узлов.
# ARP -N if_addr Отображает ARP-записи для заданного в if_addr сетевого интерфейса.
# eth_addr Определяет физический адрес.
# if_addr  Если параметр задан, он определяет адрес интерфейса в
# Интернете, чья таблица преобразования адресов должна измениться. Если параметр не задан, будет использова первый доступный интерфейс.
# Пример:
#  > arp -s 157.55.85.212   00-aa-00-62-c6-09  .. Добавляет статическую запись.
#  > arp -a                                    .. Выводит ARP-таблицу.
########################################################################################################################
import os, time, socket
from socket import socket as Socket, AF_INET, SOCK_DGRAM

if __name__ == '__main__':
    host = '192.168.214.130'
    sock = Socket(AF_INET, SOCK_DGRAM)

    for i in range(10):
        a = time.time()
        os.system('arp -d ' + host)
        os.system('arp -an ' + host)
        sock.sendto('', (host, 10000))
        os.system('arp -an ' + host)
        b = time.time()
        print
        b - a
        time.sleep(3)
