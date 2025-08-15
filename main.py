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

# Audio editing endpoints
@app.post("/api/v1/record/edit/normalize")
async def normalize_recording(normalize_request: api_handlers.NormalizeRequest):
    """Normalize recorded audio to specified dB level"""
    return await api_handlers.normalize_recording(normalize_request)

@app.post("/api/v1/record/edit/trim-silence/learn")
async def learn_noise_floor():
    """Learn noise floor by recording 5 seconds of silence"""
    return await api_handlers.learn_noise_floor()

@app.post("/api/v1/record/edit/trim-silence")
async def trim_silence(trim_request: api_handlers.TrimSilenceRequest):
    """Trim silence from beginning and end of recording"""
    return await api_handlers.trim_silence(trim_request)

# Audio analysis endpoints
@app.get("/api/v1/record/analyze/clipping")
async def analyze_clipping():
    """Check if recording has clipping (peaks at 0dB)"""
    return await api_handlers.analyze_clipping()


def main():
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser(description="Audio Recorder API server.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()