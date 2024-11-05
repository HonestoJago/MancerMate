# services/conversation_manager.py

import json
import os
import re
from collections import defaultdict
import logging
from config.settings import CHAT_LOGS_DIR, PRELOADS_DIR, AVAILABLE_MODELS, DEFAULT_AI_PARAMS

logger = logging.getLogger('discord')

class ConversationManager:
    def __init__(self):
        self.conversations = defaultdict(list)
        self.last_responses = {}
        self.original_messages = {}
        self.response_message_ids = {}
        self.reroll_counters = defaultdict(int)  # Keep for logging
        self.user_params = defaultdict(lambda: DEFAULT_AI_PARAMS.copy())
        self.reroll_parameters = defaultdict(dict)

        # Load dialogue configuration
        self.config, self.ai_personality, self.example_dialogue = self.load_dialogue_from_json()

        # Get current model's context limit
        self.current_token_limit = AVAILABLE_MODELS.get(DEFAULT_AI_PARAMS.get("model", "magnum-72b"), 16384)

    def load_dialogue_from_json(self, file_name='example_dialogue.json'):
        file_path = os.path.join(PRELOADS_DIR, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            if not isinstance(data, dict) or 'config' not in data:
                raise ValueError("Invalid JSON structure. Expected 'config' key.")

            config = data.get('config', {})
            ai_personality = data.get('ai_personality', "")
            dialogue = data.get('dialogue', [])

            if not isinstance(config, dict) or 'load_example_dialogue' not in config:
                raise ValueError("Invalid config structure. Expected 'load_example_dialogue' key.")

            if not isinstance(dialogue, list):
                raise ValueError("Invalid dialogue format")

            return config, ai_personality, dialogue
        except Exception as e:
            logger.error(f"Error loading dialogue: {str(e)}", extra={'user_id': 'N/A', 'command': 'load_dialogue_from_json'})
            return {'load_example_dialogue': False}, "You are a helpful assistant.", []

    def get_conversation(self, user_id):
        return self.conversations[user_id]

    def get_ai_personality(self):
        return self.ai_personality

    def get_example_dialogue(self):
        return self.example_dialogue

    def should_load_example_dialogue(self):
        return self.config.get('load_example_dialogue', False)

    def set_last_response(self, user_id, response):
        self.last_responses[user_id] = response

    def get_last_response(self, user_id):
        return self.last_responses.get(user_id)

    def save_original_message(self, user_id, message):
        self.original_messages[user_id] = message

    def get_original_message(self, user_id):
        return self.original_messages.get(user_id, "")

    def save_response_message_id(self, user_id, message_id):
        self.response_message_ids[user_id] = message_id

    def get_response_message_id(self, user_id):
        return self.response_message_ids.get(user_id)

    def increment_reroll(self, user_id):
        self.reroll_counters[user_id] += 1

    def save_reroll_parameters(self, user_id, parameters):
        self.reroll_parameters[user_id] = parameters.copy()

    def reset_reroll_parameters(self, user_id):
        if user_id in self.reroll_parameters:
            original_params = self.reroll_parameters[user_id]
            # Update user-specific parameters instead of global
            self.user_params[user_id].update(original_params)
            del self.reroll_parameters[user_id]

    def update_last_response(self, user_id, new_response):
        history = self.conversations[user_id]
        
        # Find the last assistant message and update it
        for i in reversed(range(len(history))):
            if history[i]['role'] == 'assistant':
                history[i]['content'] = new_response
                break
        else:
            # If no assistant message found, append new one
            history.append({"role": "assistant", "content": new_response})
        
        # Update the last_responses cache
        self.last_responses[user_id] = new_response

    @staticmethod
    def estimate_tokens(message: str) -> int:
        return len(message) // 4  # Rough estimation

    def manage_conversation_length(self, user_id):
        history = self.conversations[user_id]
        total_tokens = sum(self.estimate_tokens(msg["content"]) for msg in history)

        # Ensure the system message and pre-loaded conversation are not trimmed
        preloaded_length = len(self.example_dialogue) + 1 if self.should_load_example_dialogue() else 1

        while total_tokens > self.current_token_limit and len(history) > preloaded_length:
            removed_msg = history.pop(preloaded_length)
            total_tokens -= self.estimate_tokens(removed_msg["content"])

    def get_next_log_number(self, user_id: int) -> int:
        pattern = re.compile(f"{user_id}_(\\d+)\\.json")
        max_number = 0
        for filename in os.listdir(CHAT_LOGS_DIR):
            match = pattern.match(filename)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)
        return max_number + 1

    def save_conversation_log(self, user_id):
        log_number = self.get_next_log_number(user_id)
        log_file = os.path.join(CHAT_LOGS_DIR, f"{user_id}_{log_number}.json")
        try:
            with open(log_file, 'w', encoding='utf-8') as file:
                json.dump(self.conversations[user_id], file, indent=2, ensure_ascii=False)
            logger.info(f"Conversation log saved: {log_file}", 
                       extra={'user_id': user_id, 'command': 'save_conversation_log'})
        except Exception as e:
            logger.error(f"Error saving conversation log: {str(e)}", 
                        extra={'user_id': user_id, 'command': 'save_conversation_log'})

    def clear_history(self, user_id):
        # Clear all user-specific data
        self.conversations[user_id] = []
        if user_id in self.last_responses:
            del self.last_responses[user_id]
        if user_id in self.original_messages:
            del self.original_messages[user_id]
        if user_id in self.response_message_ids:
            del self.response_message_ids[user_id]
        if user_id in self.reroll_counters:
            del self.reroll_counters[user_id]
        if user_id in self.reroll_parameters:
            del self.reroll_parameters[user_id]
        
        # Reinitialize the conversation with system message
        system_message = {"role": "system", "content": self.ai_personality}
        self.conversations[user_id].append(system_message)
        
        # Add example dialogue if enabled
        if self.should_load_example_dialogue():
            self.conversations[user_id].extend(self.example_dialogue)

    def get_user_params(self, user_id):
        return self.user_params[user_id]
