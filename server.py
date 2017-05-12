import socket
import magic_ping
import os
import settings
import datetime
import signal
import logging

logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s', level=logging.DEBUG, filename=u'server.log')


# Обработка CTRL+C
def signal_handler(signal, frame):
    print("\nSTOP SERVER.")
    s.close()
    logging.info("STOP SERVER.")
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("START SERVER!!!")
logging.info("START SERVER!!!")

s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
s.bind(('', settings.PORT))

files = {}
counters = {}

file = None
ID = 1
count = 0  # счетчик принятых пакетов
while True:
    client_address, packet_number, data = magic_ping.receive_ping(s, ID, counters)

    if not client_address:
        continue

    if packet_number == 1:
        # кортеж с именами директорий, которые нужно создать
        path = (client_address[0], datetime.datetime.now().strftime("%d-%m-%Y %H:%M"))

        tmp = ''  # путь до самой глубокой директории, создаваться они будут по очереди
        for dir_name in path:
            if len(tmp):
                tmp += '/' + dir_name
            else:
                tmp = dir_name
            try:
                os.mkdir(tmp)
                logging.debug("Create folder: %s" % tmp)
                os.chmod(tmp, 0o777)
            except FileExistsError:  # если такая директория уже существует, то просто создаем следующую
                pass

        file_name = data.decode().split('/')[-1]  # если имя файла было передано с учетом каталогов, избавляемся от них
        logging.debug("Receive new file: %s, from: %s" % (file_name, client_address[0]))
        file_name = tmp + '/' + file_name  # имя файла с учетом директорий, в которых он должен находиться

        file = open(file_name, 'wb')
        os.chmod(file_name, 0o777)
        count = 1

        files[client_address[0]] = file
        counters[client_address[0]] = count
        continue

    if file and packet_number > 1:
        counters[client_address[0]] += 1
        logging.debug("%d packet has been received" % counters[client_address[0]])
        files[client_address[0]].write(data)
        continue

    if file and packet_number == 0:
        files[client_address[0]].close()
        logging.info("receive file from: %s, number of packets: %d" % (client_address[0], counters[client_address[0]]))
        print("receive file from:", client_address[0], "number of packets:", counters[client_address[0]])
