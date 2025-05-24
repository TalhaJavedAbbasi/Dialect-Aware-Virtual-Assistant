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

      // Show custom recording notification as toast
      addMessage('system', 'Recording...', true);


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

     // Show toast notification when recording stops
    addMessage('system', 'Recording stopped. Processing...', true);

    // Show loader when processing audio
    loader.style.display = 'flex';
  }
}


async function sendAudioToServer(audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'input.wav');

  loader.style.display = 'block';

  try {
    const isTranslationMode = document.getElementById("enable-translation-mode").checked;
    const response = await fetch(`/api/audio-input?translation=${isTranslationMode}`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    console.log('Server response:', result);

    const transcription = result.user_message;

    if (!transcription) {
      loader.style.display = 'none';
      addMessage('system', '⚠️ No speech detected.');
      return;
    }

    addMessage('user', transcription); // Show transcribed speech

    if (isTranslationMode) {
      const targetLang = document.getElementById("target-lang").value;
      const translationRes = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: transcription, target_lang: targetLang })
      });

      const translationData = await translationRes.json();
      loader.style.display = 'none';

      if (translationData.translated) {
        const speaker = result.speaker || "Unknown"; // ✅ use result, not translationData
        const finalText = `${speaker}: ${translationData.translated}`;
        addMessage('assistant', finalText);
        await playAudioResponse(translationData.translated);
      } else {
        addMessage('assistant', '⚠️ Translation failed.');
      }

    } else {
      const assistantData = result.assistant_response;
      loader.style.display = 'none';

      if (assistantData && assistantData.assistant_response) {
        addMessage('assistant', assistantData.assistant_response, assistantData.detected_tone);
        await playAudioResponse(assistantData.assistant_response);
      } else {
        addMessage('assistant', '⚠️ Voice input unclear or no response returned.');
      }
    }

  } catch (error) {
    console.error('Error sending audio to server:', error);
    loader.style.display = 'none';
    addMessage('assistant', '⚠️ Error processing audio. Please try again.');
  }

  // ✅ Fix mic/send toggle
  if (chatInput.value.trim() === '') {
    sendButton.style.display = 'none';
    micButton.style.display = 'block';
  } else {
    sendButton.style.display = 'block';
    micButton.style.display = 'none';
  }
}


// Play TTS response
async function playAudioResponse(text) {
  console.log("🔊 playAudioResponse called with:", text);

  try {
    // Send text to the TTS API
    const response = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    console.log("TTS fetch response status:", response.status);


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
    audio.onplay = () => console.log("✅ Audio is playing...");
    audio.onerror = (e) => console.error("❌ Audio playback error:", e);

  } catch (error) {
    console.error('Error:', error.message);
    alert('Failed to generate audio. Please try again later.');
  }
}



