from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from tweetgrambot.app.core.account_manager import AccountManager


LLM_OPTIONS: dict[str, dict[str, object]] = {
    "openai": {
        "label": "OpenAI",
        "models": ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
    },
    "anthropic": {
        "label": "Anthropic",
        "models": ["claude-3-5-haiku-latest", "claude-3-5-sonnet-latest"],
    },
    "gemini": {
        "label": "Gemini",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
    },
    "groq": {
        "label": "Groq",
        "models": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"],
    },
    "deepseek": {
        "label": "DeepSeek",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "openrouter": {
        "label": "OpenRouter",
        "models": ["openai/gpt-4o-mini", "anthropic/claude-3.5-haiku"],
    },
    "huggingface": {
        "label": "Hugging Face",
        "models": ["meta-llama/Llama-3.1-8B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"],
    },
}


class LlmCommandHandler:
    def __init__(self, manager: AccountManager) -> None:
        self.manager = manager

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()
        parts = query.data.split(":")
        if len(parts) < 4 or parts[0] != "llm":
            return

        action = parts[1]
        if action == "provider" and len(parts) == 4:
            account_id = parts[2]
            provider = parts[3]
            if provider not in LLM_OPTIONS:
                await query.edit_message_text("Unsupported LLM provider.")
                return
            await query.edit_message_text(
                f"Choose model for {account_id} / {self.provider_label(provider)}:",
                reply_markup=self.model_keyboard(account_id, provider),
            )
            return

        if action == "model" and len(parts) == 5:
            account_id = parts[2]
            provider = parts[3]
            model_index = int(parts[4])
            model = self.models_for(provider)[model_index]
            await self.manager.set_llm_provider_model(account_id, provider, model)
            await query.edit_message_text(f"LLM provider/model set for {account_id}: {provider}/{model}")

    def provider_keyboard(self, account_id: str) -> InlineKeyboardMarkup:
        rows = [
            [
                InlineKeyboardButton(
                    str(option["label"]),
                    callback_data=f"llm:provider:{account_id}:{provider}",
                )
            ]
            for provider, option in LLM_OPTIONS.items()
        ]
        return InlineKeyboardMarkup(rows)

    def model_keyboard(self, account_id: str, provider: str) -> InlineKeyboardMarkup:
        rows = [
            [
                InlineKeyboardButton(
                    model,
                    callback_data=f"llm:model:{account_id}:{provider}:{index}",
                )
            ]
            for index, model in enumerate(self.models_for(provider))
        ]
        return InlineKeyboardMarkup(rows)

    def provider_label(self, provider: str) -> str:
        return str(LLM_OPTIONS[provider]["label"])

    def models_for(self, provider: str) -> list[str]:
        return list(LLM_OPTIONS[provider]["models"])
