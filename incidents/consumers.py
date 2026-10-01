"""WebSocket consumers (ARCHITECTURE.md §3.6)."""

from channels.generic.websocket import AsyncJsonWebsocketConsumer


def incident_group_name(incident_id) -> str:
    return f"incident_{incident_id}"


class IncidentConsumer(AsyncJsonWebsocketConsumer):
    """Pushes status changes and new RCA reports for one incident to subscribed clients."""

    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close(code=4401)
            return
        self.group_name = incident_group_name(self.scope["url_route"]["kwargs"]["incident_id"])
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def incident_update(self, event):
        """Handler for group messages sent with {"type": "incident.update", "data": ...}."""
        await self.send_json(event["data"])
