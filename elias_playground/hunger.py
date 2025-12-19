import asyncio
import random


class Hunger:
    """
    Represents the hunger need system.
    """

    def __init__(
            self, mqtt_client, topic: str = "anim/hunger", start_value: int = 17,
                 hungry_threshold: int = 8, decay_range: tuple[float, float] = (5, 10)):
        self.client = mqtt_client
        self.topic = topic
        self.start_value = start_value

        self.hungry_threshold = hungry_threshold
        self.decay_range = decay_range

        self.hunger = start_value
        self.eating = False
        self.ate_event = False

        self._task = None
        self._running = False
        self._skip_next_tick = True

        self.machineIdle = True

        self.client.message_callback_add("system/shutdown", self._on_shutdown_message)
        self.client.subscribe("system/shutdown")

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._hunger_timer())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def shutdown(self) -> None:
        """Stop the hunger timer cleanly."""
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    def reset(self) -> None:
        self.hunger = self.start_value
        self.eating = False
        self.ate_event = False

    def on_eat(self) -> None:
        self.eating = True

    def on_ate(self) -> None:
        self.eating = False
        self.ate_event = True
        self.hunger = self.start_value

    @property
    def is_hungry(self) -> bool:
        return self.hunger <= self.hungry_threshold

    async def _hunger_timer(self) -> None:
        while self._running:
            await asyncio.sleep(random.uniform(*self.decay_range))

            if self.eating:
                continue

            if not self.machineIdle:
                continue

            if getattr(self, "_skip_next_tick", False):
                self._skip_next_tick = False
                continue

            if self.hunger > 0:
                self.hunger -= 1
                print(f"Hunger decreased to {self.hunger}")
                try:
                    self.client.publish(self.topic, str(self.hunger))
                except Exception as e:
                    print("MQTT publish failed", e)

    def pause(self):
        self.machineIdle = False

    def resume(self):
        self.machineIdle = True

    def _on_shutdown_message(self, client, userdata, msg):
        if msg.payload.decode().upper() == "STOP":
            print("Hunger received shutdown command")
            asyncio.create_task(self.shutdown())
