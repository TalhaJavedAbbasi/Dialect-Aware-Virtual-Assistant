let mediaRecorder;
let audioChunks = [];

// Feedback Section Element
const feedback = document.getElementById('feedback');
const feedbackMessages = document.getElementById('feedback-messages');
const accentSelect = document.getElementById("accent-select");
const approachSelect = document.getElementById("approach-select");

function addFeedback(message, type = 'info', retryCallback = null) {
    const toastBody = document.getElementById('toast-body');
    const toastHeader = document.querySelector('.toast-header');
    const toast = document.getElementById('toast');

    // Set toast type and add icon
    const icon = document.createElement('span');
    icon.classList.add('toast-icon');
    switch (type) {
        case 'success':
            toast.classList.add('bg-success');
            icon.innerHTML = '✔️';
            break;
        case 'danger':
            toast.classList.add('bg-danger');
            icon.innerHTML = '❌';
            break;
        case 'warning':
            toast.classList.add('bg-warning');
            icon.innerHTML = '⚠️';
            break;
        default:
            toast.classList.add('bg-info');
            icon.innerHTML = 'ℹ️';
    }

    // Clear previous content and set new content
    toastHeader.innerHTML = '';
    toastHeader.appendChild(icon);
    toastHeader.insertAdjacentHTML('beforeend', `<strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>`);
    toastBody.innerHTML = message;

    if (retryCallback) {
        const retryButton = document.createElement('button');
        retryButton.classList.add('btn', 'btn-secondary', 'ms-3');
        retryButton.innerText = 'Retry';
        retryButton.onclick = retryCallback;
        toastBody.appendChild(retryButton);
    }

    const toastInstance = new bootstrap.Toast(toast);
    toastInstance.show();
}





// Button Elements
const startBtn = document.getElementById('start-btn');
const pauseBtn = document.getElementById('pause-btn');
const resumeBtn = document.getElementById('resume-btn');
const stopBtn = document.getElementById('stop-btn');
const uploadBtn = document.getElementById('upload-btn');
const fileInput = document.getElementById('file-input'); // New input for file upload

let isTranscribing = false; // Track transcription status

function setTranscribingState(isTranscribing) {
    // Disable buttons when transcribing, enable when not
    startBtn.disabled = isTranscribing;
    pauseBtn.disabled = isTranscribing || !mediaRecorder || mediaRecorder.state === "inactive";
    resumeBtn.disabled = isTranscribing || !mediaRecorder || mediaRecorder.state === "inactive";
    stopBtn.disabled = isTranscribing || !mediaRecorder || mediaRecorder.state === "inactive";
    uploadBtn.disabled = isTranscribing;
    fileInput.disabled = isTranscribing;
}

startBtn.addEventListener("click", async function() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();
        addFeedback('Recording started...', 'success');

        // Enable only Pause and Stop buttons for recording session
        startBtn.disabled = true;
        pauseBtn.disabled = false;
        stopBtn.disabled = false;

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            setTranscribingState(true);  // Set transcribing state now
            showLoadingSpinner();  // Show spinner when processing starts
document.getElementById('transcription').innerText = '';
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio_data', audioBlob, 'audio.wav');
            formData.append("accent", accentSelect.value);
            formData.append("approach", approachSelect.value);
            document.getElementById('transcription').innerText = '';


            try {
                const response = await fetch('/stt/transcribe_audio', { method: 'POST', body: formData });
                const data = await response.json();


                if (data.transcription) {
                    document.getElementById('transcription').innerText = data.transcription;
                    addFeedback('Transcription successful.', 'info');
                } else {
                    addFeedback('Transcription failed.', 'danger');
                }
            } catch (error) {
                addFeedback('Error occurred: ' + error.message, 'danger', () => mediaRecorder.onstop());
            }
            setTranscribingState(false);
            hideLoadingSpinner();
        };
    } catch (error) {
        addFeedback('Error starting recording: ' + error.message, 'danger');
        setTranscribingState(false);
        hideLoadingSpinner();
    }
});



pauseBtn.addEventListener("click", function() {
    mediaRecorder.pause();
    addFeedback('Recording paused...', 'warning'); // Changed to addFeedback

    // Enable resume button, disable pause
    resumeBtn.disabled = false;
    pauseBtn.disabled = true;
});

resumeBtn.addEventListener("click", function() {
    mediaRecorder.resume();
    addFeedback('Recording resumed...', 'success'); // Changed to addFeedback

    // Enable pause button again, disable resume
    pauseBtn.disabled = false;
    resumeBtn.disabled = true;
});

stopBtn.addEventListener("click", function() {
    mediaRecorder.stop();
    addFeedback('Recording stopped. Uploading...', 'danger'); // Changed to addFeedback

    // Disable all buttons except Start after stopping recording
    pauseBtn.disabled = true;
    resumeBtn.disabled = true;
    stopBtn.disabled = true;
    startBtn.disabled = false;
});

uploadBtn.addEventListener("click", async function(event) {
    event.preventDefault();
    const file = fileInput.files[0];
    if (!file) {
        addFeedback('Please select an audio file to upload.', 'danger');
        return;
    }

    addFeedback('Audio file is uploaded for transcription.', 'success');
    const formData = new FormData();
    formData.append('audio_data', file);
    formData.append("accent", accentSelect.value);
    formData.append("approach", approachSelect.value);


    try {
        setTranscribingState(true);
        showLoadingSpinner();
document.getElementById('transcription').innerText = '';
        const response = await fetch('/stt/transcribe_audio', { method: 'POST', body: formData });
        const data = await response.json();
        if (data.transcription) {
            document.getElementById('transcription').innerText = data.transcription;
            addFeedback('Transcription successful for uploaded audio.', 'success');
        } else {
            addFeedback('Transcription failed for uploaded audio.', 'danger');
        }
    } catch (error) {
        addFeedback('Error occurred: ' + error.message, 'danger', () => uploadBtn.click());
    }
    setTranscribingState(false);
    hideLoadingSpinner();
});

function copyToClipboard() {
    const transcriptionText = document.getElementById('transcription').innerText;

    if (!transcriptionText || transcriptionText === "Your speech transcription will appear here.") {
        addFeedback("No text to copy.", "warning");
        return;
    }

    navigator.clipboard.writeText(transcriptionText)
        .then(() => addFeedback("Text copied to clipboard!", "success"))
        .catch(err => addFeedback("Failed to copy text: " + err, "danger"));
}


function showLoadingSpinner() {
    document.getElementById("loading-spinner").classList.remove("d-none");
}

function hideLoadingSpinner() {
    document.getElementById("loading-spinner").classList.add("d-none");
}
