clc 
close all

hall_effect = load("hall_effect_data.csv");
pressure = load("pressure_data.csv");

distance = hall_effect(:, 1);
polarity_1 = hall_effect(:, 2);
polarity_2 = hall_effect(:, 4);

weight = pressure(:, 1);
sensor_reading = pressure(:, 2);

figure
plot(weight, sensor_reading, "LineWidth", 1.5)
title("Resistive Pressure Sensor Calibration")
xlabel("Weight (g)")
ylabel("Sensor Reading (0-1023)")

figure
plot(distance, polarity_2, "LineWidth", 1.5)
hold on
plot(distance, polarity_1, "LineWidth", 1.5)
yline(2.55, "--")
xlabel("Distance (mm)")
ylabel("Sensor Reading (0-1023)")
title("Hall Effect Sensor Calibration")
legend("North Side", "South Side", "Equilibrium")
