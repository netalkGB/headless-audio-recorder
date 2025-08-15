import sounddevice
import numpy
import os
import struct
from typing import List, Dict, Any, Optional


class AudioRecordingState:
    """State management for audio recording"""
    
    def __init__(self, sample_rate: int = 44100):
        # Recording state
        self.is_recording: bool = False
        self.recording_data: List[numpy.ndarray] = []
        self.recording_stream: Optional[sounddevice.InputStream] = None
        self.sample_rate: int = sample_rate
        
        # Active recording device
        self.active_device_id: Optional[int] = None
        
        # Noise floor for silence detection
        self.noise_floor: Optional[float] = None


class AudioRecorder:
    """Audio recording and processing class"""
    
    def __init__(self, state: AudioRecordingState):
        self.state = state

    def audio_callback(self, indata, frames, time, status):
        """Callback function for audio recording"""
        if status:
            print(f"Audio callback status: {status}")
        self.state.recording_data.append(indata.copy())

    def get_audio_devices(self):
        """Get list of available audio input devices"""
        devices = sounddevice.query_devices()
        hostapis = sounddevice.query_hostapis()
        device_list = []
        
        for i, device in enumerate(devices):
            # Only include input devices (recording capable)
            if device['max_input_channels'] > 0:
                hostapi_info = hostapis[device['hostapi']]
                device_info = {
                    "id": i,
                    "name": device['name'],
                    "hostapi": device['hostapi'],
                    "hostapi_name": hostapi_info['name'],
                    "max_input_channels": device['max_input_channels'],
                    "max_output_channels": device['max_output_channels'],
                    "default_samplerate": device['default_samplerate'],
                    "default_low_input_latency": device['default_low_input_latency'],
                    "default_high_input_latency": device['default_high_input_latency']
                }
                device_list.append(device_info)
        
        return device_list

    def set_active_device(self, device_id: int):
        """Set the active recording device"""
        # Check if device exists
        devices = self.get_audio_devices()
        device_ids = [device['id'] for device in devices]
        
        if device_id not in device_ids:
            raise ValueError("Device ID not found")
        
        self.state.active_device_id = device_id
        return self.state.active_device_id

    def get_active_device(self):
        """Get the current active recording device"""
        if self.state.active_device_id is None:
            return None
        
        # Get active device details
        devices = self.get_audio_devices()
        active_device = next((device for device in devices if device['id'] == self.state.active_device_id), None)
        
        return {
            "active_device_id": self.state.active_device_id,
            "device_info": active_device
        }

    def start_recording_core(self):
        """Core recording start logic"""
        if self.state.is_recording:
            raise ValueError("Recording already in progress")
        
        if self.state.active_device_id is None:
            raise ValueError("No active device set")
        
        # Check if active device is still available
        devices = self.get_audio_devices()
        active_device = next((device for device in devices if device['id'] == self.state.active_device_id), None)
        
        if active_device is None:
            raise ValueError("Active device is not available")
        
        # Clear previous recording data
        self.state.recording_data = []
        
        # Create and start input stream
        self.state.recording_stream = sounddevice.InputStream(
            samplerate=self.state.sample_rate,
            channels=2,
            dtype='float32',
            device=self.state.active_device_id,
            callback=self.audio_callback
        )
        self.state.recording_stream.start()
        self.state.is_recording = True
        
        return {
            "device_id": self.state.active_device_id,
            "sample_rate": self.state.sample_rate,
            "channels": 2,
            "dtype": "float32"
        }

    def stop_recording_core(self):
        """Core recording stop logic"""
        if not self.state.is_recording:
            raise ValueError("No recording in progress")
        
        if self.state.recording_stream:
            self.state.recording_stream.stop()
            self.state.recording_stream.close()
            self.state.recording_stream = None
        
        self.state.is_recording = False
        
        if self.state.recording_data:
            # Concatenate all recorded chunks
            full_recording = numpy.concatenate(self.state.recording_data, axis=0)
            recorded_samples = len(full_recording)
            recorded_duration = recorded_samples / self.state.sample_rate
            
            return {
                "recorded_samples": int(recorded_samples),
                "recorded_duration": float(recorded_duration),
                "sample_rate": self.state.sample_rate,
                "channels": 2,
                "dtype": "float32"
            }
        else:
            return {"recorded_samples": 0, "recorded_duration": 0.0}

    def save_recording_core(self, file_path: str):
        """Core recording save logic"""
        if self.state.is_recording:
            raise ValueError("Recording is still in progress. Stop recording first.")
        
        if not self.state.recording_data:
            raise ValueError("No recording data available to save")
        
        # Concatenate all recorded chunks
        full_recording = numpy.concatenate(self.state.recording_data, axis=0)
        
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Save as 32-bit float WAV file with manual RIFF header
        with open(file_path, 'wb') as f:
            # WAV file parameters
            channels = 2
            sample_width = 4  # 32-bit float
            frame_rate = self.state.sample_rate
            num_frames = len(full_recording)
            
            # Calculate file sizes
            data_size = num_frames * channels * sample_width
            file_size = 36 + data_size
            
            # Write RIFF header
            f.write(b'RIFF')
            f.write(struct.pack('<L', file_size))
            f.write(b'WAVE')
            
            # Write fmt chunk
            f.write(b'fmt ')
            f.write(struct.pack('<L', 16))  # chunk size
            f.write(struct.pack('<H', 3))   # IEEE float format
            f.write(struct.pack('<H', channels))
            f.write(struct.pack('<L', frame_rate))
            f.write(struct.pack('<L', frame_rate * channels * sample_width))  # byte rate
            f.write(struct.pack('<H', channels * sample_width))  # block align
            f.write(struct.pack('<H', sample_width * 8))  # bits per sample
            
            # Write data chunk
            f.write(b'data')
            f.write(struct.pack('<L', data_size))
            f.write(full_recording.tobytes())
        
        file_size = os.path.getsize(file_path)
        recorded_duration = len(full_recording) / self.state.sample_rate
        
        return {
            "file_path": file_path,
            "file_size_bytes": int(file_size),
            "recorded_duration": float(recorded_duration),
            "sample_rate": int(self.state.sample_rate),
            "channels": 2,
            "format": "WAV 32-bit float"
        }

    def normalize_recording_core(self, target_db: float = 0.0):
        """Normalize recording data to specified dB level"""
        if self.state.is_recording:
            raise ValueError("Recording is still in progress. Stop recording first.")
        
        if not self.state.recording_data:
            raise ValueError("No recording data available to normalize")
        
        # Concatenate all recorded chunks
        full_recording = numpy.concatenate(self.state.recording_data, axis=0)
        
        # Find the maximum absolute value across all channels
        max_amplitude = numpy.max(numpy.abs(full_recording))
        
        if max_amplitude == 0:
            raise ValueError("Recording contains only silence, cannot normalize")
        
        # Convert target dB to linear amplitude
        # 0 dB = 1.0, -6 dB = 0.5, -12 dB = 0.25, etc.
        target_amplitude = 10.0 ** (target_db / 20.0)
        
        # Calculate normalization factor
        normalization_factor = target_amplitude / max_amplitude
        
        # Apply normalization
        normalized_recording = full_recording * normalization_factor
        
        # Replace recording data with normalized version
        self.state.recording_data = [normalized_recording]
        
        # Calculate original peak in dB
        original_peak_db = 20.0 * numpy.log10(max_amplitude) if max_amplitude > 0 else -numpy.inf
        new_peak = numpy.max(numpy.abs(normalized_recording))
        new_peak_db = 20.0 * numpy.log10(new_peak) if new_peak > 0 else -numpy.inf
        
        return {
            "message": "Recording normalized",
            "target_db": target_db,
            "original_peak": float(max_amplitude),
            "original_peak_db": float(original_peak_db),
            "normalization_factor": float(normalization_factor),
            "new_peak": float(new_peak),
            "new_peak_db": float(new_peak_db),
            "recorded_samples": int(len(normalized_recording)),
            "recorded_duration": float(len(normalized_recording) / self.state.sample_rate)
        }

    def learn_noise_floor_core(self):
        """Learn noise floor by recording 5 seconds of silence"""
        if self.state.is_recording:
            raise ValueError("Recording already in progress")
        
        if self.state.active_device_id is None:
            raise ValueError("No active device set")
        
        # Check if active device is still available
        devices = self.get_audio_devices()
        active_device = next((device for device in devices if device['id'] == self.state.active_device_id), None)
        
        if active_device is None:
            raise ValueError("Active device is not available")
        
        # Record 5 seconds of silence
        silence_duration = 5.0
        silence_data = sounddevice.rec(
            int(silence_duration * self.state.sample_rate),
            samplerate=self.state.sample_rate,
            channels=2,
            dtype='float32',
            device=self.state.active_device_id
        )
        sounddevice.wait()
        
        # Calculate RMS noise floor
        rms_noise = numpy.sqrt(numpy.mean(silence_data ** 2))
        self.state.noise_floor = rms_noise * 2.0  # Add some margin for detection
        
        return {
            "message": "Noise floor learned",
            "noise_floor_rms": float(rms_noise),
            "noise_floor_threshold": float(self.state.noise_floor),
            "recorded_duration": float(silence_duration),
            "sample_rate": int(self.state.sample_rate)
        }

    def trim_silence_core(self, margin_seconds: float = 0.1):
        """Trim silence from beginning and end of recording"""
        if self.state.is_recording:
            raise ValueError("Recording is still in progress. Stop recording first.")
        
        if not self.state.recording_data:
            raise ValueError("No recording data available to trim")
        
        if self.state.noise_floor is None:
            raise ValueError("Noise floor not learned. Use learn_noise_floor endpoint first.")
        
        # Concatenate all recorded chunks
        full_recording = numpy.concatenate(self.state.recording_data, axis=0)
        
        # Calculate RMS in small windows
        window_size = int(0.01 * self.state.sample_rate)  # 10ms windows
        num_windows = len(full_recording) // window_size
        
        rms_values = []
        for i in range(num_windows):
            start = i * window_size
            end = start + window_size
            window_data = full_recording[start:end]
            rms = numpy.sqrt(numpy.mean(window_data ** 2))
            rms_values.append(rms)
        
        rms_values = numpy.array(rms_values)
        
        # Find first and last non-silent windows
        non_silent = rms_values > self.state.noise_floor
        
        if not numpy.any(non_silent):
            raise ValueError("Entire recording is below noise floor")
        
        first_sound = numpy.argmax(non_silent)
        last_sound = len(non_silent) - 1 - numpy.argmax(non_silent[::-1])
        
        # Convert to sample indices
        start_sample = max(0, first_sound * window_size - int(margin_seconds * self.state.sample_rate))
        end_sample = min(len(full_recording), (last_sound + 1) * window_size + int(margin_seconds * self.state.sample_rate))
        
        # Trim the recording
        trimmed_recording = full_recording[start_sample:end_sample]
        
        # Replace recording data with trimmed version
        self.state.recording_data = [trimmed_recording]
        
        original_duration = len(full_recording) / self.state.sample_rate
        trimmed_duration = len(trimmed_recording) / self.state.sample_rate
        trimmed_start_time = start_sample / self.state.sample_rate
        trimmed_end_time = end_sample / self.state.sample_rate
        
        return {
            "message": "Silence trimmed",
            "original_duration": float(original_duration),
            "trimmed_duration": float(trimmed_duration),
            "trimmed_start_time": float(trimmed_start_time),
            "trimmed_end_time": float(trimmed_end_time),
            "margin_seconds": float(margin_seconds),
            "noise_floor_threshold": float(self.state.noise_floor),
            "samples_removed_start": int(start_sample),
            "samples_removed_end": int(len(full_recording) - end_sample)
        }

    def analyze_clipping_core(self):
        """Check if recording has clipping (peaks at 0dB)"""
        if self.state.is_recording:
            raise ValueError("Recording is still in progress. Stop recording first.")
        
        if not self.state.recording_data:
            raise ValueError("No recording data available to analyze")
        
        # Concatenate all recorded chunks
        full_recording = numpy.concatenate(self.state.recording_data, axis=0)
        
        # Check for clipping (values at or very close to 1.0/-1.0)
        clipping_threshold = 0.99
        has_clipping = numpy.any(numpy.abs(full_recording) >= clipping_threshold)
        
        return {"has_clipping": bool(has_clipping)}


# Create instances with dependency injection
audio_recording_state = AudioRecordingState()
audio_recorder = AudioRecorder(audio_recording_state)