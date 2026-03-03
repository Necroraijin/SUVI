"""Google Cloud Pub/Sub service for inter-agent communication."""

import os
import json
from typing import Optional, Any
from google.cloud import pubsub_v1
from google.api_core.exceptions import NotFound, GoogleAPIError


class PubSubService:
    """Pub/Sub service for inter-agent communication and event streaming."""

    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.environ.get("GCP_PROJECT", "suvi-project")
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()

    def publish_message(
        self,
        topic: str,
        message: dict[str, Any],
        attributes: Optional[dict[str, str]] = None
    ) -> str:
        """
        Publish a message to a Pub/Sub topic.

        Args:
            topic: The topic name (without projects/ prefix)
            message: The message data as a dictionary
            attributes: Optional message attributes

        Returns:
            The message ID if successful
        """
        try:
            topic_path = self.publisher.topic_path(self.project_id, topic)
            message_bytes = json.dumps(message).encode("utf-8")

            future = self.publisher.publish(
                topic_path,
                message_bytes,
                **(attributes or {})
            )
            message_id = future.result()

            print(f"[PubSub] Published to {topic}: {message_id}")
            return message_id

        except GoogleAPIError as e:
            print(f"[PubSub] Error publishing to {topic}: {e}")
            return ""

    def subscribe(self, subscription: str, callback):
        """
        Subscribe to a Pub/Sub subscription.

        Args:
            subscription: The subscription name
            callback: Async callback function to handle messages
        """
        try:
            subscription_path = self.subscriber.subscription_path(
                self.project_id, subscription
            )

            future = self.subscriber.subscribe(
                subscription_path,
                callback=callback
            )

            print(f"[PubSub] Subscribed to {subscription}")
            return future

        except NotFound:
            print(f"[PubSub] Subscription {subscription} not found")
            return None
        except GoogleAPIError as e:
            print(f"[PubSub] Error subscribing to {subscription}: {e}")
            return None

    def create_topic(self, topic: str) -> bool:
        """Create a Pub/Sub topic if it doesn't exist."""
        try:
            topic_path = self.publisher.topic_path(self.project_id, topic)
            self.publisher.create_topic(request={"name": topic_path})
            print(f"[PubSub] Created topic: {topic}")
            return True
        except GoogleAPIError:
            # Topic may already exist
            return True

    def create_subscription(
        self,
        subscription: str,
        topic: str,
        retry_policy: Optional[dict] = None
    ) -> bool:
        """Create a Pub/Sub subscription."""
        try:
            subscription_path = self.subscriber.subscription_path(
                self.project_id, subscription
            )
            topic_path = self.publisher.topic_path(self.project_id, topic)

            config = {
                "topic": topic_path,
                "retry_policy": retry_policy or {
                    "minimum_backoff": {"seconds": 10},
                    "maximum_backoff": {"seconds": 600}
                }
            }

            self.subscriber.create_subscription(
                request={"name": subscription_path, **config}
            )
            print(f"[PubSub] Created subscription: {subscription}")
            return True

        except GoogleAPIError as e:
            print(f"[PubSub] Error creating subscription {subscription}: {e}")
            return False


# Convenience functions for common SUVI topics
def publish_action_event(action_data: dict):
    """Publish an action event to the actions topic."""
    service = PubSubService()
    service.publish_message("suvi-actions", action_data)


def publish_agent_event(agent_data: dict):
    """Publish an agent event to the agents topic."""
    service = PubSubService()
    service.publish_message("suvi-agents", agent_data)


def publish_telemetry_event(telemetry_data: dict):
    """Publish a telemetry event."""
    service = PubSubService()
    service.publish_message("suvi-telemetry", telemetry_data)
