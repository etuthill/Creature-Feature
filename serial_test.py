import serial

ser = serial.Serial('/dev/ttyACM0')
print(ser.name)
ser.write(b'yeet')

if ser.readline().decode(errors="ignore").strip() == "yote":
    print("yote")
    ser.close()
