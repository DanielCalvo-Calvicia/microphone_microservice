from domain.value_objects.input_treatment import InputTreatment
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
    assert cfg == MicrophoneConfig(16000, (), True, InputTreatment())


def test_microphone_config_parses_keywords_and_booleans():
    cfg = MicrophoneConfig.from_env(
        {
            "MICROPHONE_FALLBACK_SAMPLE_RATE": "44100",
            "MICROPHONE_TARGET_KEYWORDS": " usb , podcast ,,",
            "MICROPHONE_SHOW_METER": "false",
        }
    )
    assert cfg == MicrophoneConfig(44100, ("usb", "podcast"), False, InputTreatment())


def test_every_treatment_of_the_input_comes_from_its_own_environment_variable():
    cfg = MicrophoneConfig.from_env(
        {
            "MICROPHONE_SILENCE_THRESHOLD": "300",
            "MICROPHONE_SILENCE_LIMIT_SECONDS": "1.5",
            "MICROPHONE_SPEECH_START_FACTOR": "3",
            "MICROPHONE_DC_OFFSET_REMOVAL": "true",
            "MICROPHONE_VOLUME_SMOOTHING": "false",
            "MICROPHONE_VOLUME_SMOOTHING_FACTOR": "0.25",
            "MICROPHONE_NOISE_FLOOR_TRACKING": "0",
            "MICROPHONE_RESAMPLE_TO_HZ": "16000",
        }
    )

    assert cfg.treatment == InputTreatment(
        silence_threshold=300,
        silence_limit_seconds=1.5,
        speech_start_factor=3.0,
        dc_offset_removal=True,
        volume_smoothing=False,
        volume_smoothing_factor=0.25,
        noise_floor_tracking=False,
        resample_to_hz=16000,
    )


def test_a_blank_treatment_variable_means_its_default():
    cfg = MicrophoneConfig.from_env({"MICROPHONE_VOLUME_SMOOTHING": " ", "MICROPHONE_SILENCE_THRESHOLD": ""})

    assert cfg.treatment == InputTreatment()


def test_an_out_of_range_treatment_is_refused_at_startup():
    import pytest

    from domain.errors import InvalidInputTreatment

    with pytest.raises(InvalidInputTreatment):
        MicrophoneConfig.from_env({"MICROPHONE_SILENCE_LIMIT_SECONDS": "0"})
