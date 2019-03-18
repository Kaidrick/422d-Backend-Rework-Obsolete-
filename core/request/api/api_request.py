import time
import socket
import json
from config.settings import HOST, API_PORT, SHOW_REQUEST, TIMEOUT

class RequestApiHandle:
    DEBUG = "net_debug"
    QUERY = "net_query"
    PULL = "net_pull"
    MESSAGE = "net_message"


def filter_none_value(kn_dict):
    clean_dict = {}
    for key, value in kn_dict.items():
        if value:  # not None value
            clean_dict[key] = value

    return clean_dict


class RequestApi:
    def __init__(self, handle):
        # super().__init__()
        self.request_time = int(time.time())
        self.handle = handle

    def send(self):
        out_msg = json.dumps(self.__dict__) + "\n"

        out_bytes = bytes(out_msg, 'utf-8')

        while True:
            retry_count = 0

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((HOST, API_PORT))
                    s.settimeout(TIMEOUT)

                    if SHOW_REQUEST:
                        print("HOOK Request: " + out_msg.strip())  # DCS: Request print

                    s.sendall(out_bytes)

                    tm = b""

                    while True:
                        mp = s.recv(256)  # 1024
                        tm += mp

                        if tm.endswith(b"\n"):
                            break
                        # if tm[-3:] == EOT.encode('utf-8'):
                        #     break

                try:
                    q_result = json.loads(tm.decode('utf-8')[:-1])
                except json.decoder.JSONDecodeError as e:
                    print(__file__, "Error: ", e)
                    return {}
                else:
                    return q_result  # return dictionary

            except Exception as e:
                retry_count += 1
                if retry_count < 20:
                    print("[HOOK] Socket Exception: ", e)  # do nothing, wait for retry
                    print(out_msg.strip())
                    time.sleep(3)
                else:  # more than 20 exceptions, break and stop
                    break

            break


if __name__ == '__main__':
    RequestApi(handle=RequestApiHandle.QUERY).send()
