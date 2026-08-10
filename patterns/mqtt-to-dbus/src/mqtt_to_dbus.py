#!/usr/bin/env python3
"""
MQTT → D-Bus Bridge for Venus OS

Subscribes to MQTT topics and publishes values as D-Bus service paths.
"""

import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Any

import paho.mqtt.client as mqtt
import yaml
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

try:
    import dbus
    import dbus.service
except ImportError:
    print("dbus-python not installed. On Venus OS: opkg install python3-dbus")
    sys.exit(1)

try:
    from jinja2 import Template
except ImportError:
    Template = None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DBusGMainLoop(set_as_default=True)


class DBusService(dbus.service.Object):
    """D-Bus service exposing MQTT values as paths."""

    def __init__(self, bus, service_name: str, device_instance: int, product_name: str):
        self.service_name = service_name
        self.device_instance = device_instance
        self.paths = {}
        self.values = {}
        self._connected = 1

        bus.request_name(service_name, dbus.bus.NAME_FLAG_DO_NOT_QUEUE)
        super().__init__(bus, f"/{service_name.replace('.', '_')}")

        # Standard paths
        self.set_path("/DeviceInstance", device_instance, "uint32")
        self.set_path("/ProductId", 0xFFFF, "uint16")
        self.set_path("/ProductName", product_name, "string")
        self.set_path("/FirmwareVersion", "1.0.0", "string")
        self.set_path("/Connected", 1, "uint8")
        self.set_path("/CustomName", product_name, "string")

        logger.info(f"Registered D-Bus service: {service_name}")

    def set_path(self, path: str, value: Any, dbus_type: str = "double"):
        """Set a D-Bus path value."""
        self.paths[path] = dbus_type
        self.values[path] = value
        self.PropertiesChanged(self.service_name, {path: self._to_dbus_variant(value, dbus_type)}, [])

    def update_path(self, path: str, value: Any):
        """Update an existing D-Bus path value."""
        if path in self.values and self.values[path] != value:
            self.values[path] = value
            dbus_type = self.paths.get(path, "double")
            self.PropertiesChanged(self.service_name, {path: self._to_dbus_variant(value, dbus_type)}, [])
            logger.debug(f"Updated {path} = {value}")

    def set_connected(self, connected: bool):
        """Update connection status."""
        self._connected = 1 if connected else 0
        self.update_path("/Connected", self._connected)

    def _to_dbus_variant(self, value: Any, dbus_type: str):
        """Convert Python value to D-Bus variant."""
        type_map = {
            "double": dbus.Double,
            "int32": dbus.Int32,
            "uint32": dbus.UInt32,
            "uint16": dbus.UInt16,
            "string": dbus.String,
            "boolean": dbus.Boolean,
        }
        return type_map.get(dbus_type, dbus.Double)(value)

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="ss", out_signature="v")
    def Get(self, interface: str, property_name: str):
        if property_name in self.values:
            dbus_type = self.paths.get(property_name, "double")
            return self._to_dbus_variant(self.values[property_name], dbus_type)
        raise dbus.exceptions.DBusException("Property not found", name="org.freedesktop.DBus.Properties.UnknownProperty")

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface: str):
        result = {}
        for path, value in self.values.items():
            dbus_type = self.paths.get(path, "double")
            result[path] = self._to_dbus_variant(value, dbus_type)
        return result

    @dbus.service.signal("org.freedesktop.DBus.Properties", signature="sa{sv}as")
    def PropertiesChanged(self, interface: str, changed: dict, invalidated: list):
        pass