function addMessage(role, content, detectedTone = null, isNotification = false) {
    const message = document.createElement('div');
    message.classList.add('Message');
    message.setAttribute('data-role', role);

    if (isNotification) {
        // Show toast notification instead of adding to chat
        showToast(content, true);
    } else {
        if (role === 'assistant') {
            if (detectedTone && ["Happy", "Sad", "Frustrated"].includes(detectedTone)) {
                // Assistant message with detected tone
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
                // Regular assistant message without tone analysis
                message.innerHTML = `<div class="assistant-response">${content}</div>`;
            }
        } else {
            message.textContent = content;
        }

        chatContainer.appendChild(message);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
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


sendButton.addEventListener("click", async () => {
  const userMessage = chatInput.value.trim();
  if (!userMessage) return;

  // Disable chat controls
  chatInput.disabled = true;
  sendButton.disabled = true;

  // Add user message to chat
  addMessage("user", userMessage);
  chatInput.value = "";

  // Reset textarea height to its minimum and recalculate overflow
  const lineHeight = parseInt(getComputedStyle(chatInput).lineHeight, 10);
  chatInput.style.height = `${lineHeight}px`;
  chatInput.style.overflowY = "hidden";

  // Show loader
  loader.style.display = "flex";

  const isTranslationMode = document.getElementById("enable-translation-mode").checked;

  try {
    if (isTranslationMode) {
      await handleTranslationFlow(userMessage);
      loader.style.display = "none"; // ✅ Ensure loader is hidden after translation
    } else {
      const response = await fetch("/api/gemini-response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
      });

      const data = await response.json();
      console.log("Raw API Response:", data); // ✅ Keep the log
      loader.style.display = "none";

      if (data.assistant_response) {
        addMessage("assistant", data.assistant_response, data.detected_tone);
        await playAudioResponse(data.assistant_response);
      } else {
        addMessage("assistant", "Sorry, something went wrong.");
      }
    }
  } catch (error) {
    loader.style.display = "none";
    addMessage("assistant", "Error connecting to the server.");
  } finally {
    chatInput.disabled = false;
    sendButton.disabled = false;
    chatInput.focus();

    // ✅ Reapply mic/send toggle behavior
    if (chatInput.value.trim() === '') {
      sendButton.style.display = 'none';
      micButton.style.display = 'block';
    } else {
      sendButton.style.display = 'block';
      micButton.style.display = 'none';
    }
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

// Open Reminder Modal
document.getElementById('reminder-button').addEventListener('click', function() {
    document.getElementById('reminderModal').style.display = 'block';
});

// Close Reminder Modal
function closeReminderModal() {
    document.getElementById('reminderModal').style.display = 'none';
}

// Submit Reminder Form
document.getElementById('reminderForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const message = document.getElementById('reminderMessage').value;
    const timeInput = document.getElementById('reminderTime').value;
    const priority = document.getElementById('reminderPriority').value;

    if (!timeInput) {
        showToast("Please select a reminder time.", true);
        return;
    }

    // Convert local datetime to UTC "YYYY-MM-DD HH:MM:SS"
    const localDate = new Date(timeInput);
    const utcString = localDate.toISOString().slice(0, 19).replace("T", " ");  // ISO -> UTC format

    const response = await fetch('/api/add-reminder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, remind_at: utcString, priority })
    });

    const result = await response.json();

    if (response.ok) {
        showToast(result.message);
        closeReminderModal();
    } else {
        showToast(result.error || "Failed to set reminder", true);
    }
});


async function pollReminders() {
    try {
        const response = await fetch('/api/check-reminders');
        const data = await response.json();

        console.log("🧪 Polled Reminders:", data); // Add this

        if (data.reminders && data.reminders.length > 0) {
            data.reminders.forEach(reminder => {
                const msg = `⏰ Reminder: ${reminder.message} (Priority: ${reminder.priority})`;
                console.log("🔔 Showing Reminder:", msg); // Add this

                addMessage('assistant', msg); // Show toast
            });
        }
    } catch (err) {
        console.error("Reminder poll error:", err);
    }
}

// Check reminders every 30 seconds
setInterval(pollReminders, 50000);


document.getElementById("reminder-history-button").addEventListener("click", function () {
    window.location.href = "/reminders";
});



async function loadFilteredReminders() {
    const priority = document.getElementById("filter-priority").value;
    const muted = document.getElementById("filter-muted").value;
    const startDate = document.getElementById("filter-start-date").value;
    const endDate = document.getElementById("filter-end-date").value;


    let url = '/api/reminder-history';

    const params = new URLSearchParams();
    if (priority !== 'all') params.append('priority', priority);
    if (muted !== 'all') params.append('muted', muted);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    if ([...params].length > 0) url += '?' + params.toString();


    try {
        const response = await fetch(url);
        const result = await response.json();

        const listContainer = document.getElementById("reminder-history-list");
        listContainer.innerHTML = '';

        if (result.reminders.length === 0) {
            listContainer.innerHTML = "<p>No matching reminders found.</p>";
        } else {
            result.reminders.forEach(r => {
                const el = document.createElement("div");
                el.style.borderBottom = "1px solid #ccc";
                el.style.padding = "5px 0";

                const muteLabel = r.is_muted ? 'Unmute' : 'Mute';
                const muteButtonId = `mute-btn-${r.id}`;

                el.innerHTML = `
                    <strong>${r.message}</strong><br>
                    Time: ${r.remind_at}<br>
                    Priority: ${r.priority}<br>
                    Status: ${r.is_seen ? 'Seen' : 'Unseen'} | Muted: ${r.is_muted ? 'Yes' : 'No'}<br>
                    <button class="btn btn-sm btn-warning" id="${muteButtonId}">${muteLabel}</button>
                    <button class="btn btn-sm btn-danger" id="delete-btn-${r.id}">Delete</button>
                `;


                listContainer.appendChild(el);

                setTimeout(() => {
                    document.getElementById(`delete-btn-${r.id}`).addEventListener('click', () => deleteReminder(r.id));
                    document.getElementById(`mute-btn-${r.id}`).addEventListener('click', () => toggleMute(r.id));
                }, 0);

            });
        }

        document.getElementById("reminder-history-modal").style.display = "block";
    } catch (error) {
        console.error("Error loading filtered reminders:", error);
        showToast("Failed to load reminders", true);
    }
}


function closeReminderHistory() {
    document.getElementById("reminder-history-modal").style.display = "none";
}


async function toggleMute(reminderId) {
    try {
        const response = await fetch(`/api/toggle-mute/${reminderId}`, { method: 'POST' });
        const result = await response.json();

        if (response.ok) {
            showToast(result.message);
            // Reload the modal
            document.getElementById("reminder-history-button").click();
        } else {
            showToast(result.error || "Failed to update mute status", true);
        }
    } catch (error) {
        console.error("Mute toggle failed:", error);
        showToast("Something went wrong", true);
    }
}


async function deleteReminder(reminderId) {
    if (!confirm("Are you sure you want to delete this reminder?")) return;

    try {
        const response = await fetch(`/api/delete-reminder/${reminderId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message);
            loadFilteredReminders(); // Reload modal
        } else {
            showToast(result.error || "Failed to delete reminder", true);
        }
    } catch (error) {
        console.error("Delete failed:", error);
        showToast("Something went wrong during deletion", true);
    }
}


async function markAllSeen() {
    try {
        const response = await fetch('/api/reminders/mark-all-seen', { method: 'POST' });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message);
            loadFilteredReminders();
        } else {
            showToast(result.error || "Failed to mark as seen", true);
        }
    } catch (error) {
        console.error("Error marking all as seen:", error);
        showToast("Error occurred", true);
    }
}

async function markAllUnseen() {
    try {
        const response = await fetch('/api/reminders/mark-all-unseen', { method: 'POST' });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message);
            loadFilteredReminders();
        } else {
            showToast(result.error || "Failed to mark as unseen", true);
        }
    } catch (error) {
        console.error("Error marking all as unseen:", error);
        showToast("Error occurred", true);
    }
}

// ✅ Add to voice_assistant.js
async function handleTranslationFlow(inputText) {
  const targetLang = document.getElementById("target-lang").value;
  try {
    const response = await fetch("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: inputText, target_lang: targetLang })
    });

    const result = await response.json();
    if (result.translated) {
      const speaker = result.speaker || "Unknown";
      const displayText = `${speaker}: ${result.translated}`;
      addMessage("assistant", displayText);
      await playAudioResponse(result.translated);
    } else {
      addMessage("assistant", "Translation failed.");
    }
  } catch (err) {
    console.error("Translation error:", err);
    addMessage("assistant", "Translation error occurred.");
  }
}

document.getElementById("upload-voice-button").addEventListener("click", () => {
  document.getElementById("uploadVoiceModal").style.display = "block";
});

function closeUploadModal() {
  document.getElementById("uploadVoiceModal").style.display = "none";
}

document.getElementById("uploadVoiceForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const name = document.getElementById("speakerName").value.trim();
  const fileInput = document.getElementById("voiceSample");

  if (!name || fileInput.files.length === 0) {
    showToast("Please provide both name and audio file.", true);
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("audio", fileInput.files[0]);

  try {
    const response = await fetch("/api/upload-voice", {
      method: "POST",
      body: formData
    });

    const result = await response.json();
    if (response.ok) {
      showToast(result.message);
      closeUploadModal();
    } else {
      showToast(result.error, true);
    }
  } catch (err) {
    console.error("Upload failed:", err);
    showToast("Upload failed", true);
  }
});
