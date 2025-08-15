# Audio Recorder API

A FastAPI-based audio recording and processing server with device management, audio editing, and analysis capabilities.

## Features

- Device management (list/set active recording devices)
- Audio recording with 32-bit float, 2-channel support
- Audio editing (normalization, silence trimming)
- Audio analysis (clipping detection)

## Build

To build the application as a standalone executable:

```bash
uv run python -m nuitka main.py --onefile --output-filename=audio-recorder.exe --enable-plugin=anti-bloat --enable-plugin=numpy --assume-yes-for-downloads --windows-console-mode=force --remove-output
```

## Development

Install dependencies:
```bash
uv install
```

Run the development server:
```bash
uv run python main.py
```