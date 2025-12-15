import asyncio
import random

class Hunger:
    def __init__(self, mqtt_client, topic="anim/hunger", start_value=17, hungry_threshold=8, decay_range=(1, 3)):
        self.client = mqtt_client
        self.topic = topic
        self.hunger = start_value
        self.playing = False

        self.start_value = start_value
        self.hungry_threshold = hungry_threshold
        self.decay_range = decay_range

        self.hunger = start_value

        self.playing = False
        self.played_event = False

        self._task = None
        self._running = False


    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._hunger_timer())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def reset(self):
        self.hunger = self.start_value
        self.eating = False
        self.ate_event = False

    def on_eat(self):
        """
        Called when eating starts
        """
        self.eating = True

    def on_ate(self):
        """
        Called when eating finishes
        """
        self.eating = False
        self.ate_event = True
        self.hunger = self.start_value

    @property
    def is_hungry(self):
        return self.hunger <= self.hungry_threshold

    async def _hunger_timer(self):
        while True:
            await asyncio.sleep(random.randint(1,3))
            if self.eating:
                continue
            if self.hunger > 0:
                self.hunger -= 1
                print(f"Hunger decreased to {self.hunger}")
                self.client.publish(self.topic, str(self.hunger))
