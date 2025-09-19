"""
Controlador del grafo de conversación.
Maneja el flujo de estados, nodos y transiciones de la conversación.
"""

import uuid
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


class AgentState(TypedDict):
    """Estado del agente conversacional."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    finished: bool


class ConversationGraph:
    """Grafo de conversación que maneja el flujo y estados del chatbot."""

    def __init__(self, chatbot):
        self.chatbot = chatbot
        self.memory = MemorySaver()
        self.config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        self.app = self._build_graph()

    def _build_graph(self):
        """Construye y compila el grafo de conversación."""
        graph = StateGraph(AgentState)

        # Agregar nodos
        graph.add_node("check_finished", self._check_finished_node)
        graph.add_node("agent", self._model_call_node)
        graph.add_node("tools", self._tools_node)

        # Configurar punto de entrada
        graph.set_entry_point("check_finished")

        # Configurar transiciones condicionales
        graph.add_conditional_edges(
            "check_finished",
            self._check_finished_condition,
            {
                "finished": END,
                "continue": "agent",
            },
        )

        graph.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END,
            },
        )

        graph.add_edge("tools", "agent")

        return graph.compile(checkpointer=self.memory)

    def _check_finished_node(self, state: AgentState):
        """
        Verifica si la conversación ya ha finalizado.

        Args:
            state: Estado actual del agente

        Returns:
            dict: Estado actualizado si la conversación ha terminado
        """
        if state.get("finished", False):
            return {
                "messages": [
                    SystemMessage(
                        content="No te preocupes, ya registré tus datos. La conversación ha finalizado."
                    )
                ]
            }
        return {}

    def _model_call_node(self, state: AgentState) -> AgentState:
        """
        Nodo que invoca el modelo de lenguaje.

        Args:
            state: Estado actual del agente

        Returns:
            AgentState: Estado actualizado con la respuesta del modelo
        """
        response = self.chatbot.get_model().invoke(
            [SystemMessage(content=self.chatbot.get_system_prompt())]
            + state["messages"]
        )
        return {"messages": [response]}

    def _tools_node(self, state: AgentState):
        """
        Ejecuta las herramientas solicitadas por el modelo.

        Args:
            state: Estado actual del agente

        Returns:
            dict: Estado actualizado con los resultados de las herramientas
        """
        outputs = []
        finished_flag = state.get("finished", False)
        last_msg = state["messages"][-1]

        for tool_call in getattr(last_msg, "tool_calls", []):
            name = tool_call.get("name")
            args = tool_call.get("args", {}) or {}
            tool_id = str(tool_call.get("id", uuid.uuid4()))

            # Buscar y ejecutar la herramienta correspondiente
            for tool in self.chatbot.get_tools():
                if tool.name == name:
                    result = tool.invoke(args)
                    outputs.append(
                        ToolMessage(content=result, name=name, tool_call_id=tool_id)
                    )

                    # Marcar como finalizada si se ejecutó end_call
                    if name == "end_call":
                        finished_flag = True
                    break

        return {"messages": outputs, **({"finished": True} if finished_flag else {})}

    def _check_finished_condition(self, state: AgentState):
        """Determina si la conversación debe continuar o finalizar."""
        return "finished" if state.get("finished", False) else "continue"

    def _should_continue(self, state: AgentState):
        """Determina si debe ejecutar herramientas o finalizar."""
        messages = state["messages"]
        last_message = messages[-1]
        return "continue" if last_message.tool_calls else "end"

    def process_message(self, user_input: str):
        """
        Procesa un mensaje del usuario a través del grafo.

        Args:
            user_input: Mensaje del usuario
        """
        input_message = {"messages": [("user", user_input)]}
        print()  # Línea en blanco antes de cada interacción

        for step in self.app.stream(input_message, self.config, stream_mode="values"):
            last_message = step["messages"][-1]
            self._format_message(last_message)

    def _format_message(self, message):
        """
        Formatea y muestra los mensajes de manera legible.

        Args:
            message: Mensaje a formatear
        """
        if hasattr(message, "type"):
            if message.type == "human":
                print(f"👤 Usuario: {message.content}")
            elif message.type == "ai":
                if hasattr(message, "tool_calls") and message.tool_calls:
                    # Mostrar llamadas a herramientas
                    for tool_call in message.tool_calls:
                        name = tool_call.get("name", "unknown")
                        args = tool_call.get("args", {})

                        print(f"🔧 Tool: {name}(", end="")
                        if args:
                            arg_strs = [
                                f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}"
                                for k, v in args.items()
                            ]
                            print(", ".join(arg_strs), end="")
                        print(")")
                else:
                    print(f"🤖 Frank: {message.content}")
            elif message.type == "tool":
                print(f'📤 Return: "{message.content}"')
            elif message.type == "system":
                print(f"🤖 Sistema: {message.content}")
            else:
                print(f"🔹 {message.type}: {message.content}")
        else:
            print(f"🔸 Mensaje: {message}")
