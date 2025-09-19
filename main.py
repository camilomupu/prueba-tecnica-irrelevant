"""
Punto de entrada principal para el agente conversacional Irrelevant.
Permite ejecutar casos de prueba predefinidos o interactuar manualmente.
"""

from controllers.chatbot import IrrelevantChatbot
from controllers.graph import ConversationGraph


def run_qualified_case():
    """Ejecuta el caso de uso calificado (evento corporativo)."""
    print("🚀 Ejecutando Caso 1: Cliente Calificado")
    print("=" * 50)

    chatbot = IrrelevantChatbot()
    graph = ConversationGraph(chatbot)

    # Primer flujo: saludo y solicitud de información
    graph.process_message("Hola")

    # Segundo flujo: cliente proporciona información completa (calificado)
    graph.process_message(
        "Evento corporativo con presupuesto de 1500 dólares."
        "Me llamo Laura y mi correo es laura@empresa.com"
    )

    graph.process_message("Dale gracias")
    # Intento de continuar conversación (ya ha terminado)
    graph.process_message("Hola")


def run_unqualified_case():
    """Ejecuta el caso de uso no calificado (fiesta privada)."""
    print("🚀 Ejecutando Caso 2: Cliente No Calificado")
    print("=" * 50)

    chatbot = IrrelevantChatbot()
    graph = ConversationGraph(chatbot)

    # Primer flujo: saludo y solicitud de información
    graph.process_message("Hola")

    # Segundo flujo: cliente proporciona información (no calificado)
    graph.process_message(
        "Necesito organizar una fiesta de cumpleaños, tengo 500 dólares de presupuesto."
        "Soy Carlos y mi email es carlos@gmail.com"
    )

    # Finalización de la conversación
    graph.process_message("Perfecto, gracias")


def run_interactive_mode():
    """Permite interacción manual con el chatbot."""
    print("🚀 Modo Interactivo")
    print("=" * 50)
    print("Escribe 'salir' para terminar")
    print()

    chatbot = IrrelevantChatbot()
    graph = ConversationGraph(chatbot)

    while True:
        user_input = input("👤 Tú: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("¡Hasta luego!")
            break

        graph.process_message(user_input)
        print()


def main():
    """Función principal con menú de opciones."""
    print("🤖 Agente Conversacional Irrelevant")
    print("=" * 40)
    print("Selecciona una opción:")
    print("1. Caso de uso calificado")
    print("2. Caso de uso no calificado")
    print("3. Modo interactivo")
    print("=" * 40)

    while True:
        try:
            choice = input("Ingresa tu opción (1, 2 o 3): ").strip()

            if choice == "1":
                run_qualified_case()
                break
            elif choice == "2":
                run_unqualified_case()
                break
            elif choice == "3":
                run_interactive_mode()
                break
            else:
                print("❌ Opción inválida. Por favor ingresa 1, 2 o 3.")
        except KeyboardInterrupt:
            print("\n¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
