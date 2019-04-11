import time
import socket
import json
from config.settings import HOST, DATA_PORT, SHOW_REQUEST, TIMEOUT


class RequestExportHandle:
    DEBUG = "data_debug"
    QUERY = "data_query"


class RequestExport:
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
                    s.connect((HOST, DATA_PORT))
                    s.settimeout(TIMEOUT)

                    if SHOW_REQUEST:
                        print("EXPORT Request: " + out_msg.strip())  # DCS: Request print

                    s.sendall(out_bytes)

                    tm = b""

                    while True:
                        mp = s.recv(256)  # 1024
                        tm += mp

                        if tm.endswith(b"\n"):
                            break

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
                    print("[EXPORT] Socket Exception: ", e)  # do nothing, wait for retry
                    print(out_msg.strip())
                    time.sleep(3)
                else:  # more than 20 exceptions, break and stop
                    break

            break


if __name__ == '__main__':
    while True:
        RequestExport(handle=RequestExportHandle.QUERY).send()
        print(time.time())
