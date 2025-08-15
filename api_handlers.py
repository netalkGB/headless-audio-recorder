from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import audio_recorder


class DeviceSelection(BaseModel):
    device_id: int


class SaveRequest(BaseModel):
    file_path: str


async def get_recording_devices():
    """Get list of available recording devices"""
    return audio_recorder.get_audio_devices()


async def set_active_device(device_selection: DeviceSelection):
    """Set the active recording device"""
    try:
        device_id = audio_recorder.set_active_device(device_selection.device_id)
        return {"message": f"Active device set to ID {device_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set active device: {str(e)}")


async def get_active_device():
    """Get the current active recording device"""
    result = audio_recorder.get_active_device()
    if result is None:
        return {"active_device_id": None, "message": "No active device set"}
    
    if result["device_info"] is None:
        return {"active_device_id": result["active_device_id"], "message": "Active device is not available"}
    
    return result


async def start_recording():
    """Start audio recording with 32-bit float, 2 channels"""
    try:
        result = audio_recorder.start_recording_core()
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


async def stop_recording():
    """Stop audio recording"""
    try:
        result = audio_recorder.stop_recording_core()
        return {
            "message": "Recording stopped",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop recording: {str(e)}")


async def save_recording(save_request: SaveRequest):
    """Save recorded audio to specified file path"""
    try:
        result = audio_recorder.save_recording_core(save_request.file_path)
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