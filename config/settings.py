import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API and Discord configuration
API_KEY = os.getenv("API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_URL = "https://neuro.mancer.tech/oai/v1/chat/completions"
ALLOWED_CHANNEL_IDS = set(map(int, os.getenv("ALLOWED_CHANNEL_IDS", "").split(",")))

# Directory configuration
TEXTGEN_DIR = "textgen"
PRELOADS_DIR = "preloads"
CHAT_LOGS_DIR = "chat_logs"

# Model configuration
AVAILABLE_MODELS = {
    "magnum-72b": 16384,
    "magnum-72b-v4": 16384,
    "goliath-120b": 6144
}

# Default AI parameters
DEFAULT_AI_PARAMS = {
    "response_config": None,
    "model": "magnum-72b",
    "temperature": 1,
    "min_p": 0.1,
    "top_p": 1,
    "repetition_penalty": 1.05,
    "max_tokens": 200,
    "n": 1,
    "min_tokens": 0,
    "dynatemp_mode": 0,
    "dynatemp_min": 0,
    "dynatemp_max": 2,
    "dynatemp_exponent": 1,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "top_k": 0,
    "epsilon_cutoff": 0,
    "top_a": 0,
    "typical_p": 1,
    "eta_cutoff": 0,
    "tfs": 1,
    "smoothing_factor": 0,
    "smoothing_curve": 1,
    "mirostat_mode": 0,
    "mirostat_tau": 5,
    "mirostat_eta": 0.1,
    "sampler_priority": [
        "temperature",
        "dynatemp_mode",
        "top_k",
        "top_p",
        "typical_p",
        "epsilon_cutoff",
        "eta_cutoff",
        "tfs",
        "top_a",
        "min_p",
        "mirostat_mode"
    ],
    "logit_bias": None,
    "ignore_eos": False,
    "stop": [],
    "custom_token_bans": [],
    "stream": False,
    "custom_timeout": None,
    "allow_logging": None,
    "logprobs": False,
    "top_logprobs": None
}

# Create necessary directories
for directory in [TEXTGEN_DIR, PRELOADS_DIR, CHAT_LOGS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
