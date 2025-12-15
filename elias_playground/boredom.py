import asyncio
import random

class Boredom:
    def __init__(self, mqtt_client, topic="anim/boredom", start_value=17, bored_threshold=8, decay_range=(1,3)):
        self.client = mqtt_client
        self.topic = topic
        self.start_value = start_value
        self.bored_threshold = bored_threshold
        self.decay_range = decay_range

        self.boredom = start_value
        self.playing = False
        self.played_event = False

        self._task = None
        self._running = False

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._boredom_timer())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def reset(self):
        self.boredom = self.start_value
        self.playing = False
        self.played_event = False

    def on_play(self):
        self.playing = True

    def on_played(self):
        self.playing = False
        self.played_event = True
        self.boredom = self.start_value

    @property
    def is_bored(self):
        return self.boredom <= self.bored_threshold

    async def _boredom_timer(self):
        while self._running:
            await asyncio.sleep(random.uniform(*self.decay_range))
            if self.playing:
                continue
            if self.boredom > 0:
                self.boredom -= 1
                print(f"Boredom decreased to {self.boredom}")
                try:
                    self.client.publish(self.topic, str(self.boredom))
                except Exception as e:
                    print("MQTT publish failed:", e)
