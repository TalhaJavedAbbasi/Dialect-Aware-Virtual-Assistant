  const chatContainer = document.getElementById('chat-container');
  const chatInput = document.getElementById('chat-input');
  const sendButton = document.getElementById('send-button');
  const micButton = document.getElementById('mic-button');
  const resetContextButton = document.getElementById('reset-context-button'); // Reset context button
  const loader = document.getElementById('loader'); // Get the loader element
  const helpButton = document.getElementById('help-button');
  const helpModal = document.getElementById('help-modal');
  const closeHelpModal = document.getElementById('close-help-modal');
  const fabButton = document.getElementById('fab-button');
  const fabMenu = document.getElementById('fab-menu');

  fabButton.addEventListener('click', () => {
    fabMenu.classList.toggle('show'); // Toggle the menu's visibility
  });


  helpButton.addEventListener('click', () => {
    helpModal.style.display = 'block';
  });

  closeHelpModal.addEventListener('click', () => {
    helpModal.style.display = 'none';
  });

  let mediaRecorder;
  let audioChunks = [];

chatInput.addEventListener("input", () => {
  const minRows = 1; // Minimum rows
  const maxRows = 5; // Maximum rows
  const lineHeight = parseInt(getComputedStyle(chatInput).lineHeight, 10); // Get the line height

  // Reset height to auto to recalculate correctly
  chatInput.style.height = "auto";

  // Calculate the new height based on scrollHeight
  const newHeight = Math.min(chatInput.scrollHeight, lineHeight * maxRows);

  // Apply the new height with constraints
  chatInput.style.height = `${Math.max(newHeight, lineHeight * minRows)}px`;

  // Add overflow-y:auto when exceeding max height
  if (newHeight === lineHeight * maxRows) {
    chatInput.style.overflowY = "auto";
  } else {
    chatInput.style.overflowY = "hidden";
  }
  // Toggle between mic and send button when user types or clears the input
  if (chatInput.value.trim() !== '') {
    sendButton.style.display = 'block';
    micButton.style.display = 'none';
  } else {
    sendButton.style.display = 'none';
    micButton.style.display = 'block';
  }
});


// Initial state setup
sendButton.style.display = 'none'; // Initially hidden
micButton.style.display = 'block'; // Initially shown


sendButton.addEventListener('click', async () => {
  const userMessage = chatInput.value.trim();
  if (!userMessage) return;

   // Disable chat controls
  chatInput.disabled = true;
  sendButton.disabled = true;

  // Add user message to chat
  addMessage('user', userMessage);
  chatInput.value = '';

  // Reset textarea height to its minimum and recalculate overflow
  const lineHeight = parseInt(getComputedStyle(chatInput).lineHeight, 10); // Get line height
  chatInput.style.height = `${lineHeight}px`;
  chatInput.style.overflowY = "hidden"; // Hide overflow after reset

  // Show loader
  loader.style.display = 'flex';

  // Send message to the server
  try {
// Send message to the server for Gemini response
    const response = await fetch('/api/gemini-response', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: userMessage }),
    });

    const data = await response.json();
    console.log("Raw API Response:", data);  // ✅ Log the entire response

    loader.style.display = 'none';

    if (data.assistant_response) {
        // Add assistant message
        addMessageWithTone('assistant', data.assistant_response, data.detected_tone);
    } else {
      addMessage('assistant', 'Sorry, something went wrong.');
    }
  } catch (error) {
    // Hide loader
    loader.style.display = 'none';
    addMessage('assistant', 'Error connecting to the server.');
  } finally {
    // Re-enable chat controls
    chatInput.disabled = false;
    sendButton.disabled = false;

    // Focus back on the input for convenience
    chatInput.focus();

    // Reset mic and send button visibility
    if (chatInput.value.trim() === '') {
      sendButton.style.display = 'none';
      micButton.style.display = 'block';
    } else {
      sendButton.style.display = 'block';
      micButton.style.display = 'none';
    }
  }
});

// Mock Recording State
let isRecording = false;

// Handle Mic Button Click
micButton.addEventListener('click', () => {
  if (!isRecording) {
    startRecording();
  } else {
    stopRecording();
  }
});

