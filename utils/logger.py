import logging

class CustomFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'user_id'):
            record.user_id = 'N/A'
        if not hasattr(record, 'command'):
            record.command = 'N/A'
        
        if 'API Error' in str(record.msg):
            try:
                status_code = record.msg.split('API Error ')[1].split(':')[0]
                error_data = eval(record.msg.split(': ', 1)[1])
                error_type = error_data.get('error', {}).get('type', 'UNKNOWN_ERROR')
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                record.msg = f"API Error {status_code} - {error_type}: {error_message}"
            except:
                pass
        
        return super().format(record)

def setup_logger():
    logger = logging.getLogger('discord')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a'),
            logging.StreamHandler()
        ]
    )

    formatter = CustomFormatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    for handler in logger.handlers:
        handler.setFormatter(formatter)
    
    return logger
