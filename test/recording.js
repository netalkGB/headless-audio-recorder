function testFetchAudioDevices() {
    fetch('http://localhost:8000/api/v1/record/devices')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Devices:', data);
    })
    .catch(error => {
        console.error('Error fetching devices:', error);
    });
}

function testSetActiveDevice(deviceId) {
    fetch('http://localhost:8000/api/v1/record/devices/active', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ device_id: deviceId })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Set active device response:', data);
    })
    .catch(error => {
        console.error('Error setting active device:', error);
    });
}

function testGetActiveDevice() {
    fetch('http://localhost:8000/api/v1/record/devices/active')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Active device:', data);
    })
    .catch(error => {
        console.error('Error fetching active device:', error);
    });
}

function testStartRecording() {
    fetch('http://localhost:8000/api/v1/record/start', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Start recording response:', data);
    })
    .catch(error => {
        console.error('Error starting recording:', error);
    });
}

function testStopRecording() {
    fetch('http://localhost:8000/api/v1/record/stop', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Stop recording response:', data);
    })
    .catch(error => {
        console.error('Error stopping recording:', error);
    });
}

function testSaveRecording(filePath) {
    fetch('http://localhost:8000/api/v1/record/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: filePath })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Save recording response:', data);
    })
    .catch(error => {
        console.error('Error saving recording:', error);
    });
}

function testNormalizeRecording(targetDb = 0.0) {
    fetch('http://localhost:8000/api/v1/record/normalize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ target_db: targetDb })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Normalize recording response:', data);
    })
    .catch(error => {
        console.error('Error normalizing recording:', error);
    });
}