import asyncio

button_pressed = asyncio.Event()

async def check_button_async():
    while True:
        # Simulate checking for a button press
        user_input = await asyncio.to_thread(input, "Press 'b' to simulate button press: ")
        if user_input == 'b':
            button_pressed.set() # Set the event
            print("Button pressed!")
        await asyncio.sleep(0.1)

async def move_character_async():
    x_pos = 0
    while True:
        if button_pressed.is_set():
            print(f"Character moved to {x_pos} and button was pressed.")
            button_pressed.clear() # Clear the event
        else:
            print(f"Character moving... current position: {x_pos}")
        x_pos += 1
        await asyncio.sleep(0.5)

async def main():
    await asyncio.gather(check_button_async(), move_character_async())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program terminated.")