# utils/logger.py

import logging
import json

class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Add user_id and command attributes if they don't exist
        if not hasattr(record, 'user_id'):
            record.user_id = 'N/A'
        if not hasattr(record, 'command'):
            record.command = 'N/A'
        
        # Format the message
        message = super().format(record)
        
        # If the message contains 'API Error', process it
        if 'API Error' in record.getMessage():
            try:
                # Attempt to parse JSON from the message
                start = record.msg.find('{')
                end = record.msg.rfind('}') + 1
                error_data = json.loads(record.msg[start:end])
                error_type = error_data.get('error', {}).get('type', 'UNKNOWN_ERROR')
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                message = f"API Error - {error_type}: {error_message}"
            except:
                pass  # If parsing fails, keep the original message
        
        return message

def setup_logger():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)

    # Create handlers
    file_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a')
    stream_handler = logging.StreamHandler()

    # Create and set formatter
    formatter = CustomFormatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
