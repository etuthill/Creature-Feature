"""
State controller handles serial communication with arduino
and mqtt messaging for state changes
"""

import serial
import paho.mqtt.client as mqtt


class StateController:
    """Finite State Machine (FSM) controller.

    Reads sensor input from Arduino via serial, determines state,
    publishes state updates over MQTT, and handles reset.

    Attributes:
        client (mqtt.Client): MQTT client used to publish FSM state updates.
        ser (serial.Serial): Serial connection to Arduino for non-blocking reads.
        lastState (str | None): Last published FSM state, used to avoid duplicates.
        currentState (str): Current FSM state.
    """

    def __init__(self) -> None:
        """
        Initialize the StateController.

        Sets up MQTT client, connects to local broker, starts the MQTT loop,
        and initializes serial communication and FSM state tracking.
        """
        self.client = mqtt.Client() # MQTT client used to publish fsm state updates
        self.client.on_connect = self.on_connect # callback when mqtt connects
        self.client.connect("localhost") # connect to local 
        self.client.loop_start() # start mqtt loop in background thread
        self.client.on_message = self.on_message # start message reading

        # serial connection to arduino non blocking read
        self.ser = serial.Serial('/dev/ttyACM0', baudrate=9600, timeout=0.1)

        # previous published state used to avoid duplicates
        self.lastState = None

        # starting fsm state
        self.currentState = "machineIdle"

    def loop(self) -> None:
        """
        Perform one iteration of the FSM loop.

        Reads a line from Arduino over serial, determines the FSM state
        based on input, and publishes the state to MQTT only if it has changed.
        """
        # read a line from arduino over serial
        line = self.ser.readline().decode(errors="ignore").strip()

        # holds the state message to publish
        message = None

        # sensors report idle
        if line == "hi":
            message = "machineIdle"
        elif line == "fi":
            message = "machineIdle"

        # sensing transitions
        elif line == "ih":  # idle to sensing (hall)
            message = "sensingH"
        elif line == "if":  # idle to sensing (FSR)
            message = "sensingF"
        elif line == "he":  # hall sensor to sensing
            message = "sensing"
        elif line == "fp":  # FSR sensor to sensing
            message = "sensing"

        # reacting transitions
        elif line == "ef":  # eat to fed
            message = "reactingF"
        elif line == "pp":  # play to played
            message = "reactingP"

        # Done transitions
        elif line == "ed":  # eat to done
            self.client.publish("reset/text", "hunger")
            message = "machineIdle"
        elif line == "pd":  # play to done
            self.client.publish("reset/text", "boredom")
            message = "machineIdle"


        if message is not None and message != self.lastState:
            self.client.publish("state/text", message)
            print(f"fsm -> {message}")

            # send to arduino
            if message == "machineIdle":
                self.ser.write(b"S:i\n")
            elif message in ("sensingH", "sensingF", "sensing"):
                self.ser.write(b"S:h\n")
            elif message in ("reactingF", "reactingP"):
                self.ser.write(b"S:r\n")

            self.lastState = message
            
    def handle_reset(self) -> None:
        self.lastState = None
        self.currentState = "machineIdle"

        try:
            self.ser.write(b"RESET\n")
            self.ser.write(b"S:i\n")
        except Exception as e:
            print("failed to send reset to arduino", e)

        print("FSM reset complete")

    def reset_machine(self) -> None:
        """
        Reset FSM and notify MQTT subscribers.

        Publishes a RESET message over MQTT and calls handle_reset
        to reset internal FSM state and notify the Arduino.
        """
        print("fsm -> reset")
        self.client.publish("state/text", "RESET")
        self.handle_reset()
        
    def on_connect(self, client: mqtt.Client, userdata, flags, rc: int) -> None:
        """
        Callback when MQTT connects to broker.

        Subscribes to FSM state topic.

        Args:
            client (mqtt.Client): The MQTT client instance.
            userdata: User-defined data (unused).
            flags: Response flags from the broker.
            rc (int): Connection result code.
        """
        print("FSM connected to MQTT")
        client.subscribe("state/text")
        client.subscribe("anim/hunger")
        client.subscribe("anim/boredom")

    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
        """
        Callback when an MQTT message is received.

        If the message is "RESET", the FSM is reset.

        Args:
            client (mqtt.Client): The MQTT client instance.
            userdata: User-defined data (unused).
            msg (mqtt.MQTTMessage): Incoming MQTT message.
        """
        text = msg.payload.decode()
        #if msg.topic == "anim/hunger", pass
        if msg.topic == "anim/hunger":
            self.ser.write(b'D:h\n')
        if msg.topic == "anim/boredom":
            self.ser.write(b'D:f\n')

        if text == "RESET":
            print("FSM received RESET")
            self.handle_reset()
        


if __name__ == "__main__":
    fsm = StateController()

    try:
        while True:
            fsm.loop()
    except KeyboardInterrupt:
        print("FSM stopped")
