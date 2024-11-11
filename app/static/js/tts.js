const textarea = document.querySelector("textarea"),
      voiceList = document.querySelector("#voiceList"),
      speechBtn = document.querySelector("#speechButton"),
      modal = document.getElementById("myModal"),
      modalText = document.querySelector("#modalText"),
      span = document.getElementsByClassName("close")[0];

let audio = new Audio(),
    isPlaying = false;

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
        audio.src = data.audio_url;
        audio.play();
        isPlaying = true;
        speechBtn.innerHTML = `Pause Speech &nbsp;<i class="fa-solid fa-pause"></i>`;
    })
    .catch(error => {
        console.error("Error:", error);
        modalText.innerHTML = `Failed to generate audio. Please try again.`;
        modal.style.display = "block";
    });
}

speechBtn.addEventListener("click", (e) => {
    e.preventDefault();
    if (textarea.value === "") {
        modalText.innerHTML = `Please enter text`;
        modal.style.display = "block";
        return;
    }
    if (isPlaying) {
        audio.pause();
        isPlaying = false;
        speechBtn.innerHTML = `Resume Speech &nbsp;<i class="fa-solid fa-play"></i>`;
    } else if (!audio.src) {
        textToSpeech();
    } else {
        audio.play();
        isPlaying = true;
        speechBtn.innerHTML = `Pause Speech &nbsp;<i class="fa-solid fa-pause"></i>`;
    }
});

// Modal close functionality
span.onclick = function() {
    modal.style.display = "none";
};
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
};
