// reminder_history.js

async function loadFilteredReminders() {
    const priority = document.getElementById("filter-priority").value;
    const muted = document.getElementById("filter-muted").value;
    const startDate = document.getElementById("filter-start-date").value;
    const endDate = document.getElementById("filter-end-date").value;
    const searchTerm = document.getElementById("filter-search")?.value.trim();

    let url = '/api/reminder-history';
    const params = new URLSearchParams();

    if (priority !== 'all') params.append('priority', priority);
    if (muted !== 'all') params.append('muted', muted);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (searchTerm) params.append("search", searchTerm);  // ✅ use AFTER declaration


    if ([...params].length > 0) url += '?' + params.toString();

    try {
        const response = await fetch(url);
        const result = await response.json();

        const listContainer = document.getElementById("reminder-history-list");
        listContainer.innerHTML = '';

        const exportBtn = document.getElementById("export-csv-btn");
        const emailBtn = document.getElementById("email-summary-btn");


        if (result.reminders.length === 0) {
            listContainer.innerHTML = '<tr><td colspan="6" class="text-center">No matching reminders found.</td></tr>';
            exportBtn.classList.add("disabled");
            exportBtn.setAttribute("aria-disabled", "true");
            exportBtn.onclick = (e) => e.preventDefault();

            emailBtn.classList.add("disabled");
            emailBtn.setAttribute("aria-disabled", "true");
            emailBtn.onclick = (e) => e.preventDefault();
        } else {
              exportBtn.classList.remove("disabled");
              exportBtn.removeAttribute("aria-disabled");
              exportBtn.onclick = () => exportFilteredReminders();

              emailBtn.classList.remove("disabled");
              emailBtn.removeAttribute("aria-disabled");
              emailBtn.onclick = () => sendFilteredEmailSummary();
            result.reminders.forEach(r => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${r.message}</td>
                    <td>${r.remind_at}</td>
                    <td>${r.priority}</td>
                    <td>${r.is_seen ? 'Seen' : 'Unseen'}</td>
                    <td>${r.is_muted ? 'Yes' : 'No'}</td>
                    <td>
                        <button class="btn btn-sm btn-warning me-1" id="mute-btn-${r.id}">${r.is_muted ? 'Unmute' : 'Mute'}</button>
                        <button class="btn btn-sm btn-danger" id="delete-btn-${r.id}">Delete</button>
                    </td>
                `;

                listContainer.appendChild(row);

                setTimeout(() => {
                    document.getElementById(`mute-btn-${r.id}`).addEventListener('click', () => toggleMute(r.id));
                    document.getElementById(`delete-btn-${r.id}`).addEventListener('click', () => deleteReminder(r.id));
                }, 0);
            });
        }

    } catch (error) {
        console.error("Error loading reminders:", error);
        alert("Failed to load reminders.");
    }
}

async function toggleMute(reminderId) {
    try {
        const response = await fetch(`/api/toggle-mute/${reminderId}`, { method: 'POST' });
        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            loadFilteredReminders();
        } else {
            alert(result.error || "Failed to update mute status.");
        }
    } catch (error) {
        console.error("Mute toggle failed:", error);
        alert("Something went wrong");
    }
}

async function deleteReminder(reminderId) {
    if (!confirm("Are you sure you want to delete this reminder?")) return;

    try {
        const response = await fetch(`/api/delete-reminder/${reminderId}`, { method: 'DELETE' });
        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            loadFilteredReminders();
        } else {
            alert(result.error || "Failed to delete reminder");
        }
    } catch (error) {
        console.error("Delete failed:", error);
        alert("An error occurred while deleting");
    }
}

async function markAllSeen() {
    try {
        const response = await fetch('/api/reminders/mark-all-seen', { method: 'POST' });
        const result = await response.json();
        if (response.ok) {
            alert(result.message);
            loadFilteredReminders();
        } else {
            alert(result.error || "Failed to mark all seen");
        }
    } catch (error) {
        console.error("Error marking all seen:", error);
        alert("Error occurred");
    }
}

async function markAllUnseen() {
    try {
        const response = await fetch('/api/reminders/mark-all-unseen', { method: 'POST' });
        const result = await response.json();
        if (response.ok) {
            alert(result.message);
            loadFilteredReminders();
        } else {
            alert(result.error || "Failed to mark all unseen");
        }
    } catch (error) {
        console.error("Error marking all unseen:", error);
        alert("Error occurred");
    }

}
function exportFilteredReminders() {
    const params = new URLSearchParams();
    if (document.getElementById("filter-priority").value !== "all") {
        params.append("priority", document.getElementById("filter-priority").value);
    }
    if (document.getElementById("filter-muted").value !== "all") {
        params.append("muted", document.getElementById("filter-muted").value);
    }
    if (document.getElementById("filter-start-date").value) {
        params.append("start_date", document.getElementById("filter-start-date").value);
    }
    if (document.getElementById("filter-end-date").value) {
        params.append("end_date", document.getElementById("filter-end-date").value);
    }

    const searchTerm = document.getElementById("filter-search")?.value.trim();
    if (searchTerm) params.append("search", searchTerm);


    window.open(`/api/reminder-history/export?${params.toString()}`, "_blank");
}

async function sendFilteredEmailSummary() {
    const params = new URLSearchParams();
    const prio = document.getElementById("filter-priority").value;
    const muted = document.getElementById("filter-muted").value;
    const start = document.getElementById("filter-start-date").value;
    const end = document.getElementById("filter-end-date").value;

    if (prio !== 'all') params.append("priority", prio);
    if (muted !== 'all') params.append("muted", muted);
    if (start) params.append("start_date", start);
    if (end) params.append("end_date", end);

    const btn = document.getElementById("email-summary-btn");
    btn.textContent = "Sending...";

    try {
        const response = await fetch(`/api/reminders/email-summary?${params.toString()}`, {
            method: 'POST'
        });

        const result = await response.json();
        alert(result.message || result.error || "Done");
    } catch (error) {
        console.error("Email summary failed:", error);
        alert("Something went wrong while sending the email.");
    } finally {
        btn.textContent = "📧 Email Reminder Summary";
    }
}

// Load reminders on page load
window.addEventListener("DOMContentLoaded", loadFilteredReminders);
