import base64
import hashlib
import hmac
import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent, TextMessageContent

try:
    from openai import OpenAI
except ImportError as exc:
    raise ImportError(
        "The 'openai' package is required to run this bot. "
        "Add it to your requirements.txt and install it via pip."
    ) from exc


def is_chinese(text: str) -> bool:
    """Return True if the given text contains any CJK (Chinese) characters."""
    for char in text:
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF:
            return True
    return False


def get_openai_client(api_key: str) -> OpenAI:
    """Instantiate an OpenAI client with the given API key."""
    return OpenAI(api_key=api_key)


class TranslatorBot:
    """A LINE bot that performs on‑the‑fly translation using OpenAI."""

    def __init__(self, channel_secret: str, channel_access_token: str, openai_api_key: str, model_name: str = "o1"):
        if not channel_secret:
            print("Specify LINE_CHANNEL_SECRET as environment variable.", file=sys.stderr)
            sys.exit(1)
        if not channel_access_token:
            print("Specify LINE_CHANNEL_ACCESS_TOKEN or LINE_ACCESS_TOKEN as environment variable.", file=sys.stderr)
            sys.exit(1)
        if not openai_api_key:
            print("Specify OPENAI_API_KEY as environment variable.", file=sys.stderr)
            sys.exit(1)

        self.channel_secret = channel_secret
        self.configuration = Configuration(access_token=channel_access_token)
        self.parser = WebhookParser(channel_secret)
        self.openai_client = get_openai_client(openai_api_key)
        self.model_name = model_name or "o1"

    def translate_message(self, message_text: str) -> str:
        if is_chinese(message_text):
            system_prompt = (
                "You are a professional translator. Translate the provided text from "
                "Traditional Chinese into natural, fluent English. Preserve names and "
                "technical terms. Return only the translation without additional commentary."
            )
        else:
            system_prompt = (
                "You are a professional translator. Translate the provided text from "
                "English into natural, fluent Traditional Chinese. Preserve names and "
                "technical terms. Return only the translation without additional commentary."
            )

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message_text},
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            print(f"OpenAI translation error: {exc}", file=sys.stderr)
            return "發生錯誤，無法翻譯此訊息。 (An error has occurred; this message cannot be translated.)"

    def handle_events(self, events):
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                translation = self.translate_message(event.message.text)
                with ApiClient(self.configuration) as api_client:
                    messaging_api = MessagingApi(api_client)
                    messaging_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=translation)],
                        )
                    )


def create_app() -> Flask:
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or os.getenv("LINE_ACCESS_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL", "gpt-4.1")

    bot = TranslatorBot(channel_secret, access_token, openai_api_key, model_name)
    app = Flask(__name__)

    @app.route("/callback", methods=["POST"])
    def callback():
        signature = request.headers.get("X-Line-Signature", "")
        body = request.get_data(as_text=True)

        hash_bytes = hmac.new(bot.channel_secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
        computed_signature = base64.b64encode(hash_bytes).decode()
        if signature != computed_signature:
            abort(400)

        try:
            events = bot.parser.parse(body, signature)
        except InvalidSignatureError:
            abort(400)

        bot.handle_events(events)
        return "OK"

    return app


if __name__ == "__main__":
    parser = ArgumentParser(
        usage="python translation_bot.py [--port <port>] [--debug]",
        description="Run the LINE translator bot locally.",
    )
    parser.add_argument("-p", "--port", type=int, default=8000, help="port to listen on")
    parser.add_argument("-d", "--debug", action="store_true", help="enable debug mode")
    args = parser.parse_args()

    app = create_app()
    app.run(host="0.0.0.0", port=args.port, debug=args.debug, threaded=True)
