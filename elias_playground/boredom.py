import asyncio
import random
from typing import Tuple


class Boredom:
    """
    Class to track and manage a "boredom" state.

    Attributes:
        client: MQTT client used to publish boredom updates.
        topic: MQTT topic string for publishing boredom values.
        start_value: Initial boredom value after reset.
        bored_threshold: Value at or below which the machine is considered bored.
        decay_range: Tuple indicating min and max seconds between boredom decay ticks.
        boredom: Current boredom value.
        playing: Whether the machine is currently playing.
        played_event: Whether a play event has completed.
    """

    def __init__(
        self,
        mqtt_client,
        topic: str = "anim/boredom",
        start_value: int = 17,
        bored_threshold: int = 8,
        decay_range: Tuple[int, int] = (1, 3)
    ):
        """
        Initialize boredom tracker.

        Args:
            mqtt_client: MQTT client for publishing updates.
            topic: MQTT topic string.
            start_value: Boredom value after reset.
            bored_threshold: Threshold below which boredom is triggered.
            decay_range: Random time range (seconds) between boredom decay ticks.
        """
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
        Stop the boredom decay loop and cancel the async task.
        """
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def reset(self):
        """
        Reset boredom to starting value and clear play.
        """
        self.boredom = self.start_value
        self.playing = False
        self.played_event = False

    def on_play(self):
        """
        Markplaying.
        """
        self.playing = True

    def on_played(self):
        """
        Mark play as completed and reset boredom to starting value.
        """
        self.playing = False
        self.played_event = True
        self.boredom = self.start_value

    @property
    def is_bored(self) -> bool:
        """
        Check if the current boredom has reached or passed the threshold.

        Returns:
            True if boredom <= bored_threshold, else False.
        """
        return self.boredom <= self.bored_threshold

    async def _boredom_timer(self):
        """
        Internal async loop to gradually decrease boredom over time.

        Publishes boredom value to MQTT topic after each decrement.
        Skips decay if machine is currently playing.
        """
        while self._running:
            await asyncio.sleep(random.uniform(*self.decay_range))

            if self.playing:
                continue

            if not self.machineIdle:
                continue

            # skip first tick (start at actual full hunger)
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

    def on_message(self, client, userdata, msg):
        text = msg.payload.decode()
        
        # Machine idle
        if text == "machineIdle":
            self.machineIdle = True
            print("MachineIdle to idle")
        elif text != None:
            self.machineIdle = False
            print("MachineIdle to active")