// Start recording audio and show the custom notification
function startRecording() {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = []; // Reset audio chunks

      // Collect audio data
      mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
      };

      // When recording stops, process the audio
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        sendAudioToServer(audioBlob);
        hideNotification(); // Hide the notification when recording stops
      };

      mediaRecorder.start();
      isRecording = true;

      // Show custom recording notification
      showNotification("Recording...");

      micButton.style.background = "#ff4d4d"; // Change mic button to red
    })
    .catch(error => {
      console.error("Error accessing microphone:", error);
      addMessage('assistant', 'Unable to access microphone. Please grant permission.');
    });
}

// Utility to show the notification
function showNotification(message) {
  const notification = document.getElementById("notification");
  notification.textContent = message; // Set the message
  notification.style.display = "block"; // Show notification
}

// Utility to hide the notification
function hideNotification() {
  const notification = document.getElementById("notification");
  notification.style.display = "none"; // Hide notification
}

function stopRecording() {
  if (mediaRecorder) {
    mediaRecorder.stop();
    isRecording = false;

    // Reset mic button appearance
    micButton.style.background = "light-dark(#007bff, #5f6368)";

    // Hide recording notification
    hideNotification();

    // Show loader when processing audio
    loader.style.display = 'flex';
  }
}


async function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'input.wav');
    console.log('Sending audio to server...');
    console.log('Audio blob:', audioBlob);

    try {
        const response = await fetch('/api/audio-input', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        console.log('Server response:', data);

        // Hide loader when transcription is ready
        loader.style.display = 'none';

        if (data.user_message && data.assistant_response) {
            // Show transcribed message as user message
            addMessage('user', data.user_message);

            // Show loader while processing response
            loader.style.display = 'flex';

            setTimeout(() => {
                loader.style.display = 'none'; // Hide loader after response is ready
                addMessage('assistant', data.assistant_response); // Display assistant's response
            }, 1000); // Simulate loader delay for better UI
        } else {
            addMessage('assistant', 'Audio unclear. Please try again.');
        }
    } catch (error) {
        console.error('Error sending audio to server:', error);
        loader.style.display = 'none';
        addMessage('assistant', 'Error processing audio. Please try again.');
    }
}


// Play TTS response
async function playAudioResponse(text) {
  try {
    // Send text to the TTS API
    const response = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    // Check if the response is OK
    if (!response.ok) {
      throw new Error('Error generating audio response.');
    }

    // Convert the response to a Blob
    const audioBlob = await response.blob();

    // Create an audio URL and play it
    const audioURL = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioURL);
    audio.play();
  } catch (error) {
    console.error('Error:', error.message);
    alert('Failed to generate audio. Please try again later.');
  }
}


// Modify message addition for the assistant
function addMessage(role, content) {
  const message = document.createElement('div');
  message.classList.add('Message');
  message.setAttribute('data-role', role);

  if (role === 'assistant') {
    message.innerHTML = content;
    chatContainer.appendChild(message);

    // Trigger TTS playback for assistant messages
    playAudioResponse(content.replace(/(<([^>]+)>)/gi, '')); // Remove HTML tags for TTS
  } else {
    message.textContent = content;
    chatContainer.appendChild(message);
  }

  chatContainer.scrollTop = chatContainer.scrollHeight; // Auto-scroll to latest message
}

function addMessageWithTone(role, content, detectedTone) {
    const message = document.createElement('div');
    message.classList.add('Message');
    message.setAttribute('data-role', role);

    if (role === 'assistant' && ["Happy", "Sad", "Frustrated"].includes(detectedTone)) {
        message.innerHTML = `

                ${content}
                <div class="tone-info">
                    <span class="tone-label">Detected Tone: <strong>${detectedTone}</strong></span>
                    <button class="correct-tone-btn" onclick="showCorrectionModal('${detectedTone}')">
                        Feedback on Tone Analysis
                    </button>
                </div>

        `;
    } else {
        message.innerHTML = `<div class="assistant-response">${content}</div>`;
    }

    chatContainer.appendChild(message);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}





let originalTone = "";

function showCorrectionModal(detectedTone) {
    originalTone = detectedTone; // Store the current tone
    document.getElementById("tone-correction-modal").style.display = "block";
}

function closeCorrectionModal() {
    document.getElementById("tone-correction-modal").style.display = "none";
}

