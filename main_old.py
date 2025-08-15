import sounddevice
import numpy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import threading
import os
import struct

app = FastAPI(title="Audio Recorder API", version="1.0.0")

# Active recording device
active_device_id: Optional[int] = None

# Recording state
is_recording: bool = False
recording_data: List[numpy.ndarray] = []
recording_stream: Optional[sounddevice.InputStream] = None
sample_rate: int = 44100

class DeviceSelection(BaseModel):
    device_id: int

class SaveRequest(BaseModel):
    file_path: str

def get_audio_devices():
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

@app.get("/api/v1/record/devices", response_model=List[Dict[str, Any]])
async def get_recording_devices():
    """Get list of available recording devices"""
    return get_audio_devices()

@app.put("/api/v1/record/devices/active")
async def set_active_device(device_selection: DeviceSelection):
    """Set the active recording device"""
    global active_device_id
    
    # Check if device exists
    devices = get_audio_devices()
    device_ids = [device['id'] for device in devices]
    
    if device_selection.device_id not in device_ids:
        raise HTTPException(status_code=404, detail="Device ID not found")
    
    active_device_id = device_selection.device_id
    return {"message": f"Active device set to ID {active_device_id}"}

@app.get("/api/v1/record/devices/active")
async def get_active_device():
    """Get the current active recording device"""
    if active_device_id is None:
        return {"active_device_id": None, "message": "No active device set"}
    
    # Get active device details
    devices = get_audio_devices()
    active_device = next((device for device in devices if device['id'] == active_device_id), None)
    
    if active_device is None:
        return {"active_device_id": active_device_id, "message": "Active device is not available"}
    
    return {"active_device_id": active_device_id, "device_info": active_device}

def audio_callback(indata, frames, time, status):
    """Callback function for audio recording"""
    global recording_data
    if status:
        print(f"Audio callback status: {status}")
    recording_data.append(indata.copy())

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

@app.post("/api/v1/record/start")
async def start_recording():
    """Start audio recording with 32-bit float, 2 channels"""
    try:
        result = start_recording_core()
        return {
            "message": "Recording started",
            **result
        }
    except ValueError as e:
        if "already in progress" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")

@app.post("/api/v1/record/stop")
async def stop_recording():
    """Stop audio recording"""
    try:
        result = stop_recording_core()
        return {
            "message": "Recording stopped",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop recording: {str(e)}")

@app.post("/api/v1/record/save")
async def save_recording(save_request: SaveRequest):
    """Save recorded audio to specified file path"""
    try:
        result = save_recording_core(save_request.file_path)
        return {
            "message": "Recording saved successfully",
            **result
        }
    except ValueError as e:
        if "still in progress" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save recording: {str(e)}")

