import os
from textual.app import App
from textual.widgets import Header, Footer, Input, Button, Static, Label
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.binding import Binding
import requests
import json

class Happy2AlignTUI(App):
    """Terminal User Interface voor Happy 2 Align."""
    
    CSS_PATH = "style.css"
    BINDINGS = [
        Binding("q", "quit", "Afsluiten"),
        Binding("n", "new_session", "Nieuwe Sessie"),
        Binding("h", "toggle_help", "Help")
    ]
    
    # Reactieve variabelen
    current_session_id = reactive(None)
    user_id = reactive(None)
    logged_in = reactive(False)
    credits = reactive(0)
    
    def __init__(self, api_url="http://localhost:5000"):
        """Initialiseer de TUI app."""
        super().__init__()
        self.api_url = api_url
        self.conversation_history = []
    
    def compose(self):
        """Bouw de UI op."""
        yield Header()
        
        with Container(id="main"):
            # Login scherm (standaard zichtbaar)
            with Container(id="login_screen"):
                yield Static("Happy 2 Align", id="title")
                yield Static("Log in om te beginnen", id="subtitle")
                yield Input(placeholder="Gebruikersnaam", id="username_input")
                yield Input(placeholder="Wachtwoord", id="password_input", password=True)
                
                with Horizontal(id="login_buttons"):
                    yield Button("Inloggen", variant="primary", id="login_button")
                    yield Button("Registreren", id="register_button")
            
            # Hoofdscherm (verborgen tot ingelogd)
            with Container(id="main_screen", classes="hidden"):
                with Horizontal(id="header_bar"):
                    yield Static("Happy 2 Align", id="app_title")
                    yield Static("", id="credits_display")
                
                with Container(id="session_container"):
                    yield Static("Geen actieve sessie", id="session_status")
                    
                    # Conversatie weergave
                    yield Static("", id="conversation")
                    
                    # Input gebied
                    with Container(id="input_area"):
                        yield Input(placeholder="Type je vraag hier...", id="user_input")
                        yield Button("Verstuur", variant="primary", id="send_button")
        
        yield Footer()
    
    def on_mount(self):
        """Wordt uitgevoerd wanneer de app wordt opgestart."""
        # Stel CSS in voor verborgen elementen
        self.query_one("#main_screen").add_class("hidden")
        
        # Focus op gebruikersnaam input
        self.query_one("#username_input").focus()
    
    def on_button_pressed(self, event: Button.Pressed):
        """Afhandeling van button clicks."""
        button_id = event.button.id
        
        if button_id == "login_button":
            self.handle_login()
        elif button_id == "register_button":
            self.handle_register()
        elif button_id == "send_button":
            self.handle_send_message()
    
    def handle_login(self):
        """Verwerk login poging."""
        username = self.query_one("#username_input").value
        password = self.query_one("#password_input").value
        
        if not username or not password:
            self.show_notification("Vul alle velden in")
            return
        
        # Simuleer login (in echte app: API call naar backend)
        # In een echte implementatie zou dit een API call naar de backend zijn
        # response = requests.post(f"{self.api_url}/auth/login", json={"username": username, "password": password})
        
        # Voor demo doeleinden:
        self.logged_in = True
        self.user_id = 1
        self.credits = 10
        
        # Update UI
        self.query_one("#login_screen").add_class("hidden")
        self.query_one("#main_screen").remove_class("hidden")
        self.query_one("#credits_display").update(f"Credits: {self.credits}")
        
        # Toon welkomstbericht
        self.show_notification(f"Welkom, {username}!")
    
    def handle_register(self):
        """Verwerk registratie poging."""
        username = self.query_one("#username_input").value
        password = self.query_one("#password_input").value
        
        if not username or not password:
            self.show_notification("Vul alle velden in")
            return
        
        # Simuleer registratie (in echte app: API call naar backend)
        # In een echte implementatie zou dit een API call naar de backend zijn
        # response = requests.post(f"{self.api_url}/auth/register", json={"username": username, "password": password, "email": f"{username}@example.com"})
        
        # Voor demo doeleinden:
        self.show_notification(f"Account aangemaakt voor {username}. Je kunt nu inloggen.")
    
    def handle_send_message(self):
        """Verwerk verzonden bericht."""
        user_input = self.query_one("#user_input").value
        
        if not user_input:
            return
        
        # Voeg bericht toe aan conversatie
        self.add_to_conversation("user", user_input)
        
        # Reset input veld
        self.query_one("#user_input").value = ""
        
        # Controleer of er een actieve sessie is
        if not self.current_session_id:
            # Start nieuwe sessie
            self.start_new_session(user_input)
        else:
            # Verwerk bericht in huidige sessie
            self.process_message(user_input)
    
    def start_new_session(self, initial_query):
        """Start een nieuwe sessie."""
        # In een echte implementatie zou dit een API call naar de backend zijn
        # response = requests.post(f"{self.api_url}/dashboard/sessions/new", json={"topic": initial_query})
        
        # Voor demo doeleinden:
        self.current_session_id = 1
        self.query_one("#session_status").update(f"Actieve sessie: {self.current_session_id}")
        
        # Verwerk het eerste bericht
        self.process_message(initial_query)
    
    def process_message(self, message):
        """Verwerk een bericht met de agents."""
        # In een echte implementatie zou dit een API call naar de backend zijn
        # response = requests.post(
        #     f"{self.api_url}/api/process", 
        #     json={"session_id": self.current_session_id, "query": message}
        # )
        
        # Voor demo doeleinden:
        if "vereisten" in message.lower() or "requirements" in message.lower():
            agent_type = "RequirementRefiner"
            response_text = "Ik begrijp dat je wilt werken aan vereisten. Kun je me vertellen wat het doel is van je project?"
        else:
            agent_type = "WorkflowRefiner"
            response_text = "Hier is een voorgestelde workflow:\n1. Definieer projectdoelen\n2. Identificeer belanghebbenden\n3. Verzamel vereisten\n4. Prioriteer vereisten\n5. Valideer met belanghebbenden"
        
        # Voeg agent antwoord toe aan conversatie
        self.add_to_conversation("agent", f"[{agent_type}] {response_text}")
    
    def add_to_conversation(self, sender, message):
        """Voeg een bericht toe aan de conversatie weergave."""
        # Voeg toe aan geschiedenis
        self.conversation_history.append({"sender": sender, "message": message})
        
        # Update weergave
        conversation_widget = self.query_one("#conversation")
        
        # Bouw conversatie opnieuw op
        conversation_text = ""
        for item in self.conversation_history:
            prefix = "Jij: " if item["sender"] == "user" else "AI: "
            conversation_text += f"{prefix}{item['message']}\n\n"
        
        conversation_widget.update(conversation_text)
    
    def show_notification(self, message):
        """Toon een notificatie aan de gebruiker."""
        # In een volledige implementatie zou dit een popup of toast notification zijn
        self.notify(message)
    
    def action_new_session(self):
        """Start een nieuwe sessie (via keyboard shortcut)."""
        if not self.logged_in:
            return
        
        # Reset huidige sessie
        self.current_session_id = None
        self.conversation_history = []
        self.query_one("#conversation").update("")
        self.query_one("#session_status").update("Geen actieve sessie")
        
        # Toon instructie
        self.show_notification("Type je vraag om een nieuwe sessie te starten")
    
    def action_toggle_help(self):
        """Toon/verberg help informatie."""
        # In een volledige implementatie zou dit een help scherm tonen
        self.show_notification("Help: 'q' om af te sluiten, 'n' voor een nieuwe sessie")

def run_tui():
    """Start de terminal user interface."""
    app = Happy2AlignTUI()
    app.run()

if __name__ == "__main__":
    run_tui()
