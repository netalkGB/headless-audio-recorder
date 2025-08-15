import sounddevice
import numpy
import os
import struct
from typing import List, Dict, Any, Optional


# Recording state
is_recording: bool = False
recording_data: List[numpy.ndarray] = []
recording_stream: Optional[sounddevice.InputStream] = None
sample_rate: int = 44100

# Active recording device
active_device_id: Optional[int] = None


def audio_callback(indata, frames, time, status):
    """Callback function for audio recording"""
    global recording_data
    if status:
        print(f"Audio callback status: {status}")
    recording_data.append(indata.copy())


def get_audio_devices():
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


def set_active_device(device_id: int):
    """Set the active recording device"""
    global active_device_id
    
    # Check if device exists
    devices = get_audio_devices()
    device_ids = [device['id'] for device in devices]
    
    if device_id not in device_ids:
        raise ValueError("Device ID not found")
    
    active_device_id = device_id
    return active_device_id


def get_active_device():
    """Get the current active recording device"""
    if active_device_id is None:
        return None
    
    # Get active device details
    devices = get_audio_devices()
    active_device = next((device for device in devices if device['id'] == active_device_id), None)
    
    return {
        "active_device_id": active_device_id,
        "device_info": active_device
    }


def start_recording_core():
    """Core recording start logic"""
    global is_recording, recording_data, recording_stream, active_device_id
    
    if is_recording:
        raise ValueError("Recording already in progress")
    
    if active_device_id is None:
        raise ValueError("No active device set")
    
    # Check if active device is still available
    devices = get_audio_devices()
    active_device = next((device for device in devices if device['id'] == active_device_id), None)
    
    if active_device is None:
        raise ValueError("Active device is not available")
    
    # Clear previous recording data
    recording_data = []
    
    # Create and start input stream
    recording_stream = sounddevice.InputStream(
        samplerate=sample_rate,
        channels=2,
        dtype='float32',
        device=active_device_id,
        callback=audio_callback
    )
    recording_stream.start()
    is_recording = True
    
    return {
        "device_id": active_device_id,
        "sample_rate": sample_rate,
        "channels": 2,
        "dtype": "float32"
    }


def stop_recording_core():
    """Core recording stop logic"""
    global is_recording, recording_data, recording_stream
    
    if not is_recording:
        raise ValueError("No recording in progress")
    
    if recording_stream:
        recording_stream.stop()
        recording_stream.close()
        recording_stream = None
    
    is_recording = False
    
    if recording_data:
        # Concatenate all recorded chunks
        full_recording = numpy.concatenate(recording_data, axis=0)
        recorded_samples = len(full_recording)
        recorded_duration = recorded_samples / sample_rate
        
        return {
            "recorded_samples": recorded_samples,
            "recorded_duration": recorded_duration,
            "sample_rate": sample_rate,
            "channels": 2,
            "dtype": "float32"
        }
    else:
        return {"recorded_samples": 0, "recorded_duration": 0}


def save_recording_core(file_path: str):
    """Core recording save logic"""
    global recording_data
    
    if is_recording:
        raise ValueError("Recording is still in progress. Stop recording first.")
    
    if not recording_data:
        raise ValueError("No recording data available to save")
    
    # Concatenate all recorded chunks
    full_recording = numpy.concatenate(recording_data, axis=0)
    
    # Ensure directory exists
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Save as 32-bit float WAV file with manual RIFF header
    with open(file_path, 'wb') as f:
        # WAV file parameters
        channels = 2
        sample_width = 4  # 32-bit float
        frame_rate = sample_rate
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
    recorded_duration = len(full_recording) / sample_rate
    
    return {
        "file_path": file_path,
        "file_size_bytes": file_size,
        "recorded_duration": recorded_duration,
        "sample_rate": sample_rate,
        "channels": 2,
        "format": "WAV 32-bit float"
    }


def normalize_recording_core(target_db: float = 0.0):
    """Normalize recording data to specified dB level"""
    global recording_data
    
    if is_recording:
        raise ValueError("Recording is still in progress. Stop recording first.")
    
    if not recording_data:
        raise ValueError("No recording data available to normalize")
    
    # Concatenate all recorded chunks
    full_recording = numpy.concatenate(recording_data, axis=0)
    
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
    recording_data = [normalized_recording]
    
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
        "recorded_samples": len(normalized_recording),
        "recorded_duration": len(normalized_recording) / sample_rate
    }