from typing import Optional

import numpy as np


class AudioRecordResult:
    """
    A data class representing the result of an audio recording process.

    This class is used to encapsulate the outcome of an audio recording operation, including
    whether the recording was successful, the recorded audio data, and whether the recording
    stopped due to a silence timeout.

    Attributes:
        success (bool): Indicates whether the audio recording was successful.
        data (Optional[np.ndarray]): The recorded audio data as a NumPy array. This will be None
            if the recording was not successful or if no audio data was captured.
        silence_timeout (bool): Indicates whether the recording was stopped due to a silence
            timeout, meaning that no speech was detected for a specified duration.
    """

    def __init__(
        self,
        success: bool,
        data: Optional[np.ndarray] = None,
        silence_timeout: bool = False,
    ):
        self.success = success
        self.data = data
        self.silence_timeout = silence_timeout
