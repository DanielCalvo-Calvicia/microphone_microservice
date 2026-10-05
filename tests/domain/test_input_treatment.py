import pytest

from domain.errors import InvalidInputTreatment
from domain.value_objects.input_treatment import InputTreatment


def test_the_defaults_are_the_cutting_the_openai_engine_of_stt_used_to_do():
    treatment = InputTreatment()

    assert (treatment.silence_threshold, treatment.silence_limit_seconds, treatment.speech_start_factor) == (150, 2.0, 2.0)
    assert (treatment.volume_smoothing, treatment.noise_floor_tracking) == (True, True)
    assert (treatment.dc_offset_removal, treatment.resample_to_hz) == (False, 0)


@pytest.mark.parametrize(
    "bad",
    [
        {"silence_threshold": -1},
        {"silence_limit_seconds": 0},
        {"silence_limit_seconds": -1.0},
        {"speech_start_factor": 0.5},
        {"volume_smoothing_factor": 0},
        {"volume_smoothing_factor": 1.5},
        {"resample_to_hz": -16000},
    ],
)
def test_out_of_range_settings_are_refused(bad):
    with pytest.raises(InvalidInputTreatment):
        InputTreatment(**bad)
