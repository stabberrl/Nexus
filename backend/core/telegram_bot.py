"""
Nexus AI - Telegram Bot Integration
Escucha mensajes de Telegram y los procesa con NexusAgent.
Ejecución independiente: python -m backend.core.telegram_bot --token TOKEN
"""

import argparse
import asyncio
import os
from typing import Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
DEFAULT_MODEL = "llama3.2"


class NexusTelegramBot:
    """Puente entre Telegram y NexusAgent."""

    def __init__(self, token: str, model: str = DEFAULT_MODEL):
        self.token = token
        self.model = model
        self._agent = None

    def _get_agent(self):
        """Importa e inicializa NexusAgent bajo demanda (lazy)."""
        if self._agent is None:
            from backend.core.agent import NexusAgent
            self._agent = NexusAgent(model=self.model)
        return self._agent

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Responde al comando /start."""
        await update.message.reply_text(
            "¡Hola! Soy Nexus, tu asistente de IA local.\n\n"
            "Puedes preguntarme cualquier cosa: "
            "controlar tu PC, buscar en internet, ejecutar código, "
            "crear documentos y más.\n\n"
            "Comandos disponibles:\n"
            "/start - Mostrar este mensaje\n"
            "/clear - Limpiar el historial de la conversación\n"
            "/help - Mostrar ayuda"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Responde al comando /help."""
        await update.message.reply_text(
            "Soy Nexus, tu asistente personal con IA local.\n\n"
            "Puedo:\n"
            "• Controlar tu PC (abrir apps, ejecutar comandos)\n"
            "• Buscar en internet\n"
            "• Ejecutar código Python\n"
            "• Crear documentos Word, Excel, PowerPoint\n"
            "• Responder preguntas y mantener conversaciones\n\n"
            "Comandos:\n"
            "/start - Mensaje de bienvenida\n"
            "/clear - Limpiar historial\n"
            "/help - Esta ayuda"
        )

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Limpia el historial de la sesión."""
        agent = self._get_agent()
        session_id = f"telegram_{update.effective_user.id}"
        agent.set_session(session_id)
        agent.clear_history()
        await update.message.reply_text("Historial limpiado. Empezamos de nuevo.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa un mensaje de texto con NexusAgent."""
        user_text = update.message.text.strip()
        if not user_text:
            return

        user_id = update.effective_user.id
        session_id = f"telegram_{user_id}"

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        try:
            agent = self._get_agent()
            agent.set_session(session_id)
            response = await agent.chat(user_text)

            # Telegram tiene límite de 4096 caracteres por mensaje
            if len(response) > 4000:
                for i in range(0, len(response), 4000):
                    chunk = response[i:i + 4000]
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(response)

        except Exception as e:
            await update.message.reply_text(f"Error interno: {str(e)}")

    async def handle_error(self, update: Optional[Update], context: ContextTypes.DEFAULT_TYPE):
        """Maneja errores del bot."""
        print(f"[Telegram] Error: {context.error}")

    async def run(self):
        """Inicia el bot de Telegram."""
        app = Application.builder().token(self.token).build()

        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("clear", self.clear_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        app.add_error_handler(self.handle_error)

        print(f"[Telegram] Bot iniciado. Presiona Ctrl+C para detener.")
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()


def main():
    parser = argparse.ArgumentParser(description="Nexus AI - Telegram Bot")
    parser.add_argument("--token", help="Token del bot de Telegram")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Modelo Ollama a usar")
    args = parser.parse_args()

    token = args.token or os.environ.get(BOT_TOKEN_ENV)
    if not token:
        print("Error: Debes proporcionar un token via --token o variable TELEGRAM_BOT_TOKEN")
        print("Ejemplo: python -m backend.core.telegram_bot --token 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        exit(1)

    bot = NexusTelegramBot(token=token, model=args.model)
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
