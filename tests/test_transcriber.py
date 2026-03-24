"""Tests for transcriber module."""

from unittest.mock import MagicMock, patch

import numpy as np

from lerolero.transcriber import _VAD_FRAME_SAMPLES, Transcriber


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcriber_initialization_cpu(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,
    mock_pipeline: MagicMock,
) -> None:
    transcriber = Transcriber(device="cpu", compute_type="int8")

    assert transcriber.device == "CPU"
    assert transcriber.compute_type == "int8"
    mock_ov_model.from_pretrained.assert_called_once()
    mock_pipeline.assert_called_once()


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcriber_initialization_cuda_auto(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,  # noqa: ARG001
) -> None:
    transcriber = Transcriber(device="cuda", compute_type="auto")

    assert transcriber.device == "GPU"
    assert transcriber.compute_type == "float16"


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcriber_initialization_gpu_device(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,  # noqa: ARG001
) -> None:
    transcriber = Transcriber(device="GPU", compute_type="auto")

    assert transcriber.device == "GPU"
    assert transcriber.compute_type == "float16"


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcriber_cpu_auto_compute(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,  # noqa: ARG001
) -> None:
    transcriber = Transcriber(device="cpu", compute_type="auto")

    assert transcriber.device == "CPU"
    assert transcriber.compute_type == "int8"


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcribe_success_dict(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,
) -> None:
    mock_pipe_instance = MagicMock(return_value={"text": "Hello world"})
    mock_pipeline.return_value = mock_pipe_instance

    transcriber = Transcriber(language="en")

    # Build audio with a clear speech-like burst to pass VAD
    audio = _build_speech_audio()
    result = transcriber.transcribe(audio)

    assert result == "Hello world"
    mock_pipe_instance.assert_called_once()
    _, kwargs = mock_pipe_instance.call_args
    assert kwargs["generate_kwargs"]["language"] == "en"


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcribe_no_language(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,
) -> None:
    mock_pipe_instance = MagicMock(return_value={"text": "Test"})
    mock_pipeline.return_value = mock_pipe_instance

    transcriber = Transcriber()
    audio = _build_speech_audio()
    result = transcriber.transcribe(audio)

    assert result == "Test"
    _, kwargs = mock_pipe_instance.call_args
    assert kwargs["generate_kwargs"] == {}


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcribe_english_only_model_skips_language(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,
) -> None:
    mock_pipe_instance = MagicMock(return_value={"text": "Test"})
    mock_pipeline.return_value = mock_pipe_instance

    transcriber = Transcriber(
        model_id="openai/whisper-base.en", language="en"
    )
    audio = _build_speech_audio()
    result = transcriber.transcribe(audio)

    assert result == "Test"
    _, kwargs = mock_pipe_instance.call_args
    assert kwargs["generate_kwargs"] == {}


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcribe_multiple_segments(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,
) -> None:
    mock_pipe_instance = MagicMock(
        return_value=[{"text": "Hello"}, {"text": "world"}]
    )
    mock_pipeline.return_value = mock_pipe_instance

    transcriber = Transcriber()
    result = transcriber.transcribe("path/to/audio.wav")

    assert result == "Hello world"


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcribe_empty_list(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,
) -> None:
    mock_pipe_instance = MagicMock(return_value=[])
    mock_pipeline.return_value = mock_pipe_instance

    transcriber = Transcriber()
    result = transcriber.transcribe("path/to/audio.wav")
    assert result == ""


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcribe_unexpected_return_type(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,
) -> None:
    mock_pipe_instance = MagicMock(return_value="Not a dict or list")
    mock_pipeline.return_value = mock_pipe_instance

    transcriber = Transcriber()
    assert transcriber.transcribe("audio.wav") == ""


# --- VAD unit tests (pure numpy, no mocks needed) ---


def test_has_speech_silence() -> None:
    """Pure silence (zeros) should be rejected by the energy VAD."""
    silence = np.zeros(16000, dtype=np.float32)
    assert Transcriber._has_speech(silence) is False  # noqa: SLF001


def test_has_speech_with_burst() -> None:
    """Audio with a loud burst should be detected as speech."""
    audio = _build_speech_audio()
    assert Transcriber._has_speech(audio) is True  # noqa: SLF001


def test_has_speech_too_short() -> None:
    """Audio shorter than one frame should return False."""
    short = np.zeros(_VAD_FRAME_SAMPLES - 1, dtype=np.float32)
    assert Transcriber._has_speech(short) is False  # noqa: SLF001


def test_has_speech_multidim() -> None:
    """Multi-dimensional arrays should be flattened and work."""
    audio = _build_speech_audio().reshape(1, -1)
    assert Transcriber._has_speech(audio) is True  # noqa: SLF001


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcribe_vad_rejects_silence(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,
) -> None:
    """The transcribe method should return '' for silent numpy input."""
    mock_pipeline.return_value = MagicMock()

    transcriber = Transcriber()
    result = transcriber.transcribe(np.zeros(16000, dtype=np.float32))

    assert result == ""
    transcriber.pipe.assert_not_called()


@patch("lerolero.transcriber.pipeline")
@patch("lerolero.transcriber.OVModelForSpeechSeq2Seq")
@patch("lerolero.transcriber.AutoProcessor")
def test_transcribe_vad_passes_speech(
    mock_auto_processor: MagicMock,  # noqa: ARG001
    mock_ov_model: MagicMock,  # noqa: ARG001
    mock_pipeline: MagicMock,
) -> None:
    """The transcribe method should invoke the pipeline for speech audio."""
    mock_pipe_instance = MagicMock(return_value={"text": "Speech detected"})
    mock_pipeline.return_value = mock_pipe_instance

    transcriber = Transcriber()
    audio = _build_speech_audio()
    result = transcriber.transcribe(audio)

    assert result == "Speech detected"
    mock_pipe_instance.assert_called_once()


# --- Helper ---


def _build_speech_audio(
    duration_s: float = 1.0,
    sample_rate: int = 16000,
) -> np.ndarray:
    """Build a synthetic audio array with silence + a speech-like burst."""
    n_samples = int(duration_s * sample_rate)
    audio = np.zeros(n_samples, dtype=np.float32)
    # Insert a loud burst in the middle to simulate speech energy
    burst_start = n_samples // 4
    burst_end = 3 * n_samples // 4
    rng = np.random.default_rng(42)
    audio[burst_start:burst_end] = rng.standard_normal(
        burst_end - burst_start
    ).astype(np.float32) * 0.5
    return audio
