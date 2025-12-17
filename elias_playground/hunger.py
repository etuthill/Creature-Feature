import asyncio
import random


class Hunger:
    """
    Represents the hunger need system.
    """

    def __init__(
        self,
        mqtt_client,
        topic: str = "anim/hunger",
        start_value: int = 17,
        hungry_threshold: int = 8,
        decay_range: tuple[float, float] = (1, 3),
    ):
        self.client = mqtt_client
        self.topic = topic
        self.start_value = start_value

        self.hungry_threshold = hungry_threshold
        self.decay_range = decay_range

        self.hunger = start_value
        self.eating = False
        self.ate_event = False

        self._task: asyncio.Task | None = None
        self._running = False
        self._skip_next_tick = True

        self.machineIdle = True

    def start(self) -> None:
        """Start the hunger decay loop if it is not already running."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._hunger_timer())

    def stop(self) -> None:
        """Stop the hunger decay loop (sync-safe)."""
        self._running = False
        if self._task:
            self._task.cancel()

    # 🔹 ADDED: async shutdown for Ctrl-C
    async def shutdown(self) -> None:
        """Gracefully shut down the hunger task."""
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
        """
        Asynchronous loop that decreases hunger over time.
        """
        try:
            while self._running:
                await asyncio.sleep(random.uniform(*self.decay_range))

                # skip decay while eating
                if self.eating:
                    continue

                if not self.machineIdle:
                    continue

                # skip first tick
                if self._skip_next_tick:
                    self._skip_next_tick = False
                    continue

                if self.hunger > 0:
                    self.hunger -= 1
                    print(f"Hunger decreased to {self.hunger}")
                    try:
                        self.client.publish(self.topic, str(self.hunger))
                    except Exception as e:
                        print("MQTT publish failed", e)

        except asyncio.CancelledError:
            pass
        finally:
            print("Hunger timer exited")

    def pause(self):
        self.machineIdle = False

    def resume(self):
        self.machineIdle = True
