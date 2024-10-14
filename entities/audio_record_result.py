from typing import Optional
import numpy as np

class AudioRecordResult:
    def __init__(self, success: bool, data: Optional[np.ndarray] = None, silence_timeout: bool = False):
        self.success = success
        self.data = data
        self.silence_timeout = silence_timeout