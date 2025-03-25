document.addEventListener("DOMContentLoaded", () => {
    loadCommands();

    document.getElementById("commandForm").addEventListener("submit", function(e) {
        e.preventDefault();
        let commandId = document.getElementById("command_id").value;
        let commandData = {
            user_id: 1,
            command_name: document.getElementById("command_name").value,
            trigger_phrase: document.getElementById("trigger_phrase").value,
            action_type: document.getElementById("action_type").value
        };

        let url = commandId ? `/voice-commands/update/${commandId}` : "/voice-commands/create";
        let method = commandId ? "PUT" : "POST";

        fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(commandData)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            document.getElementById("commandForm").reset();
            loadCommands();
        });
    });
});

// Fetch and display commands
function loadCommands() {
    fetch("/voice-commands/get-commands")
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
                    <input type="text" id="schedule-${cmd.id}" value="${cmd.activation_schedule || ''}"
                           placeholder="e.g., 9:00 AM - 5:00 PM">
                    <button onclick="updateSchedule(${cmd.id})">Update</button>
                </td>
                <td>
                    <button onclick="editCommand(${cmd.id}, '${cmd.command_name}', '${cmd.trigger_phrase}', '${cmd.action_type}')">Edit</button>
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
            user_id: 1, // Replace with dynamic user ID if needed
            shortcut_name: document.getElementById("shortcut_name").value,
            description: document.getElementById("shortcut_description").value,
            command_ids: Array.from(document.getElementById("shortcut_commands").selectedOptions).map(option => option.value)
        };

        fetch("/voice-commands/create-shortcut", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(shortcutData)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            document.getElementById("shortcutForm").reset();
            loadShortcuts();
        });
    });
});

// Fetch and display shortcuts
function loadShortcuts() {
    fetch("/voice-commands/get-shortcuts")
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
        fetch("/voice-commands/get-commands")
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
    fetch(`/voice-commands/delete-shortcut/${shortcutId}`, {
        method: "DELETE"
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadShortcuts();
    });
}



// Edit command (fill form)
function editCommand(id, name, trigger, action) {
    document.getElementById("command_id").value = id;
    document.getElementById("command_name").value = name;
    document.getElementById("trigger_phrase").value = trigger;
    document.getElementById("action_type").value = action;

    // Scroll to the form for better user experience
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Delete command
function deleteCommand(id) {
    fetch(`/voice-commands/delete/${id}`, { method: "DELETE" })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadCommands();
    });
}


function updateSchedule(cmd_id) {
    let schedule = document.getElementById(`schedule-${cmd_id}`).value;
    fetch(`/voice-commands/update-schedule/${cmd_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ activation_schedule: schedule })
    }).then(response => response.json()).then(data => alert(data.message));
}

function toggleStatus(cmd_id) {
    fetch(`/voice-commands/toggle-status/${cmd_id}`, {
        method: "PATCH"
    }).then(response => response.json()).then(data => {
        alert(data.message);
        loadCommands();
    });
}