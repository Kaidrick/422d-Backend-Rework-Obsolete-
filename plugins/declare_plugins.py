import threading

plugin_mains = {}


def plugin_log(plugin_name, msg):
    print(f"LOG <{plugin_name}>: {msg}")


def load_plugins():
    for plugin_name, plugin_main in plugin_mains.items():
        print(f"Loading <{plugin_name}>")
        threading.Thread(target=plugin_main).start()
