import asyncio
import random
from typing import Tuple


class Boredom:
    """
    Class to track and manage a "boredom" state.
    """

    def __init__(
        self,
        mqtt_client,
        topic: str = "anim/boredom",
        start_value: int = 17,
        bored_threshold: int = 8,
        decay_range: Tuple[int, int] = (5, 10)
    ):
        self.client = mqtt_client
        self.topic = topic
        self.start_value = start_value
        self.bored_threshold = bored_threshold
        self.decay_range = decay_range

        self.boredom: int = start_value
        self.playing: bool = False
        self.played_event: bool = False

        self._task: asyncio.Task | None = None
        self._running: bool = False
        self._skip_next_tick = True 

        self.machineIdle = True

        # --- ADDED: subscribe to shutdown topic ---
        self.client.message_callback_add("system/shutdown", self._on_shutdown_message)
        self.client.subscribe("system/shutdown")

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
    def is_bored(self) -> bool:
        return self.boredom <= self.bored_threshold

    async def _boredom_timer(self):
        while self._running:
            await asyncio.sleep(random.uniform(*self.decay_range))

            if self.playing:
                continue

            if not self.machineIdle:
                continue

            if getattr(self, "_skip_next_tick", False):
                self._skip_next_tick = False
                continue

            if self.boredom > 0:
                self.boredom -= 1
                print(f"Boredom decreased to {self.boredom}")
                try:
                    self.client.publish(self.topic, str(self.boredom))
                except Exception as e:
                    print("MQTT publish failed:", e)

    def pause(self):
        self.machineIdle = False

    def resume(self):
        self.machineIdle = True
            
    async def shutdown(self):
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    # --- ADDED: handle shutdown MQTT message ---
    def _on_shutdown_message(self, client, userdata, msg):
        if msg.payload.decode().upper() == "STOP":
            print("Boredom received shutdown command")
            # schedule async shutdown
            asyncio.create_task(self.shutdown())

