"""
Configuratie voor de agents met timeout en fallback support
"""

import os
from dotenv import load_dotenv

# Laad environment variables
load_dotenv()

# OpenAI configuratie
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")

# Model configuratie met fallback
PRIMARY_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-2025-04-14")  # Nieuwste GPT-4 model
FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL", "o4-mini-2025-04-16")  # Snelle fallback
DEFAULT_MODEL = PRIMARY_MODEL

# Temperature settings
DEFAULT_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
FALLBACK_TEMPERATURE = float(os.getenv("OPENAI_FALLBACK_TEMPERATURE", "0.7"))

# Timeout configuratie
MODEL_TIMEOUT = int(os.getenv("MODEL_TIMEOUT", "30"))  # 30 seconden voor primary model
FALLBACK_TIMEOUT = int(os.getenv("FALLBACK_TIMEOUT", "10"))  # 10 seconden voor fallback
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "45"))  # Totale request timeout

# Agent configuratie
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Systeem prompts
ROUTER_SYSTEM_PROMPT = """Je bent een Router agent die berichten analyseert en doorstuurt naar de juiste agent.
Analyseer het bericht en bepaal of het gaat om:
1. Requirement verfijning (antwoord met "RequirementRefiner")
2. Workflow generatie (antwoord met "WorkflowRefiner")

Je moet ALTIJD één van deze twee opties kiezen:
- "RequirementRefiner" voor vragen over requirements
- "WorkflowRefiner" voor vragen over workflows

Antwoord met ALLEEN één van deze twee woorden, zonder extra tekst."""

REQUIREMENT_REFINER_SYSTEM_PROMPT = """Je bent een Requirement Refiner agent die helpt bij het verfijnen van requirements.
Analyseer het bericht en help de gebruiker om duidelijke, meetbare en testbare requirements op te stellen.
Als de requirements compleet zijn, zeg dan "requirements_complete"."""

WORKFLOW_GENERATOR_SYSTEM_PROMPT = """Je bent een Workflow Generator agent die helpt bij het opstellen van workflows.
Gebruik de requirements om een gedetailleerde workflow te genereren met duidelijke stappen en verantwoordelijkheden."""

# Database configuratie
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/happy2align.db")

# API configuratie
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Model retry configuratie
MODEL_RETRY_CONFIG = {
    "max_retries": 2,
    "retry_delay": 1.0,  # seconds
    "timeout": MODEL_TIMEOUT,
    "fallback_timeout": FALLBACK_TIMEOUT,
    "use_fallback": True
}