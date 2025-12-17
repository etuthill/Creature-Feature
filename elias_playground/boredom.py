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
        decay_range: Tuple[int, int] = (1, 3)
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

    def start(self):
        """
        Start the asynchronous boredom decay loop.
        """
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._boredom_timer())

    def stop(self):
        """
        Stop the boredom decay loop (sync-safe).
        """
        self._running = False
        if self._task:
            self._task.cancel()

    async def shutdown(self):
        """
        ctrl c shutdown
        """
        self._running = False

        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
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
        """
        Internal async loop to gradually decrease boredom over time.
        """
        try:
            while self._running:
                await asyncio.sleep(random.uniform(*self.decay_range))

                if self.playing:
                    continue

                if not self.machineIdle:
                    continue

                # skip first tick
                if self._skip_next_tick:
                    self._skip_next_tick = False
                    continue

                if self.boredom > 0:
                    self.boredom -= 1
                    print(f"Boredom decreased to {self.boredom}")
                    try:
                        self.client.publish(self.topic, str(self.boredom))
                    except Exception as e:
                        print("MQTT publish failed:", e)

        except asyncio.CancelledError:
            pass
        finally:
            print("Boredom timer exited")

    def pause(self):
        self.machineIdle = False

    def resume(self):
        self.machineIdle = True