async function submitToneCorrection() {
    const correctTone = document.getElementById("correct-tone").value;

    const response = await fetch("/api/submit-tone-feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ original_tone: originalTone, correct_tone: correctTone })
    });

    const data = await response.json();

    if (response.ok) {
        showToast(data.message, false);
    } else {
        showToast("Failed to update tone. Try again.", true);
    }

    closeCorrectionModal();
}


  // Handle message sending
  sendButton.addEventListener('click', async () => {
    const userMessage = chatInput.value.trim();
    if (!userMessage) return;

    // Add user message to chat
    addMessage('user', userMessage);
    chatInput.value = '';

    // Send message to the server
    try {
      const response = await fetch('/api/send-message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });
      const data = await response.json();
      if (data.response) {
        addMessage('assistant', data.response);
      } else {
        addMessage('assistant', 'Sorry, something went wrong.');
      }
    } catch (error) {
      addMessage('assistant', 'Error connecting to the server.');
    }
  });

document.getElementById("chat-input").addEventListener("keydown", function (event) {
  // Check if "Enter" is pressed without "Shift"
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault(); // Prevent default new line behavior
    document.getElementById("send-button").click(); // Trigger the send button click
  }
});

// Open Mood Summary Modal
document.getElementById("mood-summary-button").addEventListener("click", function() {
    fetch("/api/mood-summary")
        .then(response => response.json())
        .then(data => {
            document.getElementById("mood-summary-text").innerHTML = data.message;
            document.getElementById("mood-summary-modal").classList.add("show");
        })
        .catch(error => console.error("Error fetching mood summary:", error));
});

// Close Mood Summary Modal
document.getElementById("close-mood-modal").addEventListener("click", function() {
    document.getElementById("mood-summary-modal").classList.remove("show");
});

document.getElementById("tone-overview-button").addEventListener("click", function() {
        window.location.href = "/tone-overview";
    });





// Trigger modal on Reset Context button click
resetContextButton.addEventListener("click", showConfirmationModal);

async function showConfirmationModal() {
    // Show the modal
    document.getElementById("confirmation-modal").style.display = 'block';

    try {
        // Fetch the current context
        const response = await fetch('/api/get-context', { method: 'GET' });
        const result = await response.json();

        const contextMessagesDiv = document.getElementById("context-messages");

        if (response.ok) {
            const contextMessages = result.context.messages;

            // Clear any previous content
            contextMessagesDiv.innerHTML = '';

            if (contextMessages.length === 0) {
                // If no context is present, display a message
                const noContextMessage = document.createElement('p');
                noContextMessage.textContent = 'No context available.';
                contextMessagesDiv.appendChild(noContextMessage);
            } else {
                // Display messages from the current context
                contextMessages.forEach(msg => {
                    const msgElement = document.createElement('p');
                    // Strip out HTML tags from the content
                    const cleanMessage = msg.content.replace(/<\/?[^>]+(>|$)/g, "");
                    msgElement.textContent = `${msg.role}: ${cleanMessage}`;
                    contextMessagesDiv.appendChild(msgElement);
                });
            }
        } else {
            console.error('Error fetching context:', result.error);
        }
    } catch (error) {
        console.error('Error fetching context:', error);
    }
}



// Close modal on Cancel
document.getElementById("cancel-reset-button").addEventListener("click", hideConfirmationModal);

// Hide modal
function hideConfirmationModal() {
    document.getElementById("confirmation-modal").style.display = 'none';
}

// Handle Reset Context confirmation
document.getElementById("confirm-reset-button").addEventListener("click", async () => {
    hideConfirmationModal();

    try {
        // Show the loader
        loader.style.display = 'block';

        const response = await fetch('/api/reset-context', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message || "Context reset successfully!");

            // Clear the chat UI
            chatContainer.innerHTML = '';
        } else {
            showToast(result.error || "Error resetting context. Please try again.", true);
        }
    } catch (error) {
        console.error('Error resetting context:', error);
        showToast("An error occurred while resetting context.", true);
    } finally {
        // Hide the loader
        loader.style.display = 'none';
    }
});

// Show toast notifications
function showToast(message, isError = false) {
    const toast = document.createElement("div");
    toast.className = `Toast ${isError ? "Toast--error" : "Toast--success"}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("Toast--hide");
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}


document.getElementById('registerRecipientForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const name = document.getElementById('recipientName').value;
    const nickname = document.getElementById('recipientNickname').value;
    const email = document.getElementById('recipientEmail').value;

    const response = await fetch('/api/register-recipient', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, nickname, email }),
    });

    const result = await response.json();
    if (response.ok) {
        // Show success toast
        showToast(result.message, false);

        // Hide the modal after a short delay
        setTimeout(() => {
            $('#addRecipientModal').modal('hide');
        }, 1000); // Delay before hiding modal
    } else {
        // Show error toast
        showToast(result.error, true);
    }
});
