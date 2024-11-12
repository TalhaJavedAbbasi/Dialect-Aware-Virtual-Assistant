const textarea = document.querySelector("textarea"),
      voiceList = document.querySelector("#voiceList"),
      speechBtn = document.querySelector("#speechButton"),
      modal = document.getElementById("myModal"),
      modalText = document.querySelector("#modalText"),
      span = document.getElementsByClassName("close")[0];

let audio = new Audio(),
    isPlaying = false,
    isPaused = false;

// Update button styles based on playback state
function updateButtonStyle() {
    if (isPlaying) {
        speechBtn.style.backgroundColor = "#d9534f"; // Red when playing
        speechBtn.innerHTML = "Pause Speech &nbsp;<i class='fa-solid fa-pause'></i>";
    } else if (isPaused) {
        speechBtn.style.backgroundColor = "#5bc0de"; // Light blue when paused
        speechBtn.innerHTML = "Resume Speech &nbsp;<i class='fa-solid fa-play'></i>";
    } else {
        speechBtn.style.backgroundColor = "#6B5B95"; // Original color
        speechBtn.innerHTML = "Convert To Speech &nbsp;<i class='fa-solid fa-headphones'></i>";
    }
}

speechBtn.addEventListener("click", (e) => {
    e.preventDefault();
    if (textarea.value.trim() === "") {
        showModal("Please enter text to convert.");
        return;
    }

    if (isPaused) {
        audio.play();
        isPlaying = true;
        isPaused = false;
        updateButtonStyle();
        return;
    }

    if (isPlaying) {
        audio.pause();
        isPlaying = false;
        isPaused = true;
        updateButtonStyle();
        return;
    }

    // Clear previous audio and reset playback state
    audio.src = "";
    audio.currentTime = 0; // Reset playback time to the beginning
    textToSpeech();
});

function textToSpeech() {
    const text = textarea.value;
    const selectedVoice = voiceList.value;

    fetch("/synthesize", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: text, voice: selectedVoice })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showModal(data.error);
        } else {
            const audioUrl = `${data.audio_url}?t=${new Date().getTime()}`;
            audio.src = audioUrl;
            audio.play();
            isPlaying = true;
            isPaused = false;
            updateButtonStyle();
        }
    })
    .catch(error => {
        console.error("Error:", error);
        showModal("Failed to generate audio. Please try again.");
    });
}

audio.addEventListener("ended", () => {
    isPlaying = false;
    isPaused = false;
    updateButtonStyle();
});

function showModal(message) {
    modalText.innerHTML = message;
    modal.style.display = "block";
}

// Modal close functionality
span.onclick = function() {
    modal.style.display = "none";
};
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
};

// Update initial button style
updateButtonStyle();


// Select the wave container element
const waveContainer = document.getElementById('wave-container');

// Define the number of wave bars (adjust as needed)
const numberOfBars = 50;

// Create and add wave bars to the container
for (let i = 1; i <= numberOfBars; i++) {
    const bar = document.createElement('div');
    bar.classList.add('wave-bar');
    bar.style.setProperty('--i', i); // Set the custom property for staggered delay

    // Add random height for initial animation state
    bar.style.height = `${15 + Math.random() * 45}px`; // Random height between 15 and 60px
    bar.style.animationDuration = `${1 + Math.random()}s`; // Random animation duration
    waveContainer.appendChild(bar);
}

