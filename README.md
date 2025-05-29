# Happy2Align

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-%E2%9C%94%EF%B8%8F-blue)
![CrewAI](https://img.shields.io/badge/CrewAI-ready-green)

Happy2Align is een geavanceerde multi-agent AI-assistent voor requirements engineering en workflow-generatie. Het systeem combineert een centrale orchestrator, meerdere gespecialiseerde agents (Router, Requirement Refiner, Workflow Generator, ToM Helpers, enz.), een transparante API en een moderne chat-frontend.

## 🚀 Features
- **Multi-agent architectuur**: Router, Requirement Refiner, Workflow Generator, Workflow Refiner, Topic Decomposer, Sentiment & Expertise ToM Helpers
- **Centrale orchestrator**: Stuurt de flow, bewaart context, schakelt agents slim in
- **LangChain & CrewAI integratie**: Flexibel, uitbreidbaar, klaar voor productie
- **Fallback & robuustheid**: Automatische fallback bij timeouts of errors
- **Transparante API**: `/api/process` endpoint voor alle communicatie
- **Moderne frontend**: Chatinterface met statusbalk en live agent-status

## 🏗️ Architectuur
```
Gebruiker → Frontend (chat) → /api/process → Orchestrator → [Router → (Topic Decomposer → Requirement Refiner + ToM) → Workflow Generator | Workflow Refiner] → Antwoord
```
- **Orchestrator**: Stuurt de flow, roept agents aan, bewaart context/history
- **Agents**: Elke agent heeft een eigen prompt (zie `agents/prompts.py`)
- **LangChain/CrewAI**: LLM-calls, memory, tools, conditionele branching

## ⚡ Installatie
1. Clone deze repo:
   ```bash
   git clone https://github.com/janssja/happy2align.git
   cd happy2align
   ```
2. Maak een virtuele omgeving en installeer requirements:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Zet je OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=sk-...
   ```
4. Start de backend:
   ```bash
   python src/main.py
   ```
5. Open de frontend in je browser (`http://localhost:5001`)

## 🧑‍💻 Gebruik
- Typ je wens of vraag in de chat.
- De orchestrator bepaalt automatisch de juiste flow en agents.
- Je ziet de status van alle agents live boven de chat.
- Resultaten (requirements, workflow, etc.) verschijnen in de chat.

## 📚 Voorbeeld API-call
```bash
curl -X POST http://localhost:5001/api/process \
  -H 'Content-Type: application/json' \
  -d '{"message": "Ik wil een app die automatisch taken plant", "history": []}'
```

## 🛠️ Ontwikkeltips
- **Agents en prompts**: Zie `agents/prompts.py` voor alle prompt skeletons.
- **Orchestrator**: Zie `agents/orchestrator.py` voor de centrale flow.
- **Frontend**: Zie `templates/chat.html` voor de chatinterface en statusbalk.
- **.env**: Zet je OpenAI key en andere secrets nooit in git.
- **.gitignore**: Is al geconfigureerd voor Python, venv, logs, etc.

## 🤝 Bijdragen
Pull requests, issues en suggesties zijn welkom!

## 📄 Licentie
MIT