# bot/slack_bot.py
import os
import sys
import logging
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000/chat")
SECRET_KEY = os.getenv("SECRET_KEY")

app = App(token=os.getenv("SLACK_BOT_TOKEN"))


@app.event("app_mention")
def handle_mention(event, say):
    """Triggered when someone @mentions the bot in a channel."""
    _process_message(event, say)


@app.event("message")
def handle_direct_message(event, say):
    """Triggered when someone DMs the bot directly."""
    # ignore bot's own messages
    if event.get("bot_id"):
        return
    _process_message(event, say)


def _process_message(event: dict, say) -> None:
    """Core handler — sends message to gateway and replies."""
    user_id = event.get("user", "unknown")
    text = event.get("text", "").strip()

    if not text:
        return

    logger.info(f"Slack message from user={user_id} len={len(text)}")

    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(
                GATEWAY_URL,
                json={"user_id": f"slack_{user_id}", "message": text},
                headers={"x-api-key": SECRET_KEY},
            )

            if response.status_code != 200:
                logger.error(f"Gateway error {response.status_code}: {response.text}")
                say(f"Gateway error ({response.status_code}). Try again.")
                return

            data = response.json()
            reply = data.get("response", "No response from gateway.")
            logger.info(f"Replying to slack user={user_id}")
            say(reply)

    except httpx.ConnectError:
        logger.error(f"Cannot connect to gateway at {GATEWAY_URL}")
        say("Cannot reach the gateway. Is the server running?")
    except httpx.TimeoutException:
        logger.error("Gateway timeout")
        say("Gateway took too long to respond. Try again.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        say("Something went wrong. Try again.")

@app.command("/summarize")


def handle_summarize(ack, command, client, say):
    logger.info(f"Received /summarize command from user={command['user_id']} in channel={command['channel_id']}")   
    """
    /summarize — reads last 20 messages in channel,
    sends to gateway to summarize, replies only visible to you.
    """
    ack()  # must acknowledge within 3 seconds

    user_id = command["user_id"]
    channel_id = command["channel_id"]

    try:
        # fetch last 20 messages from channel
        result = client.conversations_history(
            channel=channel_id,
            limit=20
        )

        messages = result.get("messages", [])
        if not messages:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="No messages found in this channel."
            )
            return

        # format messages into one block of text
        logger.info(f"Processing {len(messages)} messages for summarization.")
        conversation = "\n".join([
            f"{msg.get('user', 'unknown')}: {msg.get('text', '')}"
            for msg in reversed(messages)  # oldest first
            if msg.get("text")
        ])
        
        prompt = f"Please summarize this Slack conversation concisely:\n\n{conversation}"
        logger.info(f"Sending conversation to gateway for summarization (user={user_id})")

        # hit your gateway
        with httpx.Client(timeout=60) as http:
            response = http.post(
                GATEWAY_URL,
                json={
                    "user_id": f"slack_{user_id}",
                    "message": prompt
                },
                headers={"x-api-key": SECRET_KEY},
            )
            summary = response.json().get("response", "Could not summarize.")

        # ephemeral = only YOU see this
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"📋 *Summary (only visible to you):*\n\n{summary}"
        )

    except Exception as e:
        logger.error(f"Summarize error: {str(e)}")
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="Something went wrong while summarizing."
        )


if __name__ == "__main__":
    app_token = os.getenv("SLACK_APP_TOKEN")
    if not app_token:
        raise ValueError("SLACK_APP_TOKEN not set in .env")

    logger.info("Starting Slack bot via Socket Mode...")
    SocketModeHandler(app, app_token).start()