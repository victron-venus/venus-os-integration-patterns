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

    assert bridge._convert_value("nan", "double") is None
    assert bridge._convert_value("inf", "double") is None
    assert bridge._convert_value("-inf", "double") is None
    assert bridge._convert_value("1e309", "double") is None


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


@pytest.fixture
def config_with_defaults(tmp_path):
    """Config covering declared defaults and no-default mappings."""
    import yaml

    config = {
        "mqtt": {"host": "localhost", "port": 1883, "client_id": "test-bridge"},
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
                "default": 20.0,
            },
            {
                "mqtt_topic": "sensor/humidity",
                "dbus_path": "/Humidity",
                "dbus_type": "double",
                "default": 50.0,
            },
            {
                "mqtt_topic": "sensor/power",
                "dbus_path": "/Ac/Power",
                "dbus_type": "double",
            },
            {
                "mqtt_topic": "sensor/voltage",
                "dbus_path": "/Ac/L1/Voltage",
                "dbus_type": "double",
            },
        ],
    }
    config_path = tmp_path / "config_defaults.yaml"
    config_path.write_text(yaml.dump(config))
    return str(config_path)


@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_mapping_paths_registered_with_defaults(
    mock_mqtt_client, mock_system_bus, config_with_defaults
):
    """Actual DBusService registers mapping paths; defaults are present before MQTT."""
    from src.mqtt_to_dbus import DBusService

    mock_bus = MagicMock()
    mock_system_bus.return_value = mock_bus

    bridge = MQTTToDBusBridge(config_with_defaults)
    assert type(bridge.service) is DBusService

    assert bridge.service.paths["/Temperature"] == "double"
    assert bridge.service.values["/Temperature"] == 20.0
    assert bridge.service.paths["/Humidity"] == "double"
    assert bridge.service.values["/Humidity"] == 50.0
    assert bridge.service.paths["/Ac/Power"] == "double"
    assert "/Ac/Power" not in bridge.service.values
    assert bridge.service.paths["/Ac/L1/Voltage"] == "double"
    assert "/Ac/L1/Voltage" not in bridge.service.values


@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_first_valid_message_creates_and_updates_registered_paths(
    mock_mqtt_client, mock_system_bus, config_with_defaults
):
    """First valid MQTT reading creates unset paths; later values update; non-finite skipped."""
    from src.mqtt_to_dbus import DBusService

    mock_bus = MagicMock()
    mock_system_bus.return_value = mock_bus

    bridge = MQTTToDBusBridge(config_with_defaults)
    assert type(bridge.service) is DBusService

    mock_msg = MagicMock()
    mock_msg.topic = "sensor/power"
    mock_msg.payload = b"123.5"
    bridge._on_mqtt_message(None, None, mock_msg)
    assert bridge.service.values["/Ac/Power"] == 123.5

    mock_msg.payload = b"200.0"
    bridge._on_mqtt_message(None, None, mock_msg)
    assert bridge.service.values["/Ac/Power"] == 200.0

    mock_msg.topic = "sensor/temperature"
    mock_msg.payload = json.dumps({"value": 22.5}).encode()
    bridge._on_mqtt_message(None, None, mock_msg)
    assert bridge.service.values["/Temperature"] == 22.5

    # Non-finite must not replace a valid reading
    mock_msg.payload = json.dumps({"value": "nan"}).encode()
    bridge._on_mqtt_message(None, None, mock_msg)
    assert bridge.service.values["/Temperature"] == 22.5

    mock_msg.topic = "sensor/voltage"
    mock_msg.payload = json.dumps({"value": "inf"}).encode()
    bridge._on_mqtt_message(None, None, mock_msg)
    assert "/Ac/L1/Voltage" not in bridge.service.values

    mock_msg.payload = json.dumps({"value": 230.0}).encode()
    bridge._on_mqtt_message(None, None, mock_msg)
    assert bridge.service.values["/Ac/L1/Voltage"] == 230.0


