
document.addEventListener("DOMContentLoaded", () => {
    loadCommands();

    document.getElementById("commandForm").addEventListener("submit", function(e) {
        e.preventDefault();
        let commandId = document.getElementById("command_id").value;
        const actionType = document.getElementById("action_type").value;
        let parameters = {};

        if (actionType === "send_email") {
            parameters = {
                to: document.getElementById("param-to")?.value || "",
                subject: document.getElementById("param-subject")?.value || "",
                body: document.getElementById("param-body")?.value || ""
            };
        } else if (actionType === "open_app") {
            parameters = {
                app: document.getElementById("param-app")?.value || ""
            };
        }
        let commandData = {
            user_id: CURRENT_USER_ID,
            command_name: document.getElementById("command_name").value,
            trigger_phrase: document.getElementById("trigger_phrase").value,
            action_type: actionType,
            parameters: parameters
        };


        let url = commandId ? `/voice_commands/update/${commandId}` : "/voice_commands/create";
        let method = commandId ? "PUT" : "POST";

        fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(commandData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error); // Show error like "shortcut already exists"
            } else {
                alert(data.message);
                document.getElementById("shortcutForm").reset();
                loadShortcuts();
            }
        });
    });
});

// Fetch and display commands
function loadCommands() {
    fetch("/voice_commands/get-commands")
    .then(response => response.json())
    .then(data => {
        let commandList = document.getElementById("commandList");
        commandList.innerHTML = "";
        data.forEach(cmd => {
            let row = `<tr>
                <td>${cmd.command_name}</td>
                <td>${cmd.trigger_phrase}</td>
                <td>${cmd.action_type}</td>
                <td>
                    <input type="checkbox" ${cmd.status ? "checked" : ""}
                           onchange="toggleStatus(${cmd.id})">
                </td>
                <td>
                    <div id="schedule-${cmd.id}" class="form-check form-check-inline">
                        ${['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(day => `
                            <input class="form-check-input" type="checkbox" id="day-${day}-${cmd.id}" name="days" value="${day}"
                                ${cmd.activation_schedule && cmd.activation_schedule.includes(day) ? 'checked' : ''}>
                            <label class="form-check-label me-2" for="day-${day}-${cmd.id}">${day}</label>
                        `).join('')}
                    </div>
                    <button onclick="updateSchedule(${cmd.id})">Update</button>

                </td>
                <td>
                    <button onclick='editCommand(${cmd.id}, "${cmd.command_name}", "${cmd.trigger_phrase}", "${cmd.action_type}", ${JSON.stringify(cmd.parameters || {})})'>Edit</button>

                    <button onclick="deleteCommand(${cmd.id})">Delete</button>
                </td>
            </tr>`;
            commandList.innerHTML += row;
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    loadCommands();
    loadShortcuts();

    document.getElementById("shortcutForm").addEventListener("submit", function(e) {
        e.preventDefault();

        let shortcutData = {
            user_id: CURRENT_USER_ID, // Replace with dynamic user ID if needed
            shortcut_name: document.getElementById("shortcut_name").value,
            description: document.getElementById("shortcut_description").value,
            command_ids: Array.from(document.getElementById("shortcut_commands").selectedOptions).map(option => option.value)
        };

        fetch("/voice_commands/create-shortcut", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(shortcutData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error); // Show error like "shortcut already exists"
            } else {
                alert(data.message);
                document.getElementById("shortcutForm").reset();
                loadShortcuts();
            }
        });

    });
});

// Fetch and display shortcuts
function loadShortcuts() {
    fetch("/voice_commands/get-shortcuts")
    .then(response => response.json())
    .then(data => {
        let shortcutList = document.getElementById("shortcutList");
        shortcutList.innerHTML = "";
        data.forEach(shortcut => {
            let row = `<tr>
                <td>${shortcut.shortcut_name}</td>
                <td>${shortcut.description || '—'}</td>
                <td>${shortcut.commands.map(c => c.command_name).join(", ")}</td>
                <td>
                    <button onclick="deleteShortcut(${shortcut.id})">Delete</button>
                </td>
            </tr>`;
            shortcutList.innerHTML += row;
        });

        // Load available commands in shortcut creation dropdown
        fetch("/voice_commands/get-commands")
        .then(response => response.json())
        .then(commands => {
            let shortcutCommands = document.getElementById("shortcut_commands");
            shortcutCommands.innerHTML = "";
            commands.forEach(cmd => {
                let option = document.createElement("option");
                option.value = cmd.id;
                option.textContent = cmd.command_name;
                shortcutCommands.appendChild(option);
            });
        });
    });
}

// Delete shortcut
function deleteShortcut(shortcutId) {
    fetch(`/voice_commands/delete-shortcut/${shortcutId}`, {
        method: "DELETE"
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadShortcuts();
    });
}



// Edit command (fill form)
function editCommand(id, name, trigger, action, parameters = {}) {
    document.getElementById("command_id").value = id;
    document.getElementById("command_name").value = name;
    document.getElementById("trigger_phrase").value = trigger;
    document.getElementById("action_type").value = action;

    updateDynamicFields(); // Show dynamic fields

    setTimeout(() => {
        if (action === "send_email") {
            document.getElementById("param-to").value = parameters.to || '';
            document.getElementById("param-subject").value = parameters.subject || '';
            document.getElementById("param-body").value = parameters.body || '';
        } else if (action === "open_app") {
            document.getElementById("param-app").value = parameters.app || '';
        }
    }, 100); // Small delay to ensure input fields exist
}



// Delete command
function deleteCommand(id) {
    fetch(`/voice_commands/delete/${id}`, { method: "DELETE" })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadCommands();
    });
}


function updateSchedule(cmd_id) {
    const selectedDays = Array.from(document.querySelectorAll(`#schedule-${cmd_id} input[name="days"]:checked`))
        .map(day => day.value)
        .join(",");

    fetch(`/voice_commands/update-schedule/${cmd_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ activation_schedule: selectedDays })
    }).then(response => response.json())
      .then(data => alert(data.message));
}


function toggleStatus(cmd_id) {
    fetch(`/voice_commands/toggle-status/${cmd_id}`, {
        method: "PATCH"
    }).then(response => response.json()).then(data => {
        alert(data.message);
        loadCommands();
    });
}

const dynamicParams = document.getElementById("dynamic-params");
const actionTypeSelect = document.getElementById("action_type");

actionTypeSelect.addEventListener("change", updateDynamicFields);

function updateDynamicFields() {
    const selected = actionTypeSelect.value;
    dynamicParams.innerHTML = ""; // Clear previous

    if (selected === "send_email") {
        dynamicParams.innerHTML = `
            <label class="form-label fw-bold">Email Parameters</label>
            <input class="form-control mb-2" id="param-to" placeholder="To (email)" required>
            <input class="form-control mb-2" id="param-subject" placeholder="Subject">
            <textarea class="form-control" id="param-body" rows="3" placeholder="Body"></textarea>
        `;
    } else if (selected === "open_app") {
        dynamicParams.innerHTML = `
            <label class="form-label fw-bold">App Name</label>
            <input class="form-control" id="param-app" placeholder="e.g., notepad or calc">
        `;
    }
}
