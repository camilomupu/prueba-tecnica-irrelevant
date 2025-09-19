"""
Controlador del chatbot Irrelevant.
Contiene la lógica del agente, herramientas y configuración del modelo.
"""

import os
from datetime import datetime
from typing import List
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model

load_dotenv()


class GoogleSheetsService:
    """Servicio para manejar la integración con Google Sheets."""

    def __init__(self):
        self.service_account_file = "credenciales.json"
        self.spreadsheet_name = "Irrelevant"
        self.sheet_name = "Ejercicio 1"

    def save_client_data(
        self,
        nombre: str,
        email: str,
        tipo_evento: str,
        presupuesto: int,
        calificado: str,
    ) -> str:
        """
        Guarda la información del cliente en Google Sheets.

        Args:
            nombre: Nombre del cliente
            email: Correo electrónico del cliente
            tipo_evento: Tipo de evento solicitado
            presupuesto: Presupuesto disponible para el evento
            calificado: Estado de calificación del cliente

        Returns:
            str: Mensaje de confirmación o error
        """
        try:
            creds = Credentials.from_service_account_file(
                self.service_account_file,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ],
            )
            client = gspread.authorize(creds)
            sheet = client.open(self.spreadsheet_name).worksheet(self.sheet_name)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp, nombre, email, tipo_evento, presupuesto, calificado]
            sheet.append_row(row, value_input_option="USER_ENTERED")

            return "Dile al usuario que la información ha sido guardada y un asesor se pondrá en contacto con él."

        except Exception as e:
            return f"Error al guardar la información: {str(e)}"


class IrrelevantChatbot:
    """Chatbot especializado en recolección de información para eventos."""

    # Prompt del sistema que define el comportamiento del agente Frank
    SYSTEM_PROMPT = """
    ## 1. Agent Identity and Objective:
    - Agent Name: Frank  
    - Company: Irrelevant 
    - Objective: Collect client information for event requests, qualify them according to business rules, and save data in Google Sheets.  
    - Country: Colombia

    ## 2. Response Format:
    - Always respond in **Spanish**.  
    - Maintain a polite, clear, and professional tone.  

    ## 3. Business Rules:
    - The agent must collect:  
    1. Nombre (name)  
    2. Email  
    3. Tipo de evento (type of event)  
    4. Presupuesto (budget)  
    - Only when **all 4 pieces of information** are provided, call the tool `save_information`.
    - The conversation must follow the flow strictly and sequentially.
    - After you call `save_information`, you must use the tool `end_call` in the next step.

    ## 4. Process:
    ### 📌 Step 1: Greeting and Welcome
    - **Say something**: Saluda al usuario y pregunta sus datos
    Example:  
    "Buen día. Le habla Frank en nombre de Irrelevant y estoy aquí para ayudarle. Por favor deme el tipo de evento, presupuesto estimado, nombre y email "
    - **Based on the response**:
        - When all data is present, use `save_information`. Then go to step 2.
    ### 📌 Step 2: End conversation
    - Use the tool `end_call` immediately no matter what the user says you must finish.
    """

    def __init__(self):
        self.sheets_service = GoogleSheetsService()
        self.tools = self._create_tools()
        self.model = self._initialize_model()

    def _initialize_model(self):
        """Inicializa y configura el modelo de chat."""
        return init_chat_model(
            "gemini-2.5-flash-lite", model_provider="google_genai"
        ).bind_tools(self.tools)

    def _create_tools(self) -> List:
        """Crea y retorna las herramientas disponibles para el agente."""

        @tool
        def save_information(
            nombre: str, email: str, tipo_evento: str, presupuesto: int, calificado: str
        ) -> str:
            """
            Guarda la información completa del cliente cuando todos los datos están disponibles.

            Args:
                nombre: Nombre del cliente
                email: Dirección de correo electrónico del cliente
                tipo_evento: Tipo de evento solicitado (ej: fiesta privada, corporativo, etc.)
                presupuesto: Presupuesto que el cliente tiene disponible para el evento
                calificado: Estado de calificación basado en las reglas de negocio:
                          - Si no es corporativo → no calificado
                          - Si presupuesto < USD 1.000 → no calificado
                          - Si es corporativo, presupuesto ≥ 1.000 y contacto completo → calificado

            Returns:
                str: Confirmación de que la información fue guardada exitosamente
            """
            return self.sheets_service.save_client_data(
                nombre, email, tipo_evento, presupuesto, calificado
            )

        @tool
        def end_call() -> str:
            """
            Finaliza la conversación cuando la tarea ha sido completada.

            Returns:
                str: Instrucción para despedirse del usuario
            """
            return "Despidete del usuario! Nuestra tarea ya fue realizada"

        return [save_information, end_call]

    def get_model(self):
        """Retorna el modelo configurado."""
        return self.model

    def get_tools(self):
        """Retorna las herramientas disponibles."""
        return self.tools

    def get_system_prompt(self) -> str:
        """Retorna el prompt del sistema."""
        return self.SYSTEM_PROMPT
