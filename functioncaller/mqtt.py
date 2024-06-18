import paho.mqtt.client as client
import threading

from functioncaller.exceptions import RunTimeOrderException


class FunctionCallerMqttEndPoint:
    MQTT_QOS = 0

    def __init__(self, mqtt_url: str, mqtt_port: int, mqtt_username: str, mqtt_password: str, tlc: bool = False) -> None:
        self.mqtt_url = mqtt_url
        self.mqtt_port = mqtt_port

        # running status
        self.is_running = False

        self.client = client.Client(clean_session=True, userdata=None, protocol=client.MQTTv311, transport="tcp")
        self.client.username_pw_set(mqtt_username, mqtt_password)
        if tlc: self.client.tls_set()

        self.client.on_connect = self.handle_mqtt_connect
        self.client.on_message = self.handle_mqtt_message

    def run(self, run_in_thread: bool = True) -> None:
        self.prevent_is_not_running()
        self.is_running = True
        self.connect_to_mqtt_broker()

        def _loop():
            while self.is_running:
                self.client.loop()
                self.loop()
            if self.client.is_connected():
                self.disconnect_from_mqtt_broker()

        if run_in_thread: threading.Thread(target=_loop).start()
        else: _loop()

    def prevent_is_connected(self):
        if not self.client.is_connected():
            raise RunTimeOrderException()

    def prevent_is_not_connected(self):
        if self.client.is_connected():
            raise RunTimeOrderException()

    def prevent_is_running(self):
        if not self.is_running:
            raise RunTimeOrderException()

    def prevent_is_not_running(self):
        if self.is_running:
            raise RunTimeOrderException()

    def connect_to_mqtt_broker(self) -> None:
        self.prevent_is_running()
        self.prevent_is_not_connected()

        self.client.connect(self.mqtt_url, self.mqtt_port)

    def disconnect_from_mqtt_broker(self) -> None:
        self.prevent_is_not_running()
        self.prevent_is_connected()

        self.client.disconnect()

    def loop(self):
        self.prevent_is_running()
        self.prevent_is_connected()

    def handle_mqtt_connect(self, *args, **kwargs) -> None:
        print(f"Connected to '{self.mqtt_url}'")

    def handle_mqtt_message(self, *args, **kwargs) -> None:
        pass
