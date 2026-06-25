import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Order


class KitchenConsumer(AsyncWebsocketConsumer):
    """
    Staff-facing WebSocket consumer for the kitchen and billing dashboards.

    Group: kitchen_{restaurant_id}

    Incoming event types (server → client):
      new_order             — a customer placed an order
      order_status_changed  — staff changed an order's status
      bill_requested        — customer tapped "Request Bill"
      table_closed          — staff closed the table
    """

    async def connect(self):
        self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.group_name    = f"kitchen_{self.restaurant_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Staff can update order status directly over the WS if they choose."""
        data = json.loads(text_data)
        if data.get('type') == 'status_update':
            await self._update_order_status(data['order_id'], data['status'])
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type':     'order_status_changed',
                    'order_id': data['order_id'],
                    'status':   data['status'],
                }
            )

    @database_sync_to_async
    def _update_order_status(self, order_id, status):
        Order.objects.filter(id=order_id).update(status=status)

    # ── Group message handlers (forward event JSON as-is) ─────────────────
    async def new_order(self, event):
        await self.send(text_data=json.dumps(event))

    async def order_status_changed(self, event):
        await self.send(text_data=json.dumps(event))

    async def bill_requested(self, event):
        await self.send(text_data=json.dumps(event))

    async def table_closed(self, event):
        await self.send(text_data=json.dumps(event))


class OrderConsumer(AsyncWebsocketConsumer):
    """
    Customer-facing WebSocket consumer subscribed to a single order.
    Used on the confirmation page to show live status updates.

    Group: order_{order_id}
    """

    async def connect(self):
        self.order_id   = self.scope['url_route']['kwargs']['order_id']
        self.group_name = f"order_{self.order_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass  # customers do not send messages

    async def order_status_changed(self, event):
        await self.send(text_data=json.dumps(event))