@pytest.mark.parametrize(
    ("dbus_type", "default", "expected"),
    [
        ("double", float("nan"), None),
        ("double", float("inf"), None),
        ("int32", 2147483648, None),
        ("uint32", -1, None),
        ("uint16", 65536, None),
        ("double", "25.5", 25.5),
        ("int32", "7", 7),
    ],
)
@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_mapping_defaults_use_message_conversion(
    mock_mqtt_client, mock_system_bus, sample_config, dbus_type, default, expected, caplog
):
    """Defaults and template-error fallback obey the same typed value contract."""
    from pathlib import Path
    from types import SimpleNamespace

    import yaml

    config_path = Path(sample_config)
    config = yaml.safe_load(config_path.read_text())
    config["mappings"][0].update(dbus_type=dbus_type, default=default)
    config_path.write_text(yaml.safe_dump(config))
    bridge = MQTTToDBusBridge(sample_config)
    assert bridge.service.paths["/Temperature"] == dbus_type
    if expected is None:
        assert "/Temperature" not in bridge.service.values
    else:
        assert bridge.service.values["/Temperature"] == expected
        assert type(bridge.service.values["/Temperature"]) is type(expected)

    class BrokenTemplate:
        def render(self, **kwargs):
            raise ValueError("Synthetic template failure")

    bridge._templates = {"sensor/temperature": BrokenTemplate()}
    message = SimpleNamespace(topic="sensor/temperature", payload=b"{}")
    bridge._on_mqtt_message(None, None, message)
    record = next(record for record in caplog.records if "Template error" in record.message)
    assert record.exc_info is not None
    assert isinstance(record.exc_info[1], ValueError)
    assert record.exc_info[2] is not None
    if expected is None:
        assert "/Temperature" not in bridge.service.GetAll("")
    else:
        assert bridge.service.Get("", "/Temperature") == expected

    bridge._templates.clear()
    message.payload = b"1"
    bridge._on_mqtt_message(None, None, message)
    assert bridge.service.Get("", "/Temperature") == 1


@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_invalid_message_keeps_traceback_and_next_message_updates(
    mock_mqtt_client, mock_system_bus, sample_config, caplog
):
    from types import SimpleNamespace

    bridge = MQTTToDBusBridge(sample_config)
    message = SimpleNamespace(topic="sensor/temperature", payload=b"\xff")
    bridge._on_mqtt_message(None, None, message)
    record = next(record for record in caplog.records if "Error processing message" in record.message)
    assert record.exc_info is not None
    assert isinstance(record.exc_info[1], UnicodeDecodeError)
    assert record.exc_info[2] is not None
    assert "/Temperature" not in bridge.service.values

    message.payload = b'{"temperature": 25.5}'
    bridge._on_mqtt_message(None, None, message)
    assert bridge.service.Get("", "/Temperature") == 25.5


@pytest.mark.parametrize(
    ("dbus_type", "constructor", "lower", "upper"),
    [
        ("int32", "Int32", -2147483648, 2147483647),
        ("uint32", "UInt32", 0, 4294967295),
        ("uint16", "UInt16", 0, 65535),
    ],
)
@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_integer_message_bounds_preserve_readable_service_state(
    mock_mqtt_client,
    mock_system_bus,
    sample_config,
    monkeypatch,
    dbus_type,
    constructor,
    lower,
    upper,
):
    """Concrete range-checking host double models documented D-Bus integer bounds."""
    from pathlib import Path
    from types import SimpleNamespace

    import yaml

    from src import mqtt_to_dbus

    class BoundedInteger(int):
        def __new__(cls, value):
            number = int(value)
            if not lower <= number <= upper:
                raise OverflowError("D-Bus integer out of range")
            return super().__new__(cls, number)

    monkeypatch.setattr(mqtt_to_dbus.dbus, constructor, BoundedInteger)
    config_path = Path(sample_config)
    config = yaml.safe_load(config_path.read_text())
    config["mappings"][2]["dbus_type"] = dbus_type
    config_path.write_text(yaml.safe_dump(config))
    bridge = MQTTToDBusBridge(sample_config)
    signals = []
    monkeypatch.setattr(
        bridge.service,
        "PropertiesChanged",
        lambda interface, changed, invalidated: signals.append(changed),
    )
    message = SimpleNamespace(topic="sensor/power", payload=b"")
    for value in [lower, upper]:
        message.payload = str(value).encode()
        bridge._on_mqtt_message(None, None, message)
        assert bridge.service.Get("", "/Power") == value
    for value in [lower - 1, upper + 1]:
        message.payload = str(value).encode()
        bridge._on_mqtt_message(None, None, message)
        assert bridge.service.values["/Power"] == upper
        assert bridge.service.GetAll("")["/Power"] == upper
    assert signals == [{"/Power": lower}, {"/Power": upper}]


