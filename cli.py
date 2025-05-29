"""
Terminal interface voor Happy 2 Align
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Button, Static, Select
from textual.binding import Binding
import asyncio
import json
import httpx
from typing import Dict, Any

class MessageList(Static):
    """Een aangepaste Static widget voor het tonen van berichten."""
    
    DEFAULT_CSS = """
    MessageList {
        height: 100%;
        overflow-y: scroll;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.messages = []
    
    def add_message(self, sender: str, message: str, color: str = "white"):
        """Voeg een bericht toe aan de lijst."""
        self.messages.append((sender, message, color))
        self.update(self._format_messages())
    
    def _format_messages(self) -> str:
        """Formatteer alle berichten voor weergave."""
        return "\n\n".join(
            f"[bold {color}]{sender}:[/] {message}"
            for sender, message, color in self.messages
        )

class Happy2AlignApp(App):
    """De hoofdapplicatie voor de Happy 2 Align terminal interface."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    #chat-container {
        width: 90%;
        height: 80%;
        border: solid green;
    }
    
    #input-container {
        width: 90%;
        height: 20%;
        dock: bottom;
    }
    
    .message {
        margin: 1;
        padding: 1;
        border: solid green;
    }
    
    .user-message {
        background: #1a1a1a;
    }
    
    .agent-message {
        background: #2a2a2a;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("enter", "send_message", "Send", show=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.context: Dict[str, Any] = {}
        self.client = httpx.AsyncClient(base_url="http://localhost:8000")
    
    def compose(self) -> ComposeResult:
        """Creëer de UI componenten."""
        yield Header()
        with Container():
            with Vertical():
                yield Static("Welkom bij Happy 2 Align!", id="welcome")
                with Container(id="chat-container"):
                    yield MessageList()
                with Container(id="input-container"):
                    yield Input(placeholder="Type je bericht hier...", id="message-input")
                    yield Button("Verstuur", id="send-button")
        yield Footer()
    
    async def on_mount(self) -> None:
        """Start de applicatie."""
        self.title = "Happy 2 Align"
        self.sub_title = "Je AI Requirements Assistant"
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handel button clicks af."""
        if event.button.id == "send-button":
            await self.send_message()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handel input submissions af."""
        await self.send_message()
    
    async def send_message(self) -> None:
        """Verstuur een bericht naar de API en toon de response."""
        input_widget = self.query_one("#message-input", Input)
        message = input_widget.value.strip()
        
        if not message:
            return
        
        # Toon gebruikersbericht
        message_list = self.query_one(MessageList)
        message_list.add_message("Jij", message, "green")
        
        # Verstuur naar API
        try:
            response = await self.client.post(
                "/process",
                json={"message": message, "context": self.context}
            )
            response_data = response.json()
            
            # Update context
            self.context = response_data.get("context", {})
            
            # Toon agent response
            message_list.add_message("Assistant", response_data["response"], "blue")
            
        except Exception as e:
            message_list.add_message("Error", f"Er is een fout opgetreden: {str(e)}", "red")
        
        # Reset input
        input_widget.value = ""

if __name__ == "__main__":
    app = Happy2AlignApp()
    app.run() 