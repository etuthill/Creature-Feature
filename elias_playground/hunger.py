import asyncio
import random


class Hunger:
    def __init__(self, mqtt_client, topic="anim/hunger", start_value=17, hungry_threshold=8, decay_range=(1,3)):
        
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

    def start(self):
        # start hunger decay loop if not already running
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._hunger_timer())

    def stop(self):
        # stop hunger decay loop
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def reset(self):
        # restore hunger to starting state
        self.hunger = self.start_value
        self.eating = False
        self.ate_event = False

    def on_eat(self):
        # mark machine as currently eating
        self.eating = True

    def on_ate(self):
        # mark eating complete and reset hunger
        self.eating = False
        self.ate_event = True
        self.hunger = self.start_value

    @property
    def is_hungry(self):
        # state - hunger threshold reached
        return self.hunger <= self.hungry_threshold

    async def _hunger_timer(self):
        # decrease hunger over time
        while self._running:
            await asyncio.sleep(random.uniform(*self.decay_range))

            # skip decay while eating
            if self.eating:
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