class MQTTToDBusBridge:
    """Main bridge class."""

    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.mqtt_config = self.config["mqtt"]
        self.dbus_config = self.config["dbus"]
        self.mappings = self.config.get("mappings", [])

        self.bus = dbus.SystemBus()
        self.service = DBusService(
            self.bus,
            self.dbus_config["service_name"],
            self.dbus_config.get("device_instance", 40),
            self.dbus_config.get("product_name", "MQTT Bridge"),
        )

        self.mqtt_client = mqtt.Client(
            client_id=self.mqtt_config.get("client_id", "mqtt-to-dbus-bridge"),
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )

        if self.mqtt_config.get("username"):
            self.mqtt_client.username_pw_set(
                self.mqtt_config["username"],
                self.mqtt_config.get("password", ""),
            )

        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        self.mqtt_client.on_message = self._on_mqtt_message

        self._templates = {}
        for mapping in self.mappings:
            if mapping.get("value_template") and Template:
                self._templates[mapping["mqtt_topic"]] = Template(mapping["value_template"])

        self.running = False

    def _on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info("Connected to MQTT broker")
            self.service.set_connected(True)
            for mapping in self.mappings:
                client.subscribe(mapping["mqtt_topic"], qos=1)
                logger.info(f"Subscribed to {mapping['mqtt_topic']}")
        else:
            logger.error(f"MQTT connection failed: {reason_code}")
            self.service.set_connected(False)

    def _on_mqtt_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        logger.warning(f"Disconnected from MQTT broker: {reason_code}")
        self.service.set_connected(False)

    def _on_mqtt_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            logger.debug(f"Received on {msg.topic}: {payload}")

            for mapping in self.mappings:
                if msg.topic == mapping["mqtt_topic"]:
                    value = self._extract_value(payload, mapping)
                    if value is not None:
                        self.service.update_path(mapping["dbus_path"], value)
                    break
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _extract_value(self, payload: str, mapping: dict):
        """Extract value from MQTT payload using template or direct JSON."""
        import json

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {"value": payload}

        if mapping["mqtt_topic"] in self._templates:
            template = self._templates[mapping["mqtt_topic"]]
            try:
                rendered = template.render(value_json=data)
                return self._convert_value(rendered, mapping.get("dbus_type", "double"))
            except Exception as e:
                logger.error(f"Template error for {mapping['mqtt_topic']}: {e}")
                return mapping.get("default")

        # Direct key extraction
        if isinstance(data, dict):
            # Try common keys
            for key in ["value", "state", "payload", mapping["dbus_path"].lstrip("/").lower()]:
                if key in data:
                    return self._convert_value(data[key], mapping.get("dbus_type", "double"))

        return self._convert_value(data, mapping.get("dbus_type", "double"))

    def _convert_value(self, value: Any, dbus_type: str):
        """Convert value to appropriate type."""
        try:
            if dbus_type == "int32":
                return int(value)
            elif dbus_type == "uint32":
                return int(value)
            elif dbus_type == "uint16":
                return int(value)
            elif dbus_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)
            elif dbus_type == "string":
                return str(value)
            else:  # double
                return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert {value} to {dbus_type}, using default")
            return None

    def run(self):
        """Start the bridge."""
        self.running = True

        # Connect to MQTT
        host = self.mqtt_config.get("host", "localhost")
        port = self.mqtt_config.get("port", 1883)
        logger.info(f"Connecting to MQTT broker at {host}:{port}")
        self.mqtt_client.connect(host, port, keepalive=60)
        self.mqtt_client.loop_start()

        # Run GLib main loop for D-Bus
        loop = GLib.MainLoop()

        def signal_handler(signum, frame):
            logger.info("Shutting down...")
            self.running = False
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            loop.quit()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info("Bridge running. Press Ctrl+C to stop.")
        loop.run()


def main():
    parser = argparse.ArgumentParser(description="MQTT → D-Bus Bridge for Venus OS")
    parser.add_argument("-c", "--config", default="config.yaml", help="Config file path")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        logger.info(f"Copy config.yaml.example to {config_path} and edit it")
        sys.exit(1)

    bridge = MQTTToDBusBridge(str(config_path))
    bridge.run()


if __name__ == "__main__":
    main()