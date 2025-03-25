from flask import Blueprint, render_template, request, jsonify
from app.models import CustomCommand, CommandShortcut
from app import db  # Import database instance

# Define Blueprint
voice_commands_bp = Blueprint('voice_commands', __name__, url_prefix='/voice-commands')

# Route to display voice commands page
@voice_commands_bp.route('/')
def voice_commands_page():
    return render_template('voice_commands.html')

# API to create a new command
@voice_commands_bp.route('/create', methods=['POST'])
def create_command():
    data = request.json
    new_command = CustomCommand(
        user_id=data['user_id'],
        command_name=data['command_name'],
        trigger_phrase=data['trigger_phrase'],
        action_type=data['action_type'],
        parameters=data.get('parameters', {}),
        status=True
    )
    db.session.add(new_command)
    db.session.commit()
    return jsonify({'message': 'Command saved successfully!'})


# Fetch all commands
@voice_commands_bp.route('/get-commands', methods=['GET'])
def get_commands():
    commands = CustomCommand.query.all()
    command_list = [
        {
            'id': cmd.id,
            'command_name': cmd.command_name,
            'trigger_phrase': cmd.trigger_phrase,
            'action_type': cmd.action_type,
            'parameters': cmd.parameters,
            'status': cmd.status,
            'activation_schedule': cmd.activation_schedule
        }
        for cmd in commands
    ]
    return jsonify(command_list)


# Update command
@voice_commands_bp.route('/update/<int:cmd_id>', methods=['PUT'])
def update_command(cmd_id):
    data = request.json
    command = CustomCommand.query.get(cmd_id)
    if not command:
        return jsonify({'error': 'Command not found'}), 404

    command.command_name = data['command_name']
    command.trigger_phrase = data['trigger_phrase']
    command.action_type = data['action_type']
    command.parameters = data.get('parameters', {})
    db.session.commit()

    return jsonify({'message': 'Command updated successfully!'})


# Delete command
@voice_commands_bp.route('/delete/<int:cmd_id>', methods=['DELETE'])
def delete_command(cmd_id):
    command = CustomCommand.query.get(cmd_id)
    if not command:
        return jsonify({'error': 'Command not found'}), 404

    db.session.delete(command)
    db.session.commit()

    return jsonify({'message': 'Command deleted successfully!'})


# Toggle command status
@voice_commands_bp.route('/toggle-status/<int:cmd_id>', methods=['PATCH'])
def toggle_command_status(cmd_id):
    command = CustomCommand.query.get(cmd_id)
    if not command:
        return jsonify({'error': 'Command not found'}), 404

    command.status = not command.status  # Toggle status
    db.session.commit()
    return jsonify({'message': f'Command {"enabled" if command.status else "disabled"} successfully!'})


# Update activation schedule
@voice_commands_bp.route('/update-schedule/<int:cmd_id>', methods=['PATCH'])
def update_schedule(cmd_id):
    data = request.json
    command = CustomCommand.query.get(cmd_id)
    if not command:
        return jsonify({'error': 'Command not found'}), 404

    command.activation_schedule = data.get('activation_schedule', None)
    db.session.commit()
    return jsonify({'message': 'Activation schedule updated successfully!'})


# Create a new shortcut
@voice_commands_bp.route('/create-shortcut', methods=['POST'])
def create_shortcut():
    data = request.json
    new_shortcut = CommandShortcut(
        user_id=data['user_id'],
        shortcut_name=data['shortcut_name'],
        description=data.get('description', "")
    )

    # Associate commands
    command_ids = data.get('command_ids', [])
    commands = CustomCommand.query.filter(CustomCommand.id.in_(command_ids)).all()
    new_shortcut.commands.extend(commands)

    db.session.add(new_shortcut)
    db.session.commit()
    return jsonify({'message': 'Shortcut created successfully!'})


# Fetch all shortcuts
@voice_commands_bp.route('/get-shortcuts', methods=['GET'])
def get_shortcuts():
    shortcuts = CommandShortcut.query.all()
    shortcut_list = [
        {
            'id': s.id,
            'shortcut_name': s.shortcut_name,
            'description': s.description,
            'commands': [{'id': c.id, 'command_name': c.command_name} for c in s.commands]
        }
        for s in shortcuts
    ]
    return jsonify(shortcut_list)


# Delete shortcut
@voice_commands_bp.route('/delete-shortcut/<int:shortcut_id>', methods=['DELETE'])
def delete_shortcut(shortcut_id):
    shortcut = CommandShortcut.query.get(shortcut_id)
    if not shortcut:
        return jsonify({'error': 'Shortcut not found'}), 404

    db.session.delete(shortcut)
    db.session.commit()
    return jsonify({'message': 'Shortcut deleted successfully!'})
