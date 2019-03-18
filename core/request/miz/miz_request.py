import time
import socket
import json
from config.settings import HOST, PORT, EOT, SHOW_REQUEST, TIMEOUT
from msg_fmt import send_msg


class RequestHandle:
    MESSAGE = "message"
    ACTION = "action"
    EVENT = "event"  # ask for next event?
    PRECISE_EVENT = "precise_event"
    QUERY = "query"  # ask for information
    DEBUG = "debug"  # mist do string
    PULL = "pull"    # server prepare a pull to python to analyze?


class RequestDcs:
    def __init__(self, handle):
        # super().__init__()
        self.request_time = int(time.time())
        self.handle = handle

    def send(self):
        # deal with empty value in dict here
        outMsg = "\r\n" \
                 + json.dumps(self.__dict__) \
                 + "\r\n"

        outb = bytes(outMsg, 'utf-8')

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                s.settimeout(TIMEOUT)

                # outMsg = "\r\n" \
                # + json.dumps(self.__dict__) \
                # + "\r\n"

                if SHOW_REQUEST:
                    print("ENV Request: " + outMsg.strip())  # DCS: Request print

                # outb = bytes(outMsg, 'utf-8')

                send_msg(s, outb)

                tm = b""

                while True:
                    mp = s.recv(1024)
                    tm += mp

                    if tm[-3:] == EOT.encode('utf-8'):
                        break

        except ConnectionResetError:
            connected = False
            s.close()
            print("ENV connection lost... reconnecting in 3 seconds")
            time.sleep(1)
            while not connected:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((HOST, PORT))
                    s.settimeout(TIMEOUT)
                    connected = True

                    # outMsg = "\r\n" \
                    #          + json.dumps(self.__dict__) \
                    #          + "\r\n"

                    print("ENV control stuck!")

                    print("ENV Request: " + outMsg.strip())  # DCS: Request print

                    # outb = bytes(outMsg, 'utf-8')

                    send_msg(s, outb)
                    tm = b""

                    while True:
                        mp = s.recv(1024)

                        tm += mp

                        if tm[-3:] == EOT.encode('utf-8'):
                            break

                    s.close()

                except ConnectionResetError:
                    print("ENV ConnectionResetError ... retrying after 10 seconds.")
                    connected = False
                    s.close()
                    time.sleep(10)

                except socket.timeout:
                    connected = False
                    s.close()
                    time.sleep(1)

                except ConnectionRefusedError:
                    print("ENV ConnectionRefusedError ... retrying after 10 seconds.")
                    connected = False
                    s.close()
                    time.sleep(10)

        except ConnectionRefusedError:
            connected = False
            s.close()
            print("ENV connection lost... reconnecting")
            time.sleep(1)
            while not connected:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((HOST, PORT))
                    s.settimeout(TIMEOUT)
                    connected = True

                    # outMsg = "\r\n" \
                    #          + json.dumps(self.__dict__) \
                    #          + "\r\n"

                    print("ENV control stuck!")

                    print("ENV Request: " + outMsg.strip())  # DCS: Request print

                    # outb = bytes(outMsg, 'utf-8')

                    send_msg(s, outb)
                    tm = b""

                    while True:
                        mp = s.recv(1024)

                        tm += mp

                        if tm[-3:] == EOT.encode('utf-8'):
                            break

                    s.close()

                except ConnectionResetError:
                    print("ENV ConnectionResetError ... retrying after 10 seconds.")
                    connected = False
                    s.close()
                    time.sleep(10)

                except socket.timeout:
                    connected = False
                    s.close()
                    time.sleep(1)

                except ConnectionRefusedError:
                    print("ENV ConnectionRefusedError ... retrying after 10 seconds.")
                    connected = False
                    s.close()
                    time.sleep(10)

        except socket.timeout:
            connected = False
            s.close()
            print("ENV connection lost... reconnecting in 3 seconds.")
            time.sleep(1)
            while not connected:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((HOST, PORT))
                    s.settimeout(TIMEOUT)
                    connected = True

                    # outMsg = "\r\n" \
                    # + json.dumps(self.__dict__) \
                    # + "\r\n"

                    print("ENV control stuck!")

                    print("ENV Request: " + outMsg.strip())  # DCS: Request print

                    # outb = bytes(outMsg, 'utf-8')

                    send_msg(s, outb)
                    tm = b""

                    while True:
                        mp = s.recv(1024)

                        tm += mp

                        if tm[-3:] == EOT.encode('utf-8'):
                            break

                    s.close()

                except ConnectionResetError:
                    print("ENV ConnectionResetError ... retrying after 10 seconds.")
                    connected = False
                    s.close()
                    time.sleep(10)

                except socket.timeout:
                    connected = False
                    s.close()
                    time.sleep(1)

                except ConnectionRefusedError:
                    print("ENV ConnectionRefusedError ... retrying after 10 seconds.")
                    connected = False
                    s.close()
                    time.sleep(10)

        q_result = json.loads(tm.decode('utf-8')[:-1])
        return q_result  # return dictionary
