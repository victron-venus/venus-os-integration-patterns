# D-Bus → MQTT Bridge Pattern

Monitor D-Bus paths and publish changes to MQTT topics. Useful for exposing Venus OS data to Home Assistant, Grafana, or other MQTT consumers.

## Use Cases

- Expose Venus OS inverter data to Home Assistant via MQTT discovery
- Stream battery metrics to InfluxDB/Grafana via Telegraf MQTT consumer
- Forward D-Bus events to external automation systems

## Configuration

```yaml
mqtt:
  host: "mqtt-broker"
  port: 1883
  username: ""
  password: ""
  client_id: "dbus-to-mqtt-bridge"
  discovery_prefix: "homeassistant"  # For HA MQTT discovery

dbus:
  - service: "com.victronenergy.vebus.ttyO1"
    paths:
      - "/Ac/ActiveIn/ActivePower"
      - "/Ac/Out/ActivePower"
      - "/Soc"
    topic_prefix: "venus/vebus"

  - service: "com.victronenergy.battery.ttyUSB0"
    paths:
      - "/Soc"
      - "/Voltage"
      - "/Current"
      - "/Temperature"
    topic_prefix: "venus/battery"
```

## Running

```bash
docker-compose up -d
```

## Files

| File | Description |
|------|-------------|
| `src/dbus_to_mqtt.py` | Main bridge implementation |
| `config.yaml.example` | Example configuration |
| `docker-compose.yml` | Docker deployment |
| `Dockerfile` | Container image |
| `requirements.txt` | Python dependencies |

See the source code for implementation details.