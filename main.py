from fastapi import FastAPI
from typing import List, Dict, Any
import api_handlers

app = FastAPI(title="Audio Recorder API", version="1.0.0")

# Device management endpoints
@app.get("/api/v1/record/devices", response_model=List[Dict[str, Any]])
async def get_recording_devices():
    """Get list of available recording devices"""
    return await api_handlers.get_recording_devices()

@app.put("/api/v1/record/devices/active")
async def set_active_device(device_selection: api_handlers.DeviceSelection):
    """Set the active recording device"""
    return await api_handlers.set_active_device(device_selection)

@app.get("/api/v1/record/devices/active")
async def get_active_device():
    """Get the current active recording device"""
    return await api_handlers.get_active_device()

# Recording control endpoints
@app.post("/api/v1/record/start")
async def start_recording():
    """Start audio recording with 32-bit float, 2 channels"""
    return await api_handlers.start_recording()

@app.post("/api/v1/record/stop")
async def stop_recording():
    """Stop audio recording"""
    return await api_handlers.stop_recording()

@app.post("/api/v1/record/save")
async def save_recording(save_request: api_handlers.SaveRequest):
    """Save recorded audio to specified file path"""
    return await api_handlers.save_recording(save_request)


def main():
    print("Audio Recorder API Server")
    print("Use: uvicorn main:app --reload")


if __name__ == "__main__":
    main()