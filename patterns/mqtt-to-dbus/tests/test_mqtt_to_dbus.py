"""Unit tests for MQTT → D-Bus Bridge."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.mqtt_to_dbus import MQTTToDBusBridge


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample config file for testing."""
    config = {
        "mqtt": {
            "host": "localhost",
            "port": 1883,
            "client_id": "test-bridge",
        },
        "dbus": {
            "service_name": "com.victronenergy.test",
            "device_instance": 40,
            "product_name": "Test Bridge",
        },
        "mappings": [
            {
                "mqtt_topic": "sensor/temperature",
                "dbus_path": "/Temperature",
                "dbus_type": "double",
                "value_template": "{{ value_json.temperature }}",
            },
            {
                "mqtt_topic": "sensor/humidity",
                "dbus_path": "/Humidity",
                "dbus_type": "double",
            },
            {
                "mqtt_topic": "sensor/power",
                "dbus_path": "/Power",
                "dbus_type": "int32",
            },
        ],
    }
    config_path = tmp_path / "config.yaml"
    import yaml
    config_path.write_text(yaml.dump(config))
    return str(config_path)


@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_bridge_initialization(mock_mqtt_client, mock_system_bus, sample_config):
    """Test bridge initializes correctly."""
    mock_bus = MagicMock()
    mock_system_bus.return_value = mock_bus
    mock_bus.request_name.return_value = None

    bridge = MQTTToDBusBridge(sample_config)

    assert bridge.mqtt_config["host"] == "localhost"
    assert bridge.dbus_config["service_name"] == "com.victronenergy.test"
    assert len(bridge.mappings) == 3


@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_value_conversion(mock_mqtt_client, mock_system_bus, sample_config):
    """Test value type conversion."""
    mock_bus = MagicMock()
    mock_system_bus.return_value = mock_bus

    bridge = MQTTToDBusBridge(sample_config)

    # Test double conversion
    assert bridge._convert_value("25.5", "double") == 25.5
    assert bridge._convert_value(25, "double") == 25.0

    # Test int32 conversion
    assert bridge._convert_value("100", "int32") == 100
    assert bridge._convert_value(100.7, "int32") == 100

    # Test boolean conversion
    assert bridge._convert_value("true", "boolean") is True
    assert bridge._convert_value("false", "boolean") is False
    assert bridge._convert_value("1", "boolean") is True
    assert bridge._convert_value("0", "boolean") is False
    assert bridge._convert_value(True, "boolean") is True

    # Test string conversion
    assert bridge._convert_value(123, "string") == "123"


@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_extract_value_with_template(mock_mqtt_client, mock_system_bus, sample_config):
    """Test value extraction with Jinja2 template."""
    mock_bus = MagicMock()
    mock_system_bus.return_value = mock_bus

    bridge = MQTTToDBusBridge(sample_config)

    # Mock template rendering
    with patch.object(bridge, "_templates", {"sensor/temperature": MagicMock()}):
        bridge._templates["sensor/temperature"].render.return_value = "25.5"

        payload = json.dumps({"temperature": 25.5})
        mapping = bridge.mappings[0]

        result = bridge._extract_value(payload, mapping)

        assert result == 25.5
        bridge._templates["sensor/temperature"].render.assert_called_once_with(value_json={"temperature": 25.5})


@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_extract_value_direct_json(mock_mqtt_client, mock_system_bus, sample_config):
    """Test value extraction from direct JSON."""
    mock_bus = MagicMock()
    mock_system_bus.return_value = mock_bus

    bridge = MQTTToDBusBridge(sample_config)

    # Test with "value" key
    payload = json.dumps({"value": 42.0})
    mapping = bridge.mappings[1]  # humidity mapping
    result = bridge._extract_value(payload, mapping)
    assert result == 42.0

    # Test with "state" key
    payload = json.dumps({"state": "75.5"})
    result = bridge._extract_value(payload, mapping)
    assert result == 75.5


@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_extract_value_plain_text(mock_mqtt_client, mock_system_bus, sample_config):
    """Test value extraction from plain text payload."""
    mock_bus = MagicMock()
    mock_system_bus.return_value = mock_bus

    bridge = MQTTToDBusBridge(sample_config)

    # Plain number as text
    payload = "123.45"
    mapping = bridge.mappings[1]
    result = bridge._extract_value(payload, mapping)
    assert result == 123.45


@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_on_mqtt_connect(mock_mqtt_client, mock_system_bus, sample_config):
    """Test MQTT connect callback subscribes to topics."""
    mock_bus = MagicMock()
    mock_system_bus.return_value = mock_bus

    bridge = MQTTToDBusBridge(sample_config)

    # Mock service
    bridge.service = MagicMock()

    mock_client = MagicMock()
    bridge._on_mqtt_connect(mock_client, None, None, 0, None)

    assert mock_client.subscribe.call_count == 3
    bridge.service.set_connected.assert_called_once_with(True)


@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_on_mqtt_message_updates_dbus(mock_mqtt_client, mock_system_bus, sample_config):
    """Test MQTT message updates D-Bus path."""
    mock_bus = MagicMock()
    mock_system_bus.return_value = mock_bus

    bridge = MQTTToDBusBridge(sample_config)
    bridge.service = MagicMock()

    # Create mock message
    mock_msg = MagicMock()
    mock_msg.topic = "sensor/temperature"
    mock_msg.payload = json.dumps({"temperature": 22.5}).encode()

    bridge._on_mqtt_message(None, None, mock_msg)

    bridge.service.update_path.assert_called_once_with("/Temperature", 22.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])