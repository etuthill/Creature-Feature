import asyncio
import random


class Hunger:
    """
    Represents the hunger need system.

    Handles hunger decay over time, eating events, and publishes updates over MQTT.

    Attributes:
        client (mqtt.Client): MQTT client for publishing hunger updates.
        topic (str): MQTT topic for hunger values.
        start_value (int): Initial hunger value after reset.
        hungry_threshold (int): Value at which the machine is considered hungry.
        decay_range (tuple[float, float]): Range (seconds) for random decay intervals.
        hunger (int): Current hunger value.
        eating (bool): Whether the machine is currently eating.
        ate_event (bool): Flag indicating a completed eating event.
        _task (asyncio.Task | None): Reference to the async decay task.
        _running (bool): Flag indicating whether the decay loop is running.
    """

    def __init__(self, mqtt_client, topic: str = "anim/hunger", start_value: int = 17,
                 hungry_threshold: int = 8, decay_range: tuple[float, float] = (1, 3)):
        """
        Initialize the Hunger system.

        Args:
            mqtt_client (mqtt.Client): MQTT client for publishing updates.
            topic (str, optional): MQTT topic for hunger values. Defaults to "anim/hunger".
            start_value (int, optional): Initial hunger value after reset. Defaults to 17.
            hungry_threshold (int, optional): Threshold below which the machine is hungry. Defaults to 8.
            decay_range (tuple[float, float], optional): Random interval range for hunger decay (seconds). Defaults to (1, 3).
        """
        self.client = mqtt_client # mqtt client for publishing hunger updates
        self.topic = topic # mqtt topic for hunger updates
        self.start_value = start_value # starting hunger value after reset

        self.hungry_threshold = hungry_threshold # hunger trigger
        self.decay_range = decay_range # random time range between hunger decay ticks

        self.hunger = start_value # current hunger value
        self.eating = False # indicates whether eating
        self.ate_event = False # completed eating

        self._task = None # async task reference
        self._running = False # controls whether hunger timer is running
        self._skip_next_tick = True 

        self.machineIdle = True

    def start(self) -> None:
        """Start the hunger decay loop if it is not already running."""
        # start hunger decay loop if not already running
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._hunger_timer())

    def stop(self) -> None:
        """Stop the hunger decay loop if it is running."""
        # stop hunger decay loop
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def reset(self) -> None:
        """Reset hunger to starting value and clear eating state."""
        # restore hunger to starting state
        self.hunger = self.start_value
        self.eating = False
        self.ate_event = False

    def on_eat(self) -> None:
        """Mark the machine as currently eating."""
        # mark machine as currently eating
        self.eating = True

    def on_ate(self) -> None:
        """Mark eating as complete and reset hunger to starting value."""
        # mark eating complete and reset hunger
        self.eating = False
        self.ate_event = True
        self.hunger = self.start_value

    @property
    def is_hungry(self) -> bool:
        """
        Check if the machine is currently hungry.

        Returns:
            bool: True if hunger <= hungry_threshold, else False.
        """
        # state - hunger threshold reached
        return self.hunger <= self.hungry_threshold

    async def _hunger_timer(self) -> None:
        """
        Asynchronous loop that decreases hunger over time.

        - Skips decay while eating.
        - Publishes current hunger value to MQTT after each decay step.
        """
        # decrease hunger over time
        while self._running:
            await asyncio.sleep(random.uniform(*self.decay_range))

            # skip decay while eating
            if self.eating:
                continue

            if not self.machineIdle:
                continue
            
            # skip first tick (start at actual full hunger)
            if getattr(self, "_skip_next_tick", False):
                self._skip_next_tick = False
                continue

            # decrease hunger until zero
            if self.hunger > 0:
                self.hunger -= 1
                print(f"Hunger decreased to {self.hunger}")
                try:
                    self.client.publish(self.topic, str(self.hunger))
                except Exception as e:
                    # debug MQTT
                    print("MQTT publish failed", e)
    
    def on_message(self, client, userdata, msg):
        text = msg.payload.decode()
        
        # Machine idle
        if text == "machineIdle":
            self.machineIdle = True
            print("MachineIdle to idle")
        elif text != None:
            self.machineIdle = False
            print("MachineIdle to active")
                    