@pytest.mark.parametrize("standard_path", [True, False])
@pytest.mark.parametrize("conflicting_default", [None, 42.0])
@patch("src.mqtt_to_dbus.dbus.SystemBus")
@patch("src.mqtt_to_dbus.mqtt.Client")
def test_conflicting_mapping_types_preserve_existing_paths(
    mock_mqtt_client,
    mock_system_bus,
    sample_config,
    monkeypatch,
    standard_path,
    conflicting_default,
):
    """Rejected mappings cannot alter types, defaults, subscriptions or later messages."""
    from pathlib import Path
    from types import SimpleNamespace

    import yaml

    config_path = Path(sample_config)
    config = yaml.safe_load(config_path.read_text())
    target = "/ProductName" if standard_path else "/Reading"
    initial = "Test Bridge" if standard_path else "seed"
    mappings = (
        []
        if standard_path
        else [
            {
                "mqtt_topic": "sensor/original",
                "dbus_path": target,
                "dbus_type": "string",
                "default": initial,
            }
        ]
    )
    mappings.extend(
        [
            {"mqtt_topic": "sensor/alias", "dbus_path": target, "dbus_type": "string"},
            {
                "mqtt_topic": "sensor/conflict",
                "dbus_path": target,
                "dbus_type": "double",
                "default": conflicting_default,
            },
            {
                "mqtt_topic": "sensor/healthy",
                "dbus_path": "/Healthy",
                "dbus_type": "double",
            },
        ]
    )
    config["mappings"] = mappings
    config_path.write_text(yaml.safe_dump(config))
    bridge = MQTTToDBusBridge(sample_config)
    assert bridge.service.GetAll("")[target] == initial
    assert bridge.service.paths[target] == "string"
    assert bridge.service.Get("", target) == initial

    client = mock_mqtt_client.return_value
    bridge._on_mqtt_connect(client, None, None, 0, None)
    subscribed = {call.args[0] for call in client.subscribe.call_args_list}
    assert subscribed == {m["mqtt_topic"] for m in mappings} - {"sensor/conflict"}
    signals = []
    monkeypatch.setattr(
        bridge.service,
        "PropertiesChanged",
        lambda interface, changed, invalidated: signals.append(changed),
    )
    bridge._on_mqtt_message(
        None,
        None,
        SimpleNamespace(topic="sensor/conflict", payload=b'{"value": 99}'),
    )
    assert bridge.service.GetAll("")[target] == initial
    assert signals == []
    bridge._on_mqtt_message(
        None,
        None,
        SimpleNamespace(topic="sensor/alias", payload=b'"updated"'),
    )
    bridge._on_mqtt_message(
        None,
        None,
        SimpleNamespace(topic="sensor/healthy", payload=b"25.5"),
    )
    assert bridge.service.GetAll("")[target] == "updated"
    assert bridge.service.Get("", "/Healthy") == 25.5
    assert signals == [{target: "updated"}, {"/Healthy": 25.5}]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
