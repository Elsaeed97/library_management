import json

from channels.generic.websocket import AsyncWebsocketConsumer


class BookAvailabilityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "book_availability"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def book_available(self, event):
        await self.send(text_data=json.dumps({"message": event["message"]}))
