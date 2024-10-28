# services/ai_client.py

import json
import aiohttp
import logging
from config.settings import API_KEY, API_URL, DEFAULT_AI_PARAMS

logger = logging.getLogger('discord')

class AIClient:
    def __init__(self):
        self.session = None

    async def initialize(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def chat_with_model(
        self, 
        user_id, 
        new_message, 
        conversation_manager, 
        username=None, 
        reroll=False, 
        **kwargs
    ):
        if self.session is None:
            await self.initialize()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        # Get user-specific parameters
        params = conversation_manager.get_user_params(user_id).copy()
        params.update(kwargs)

        if reroll:
            # Save current parameters before modifying
            current_params = {k: v for k, v in params.items() if k in ['temperature', 'top_p']}
            conversation_manager.save_reroll_parameters(user_id, current_params)

            # Adjust parameters for this user only
            params['temperature'] = params.get('temperature', 1.0) + 0.1
            params['top_p'] = min(params.get('top_p', 1.0) + 0.05, 1.0)

        # Get user conversation history
        history = conversation_manager.get_conversation(user_id)

        if not history:
            # Add system message for personality
            system_message = conversation_manager.get_ai_personality()
            if username:
                system_message += f"\nYou are talking to a Discord user named {username}."
            history.append({"role": "system", "content": system_message})

            # Load pre-loaded conversation if enabled
            if conversation_manager.should_load_example_dialogue():
                history.extend(conversation_manager.get_example_dialogue())

        if reroll:
            # For rerolls, we want to keep everything up to the last user message
            # Remove the last assistant response if it exists
            if history and history[-1]['role'] == 'assistant':
                history.pop()
        else:
            # For new messages, add the user message
            user_message = f"{username}: {new_message}" if username else new_message
            history.append({"role": "user", "content": user_message})

        # Manage token context limit
        conversation_manager.manage_conversation_length(user_id)

        data = {
            "messages": history,
            **params
        }

        try:
            async with self.session.post(API_URL, headers=headers, json=data) as response:
                response_json = await response.json()
                
                if response.status == 200:
                    if not response_json.get("choices"):
                        logger.error("API returned no choices", extra={'user_id': user_id, 'command': 'chat_with_model'})
                        return "The AI model returned an empty response. Please try again."
                    
                    ai_response = response_json["choices"][0]["message"]["content"]
                    if not ai_response or not ai_response.strip():
                        logger.error("API returned empty content", extra={'user_id': user_id, 'command': 'chat_with_model'})
                        return "The AI model returned an empty response. Please try again."
                    
                    # Save conversation and update last response
                    conversation_manager.save_conversation_log(user_id)
                    conversation_manager.set_last_response(user_id, ai_response)
                    
                    # Trim the conversation if needed
                    conversation_manager.manage_conversation_length(user_id)
                    
                    return ai_response
                else:
                    error_json = await response.json()
                    error_message = error_json.get('error', {}).get('message', 'Unknown error occurred')
                    error_type = error_json.get('error', {}).get('type', 'UNKNOWN_ERROR')
                    
                    user_friendly_message = {
                        'AUTHENTICATION_FAILURE': "I'm having trouble authenticating with my AI service. Please notify the bot administrator.",
                        'MODEL_OFFLINE': "The AI model is temporarily unavailable. Please try again in a few minutes.",
                        'CONTEXT_LENGTH_EXCEEDED': "The conversation is too long. Please try clearing history with /clear_history.",
                        'RATE_LIMIT_EXCEEDED': "Too many requests. Please wait a moment before trying again.",
                        'UNKNOWN_ERROR': f"An unexpected error occurred (Status {response.status}): {error_message}"
                    }.get(error_type, f"API Error: {error_message}")
                    
                    logger.error(f"API Error {response.status}: {error_json}", 
                                extra={'user_id': user_id, 'command': 'chat_with_model'})
                    return user_friendly_message

        except aiohttp.ClientError as e:
            error_message = f"Network error: {str(e)}"
            logger.error(error_message, extra={'user_id': user_id, 'command': 'chat_with_model'})
            return "I'm having trouble connecting to the AI service. Please try again in a moment."
            
        except json.JSONDecodeError as e:
            error_message = f"Invalid API response: {str(e)}"
            logger.error(error_message, extra={'user_id': user_id, 'command': 'chat_with_model'})
            return "I received an invalid response from the AI service. Please try again."
            
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(error_message, extra={'user_id': user_id, 'command': 'chat_with_model'})
            return f"An unexpected error occurred: {str(e)}"

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
