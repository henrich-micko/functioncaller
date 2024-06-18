# FunctionCaller
Python libraly for calling function via mqtt broker. 

## Application side

```python
from functioncaller.app import FunctionCallerApp

app = FunctionCallerApp(
    mqtt_url="<MQTT-BROKER-URL>",
    mqtt_port=8883,
    mqtt_username="<MQTT-USERNAME>",
    mqtt_password="<MQTT-PASSWORD>",
)

@app.add("sum")
def sum(a: int, b: int) -> int:
  return a + b

app.run()
```

## Client side

```python
from functioncaller.client import FunctionCallerClient

client = FunctionCallerClient(
    mqtt_url="<MQTT-BROKER-URL>",
    mqtt_port=8883,
    mqtt_username="<MQTT-USERNAME>",
    mqtt_password="<MQTT-PASSWORD>",
)

client.run(run_in_thread=True)
caller = client.get_caller()

caller.sum(a=5, b=10).then(lambda output: print(f"Output: {output}"))
```

