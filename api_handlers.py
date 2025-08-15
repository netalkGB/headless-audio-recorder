from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from audio_recorder import audio_recorder


class DeviceSelection(BaseModel):
    device_id: int


class SaveRequest(BaseModel):
    file_path: str


class NormalizeRequest(BaseModel):
    target_db: float = 0.0


class TrimSilenceRequest(BaseModel):
    margin_seconds: float = 0.1


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


async def normalize_recording(normalize_request: NormalizeRequest):
    """Normalize recorded audio to specified dB level"""
    try:
        result = audio_recorder.normalize_recording_core(normalize_request.target_db)
        return result
    except ValueError as e:
        if "still in progress" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to normalize recording: {str(e)}")


async def learn_noise_floor():
    """Learn noise floor by recording 5 seconds of silence"""
    try:
        result = audio_recorder.learn_noise_floor_core()
        return result
    except ValueError as e:
        if "already in progress" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to learn noise floor: {str(e)}")


async def trim_silence(trim_request: TrimSilenceRequest):
    """Trim silence from beginning and end of recording"""
    try:
        result = audio_recorder.trim_silence_core(trim_request.margin_seconds)
        return result
    except ValueError as e:
        if "still in progress" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trim silence: {str(e)}")