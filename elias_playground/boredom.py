import asyncio
import random


class Boredom:
    def __init__(self, mqtt_client, topic="anim/boredom", start_value=17, bored_threshold=8, decay_range=(1,3)):
        
        self.client = mqtt_client  # mqtt client for publishing boredom updates
        self.topic = topic  # mqtt topic for boredom updates
        self.start_value = start_value  # starting boredom value after reset

        self.bored_threshold = bored_threshold  # boredom trigger
        self.decay_range = decay_range  # random time range between boredom decay ticks

        self.boredom = start_value  # current boredom value
        self.playing = False  # indicates whether playing
        self.played_event = False  # completed play event

        self._task = None  # async task reference
        self._running = False  # controls whether boredom timer is running

    def start(self):
        # start boredom decay loop if not already running
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._boredom_timer())

    def stop(self):
        # stop boredom decay loop
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def reset(self):
        # restore boredom to starting state
        self.boredom = self.start_value
        self.playing = False
        self.played_event = False

    def on_play(self):
        # mark machine as currently playing
        self.playing = True

    def on_played(self):
        # mark play complete and reset boredom
        self.playing = False
        self.played_event = True
        self.boredom = self.start_value

    @property
    def is_bored(self):
        # state - boredom threshold reached
        return self.boredom <= self.bored_threshold

    async def _boredom_timer(self):
        # decrease boredom over time
        while self._running:
            await asyncio.sleep(random.uniform(*self.decay_range))

            # skip decay while playing
            if self.playing:
                continue

            # decrease boredom until zero
            if self.boredom > 0:
                self.boredom -= 1
                print(f"Boredom decreased to {self.boredom}")
                try:
                    self.client.publish(self.topic, str(self.boredom))
                except Exception as e:
                    # debug mqtt
                    print("MQTT publish failed", e)
