from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.config.server_config import ServerConfig


def test_server_config_defaults():
    cfg = ServerConfig.from_env({})
    assert (cfg.service_name, cfg.host, cfg.port) == (
        "Microphone Microservice",
        "127.0.0.1",
        8000,
    )


def test_server_config_overrides():
    cfg = ServerConfig.from_env(
        {
            "SERVICE_NAME": "X",
            "SERVICE_HOST": "0.0.0.0",
            "SERVICE_PORT": "9000",
        }
    )
    assert (cfg.service_name, cfg.host, cfg.port) == ("X", "0.0.0.0", 9000)


def test_microphone_config_defaults():
    cfg = MicrophoneConfig.from_env({})
    assert cfg == MicrophoneConfig(16000, (), True)


def test_microphone_config_parses_keywords_and_booleans():
    cfg = MicrophoneConfig.from_env(
        {
            "MICROPHONE_FALLBACK_SAMPLE_RATE": "44100",
            "MICROPHONE_TARGET_KEYWORDS": " usb , podcast ,,",
            "MICROPHONE_SHOW_METER": "false",
        }
    )
    assert cfg == MicrophoneConfig(44100, ("usb", "podcast"), False)
