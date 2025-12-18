clc 
close all

hall_effect = load("hall_effect_data.csv");
pressure = load("pressure_data.csv");

distance = hall_effect(:, 1);
polarity_1 = hall_effect(:, 2);
polarity_2 = hall_effect(:, 4);

weight = pressure(:, 1);
sensor_reading = pressure(:, 2);

Vref = 5.0;
adc_max = 1023;

polarity_1_adc = polarity_1 / Vref * adc_max;
polarity_2_adc = polarity_2 / Vref * adc_max;
equilibrium_adc = 2.55 / Vref * adc_max;

figure
plot(weight, sensor_reading, "LineWidth", 1.5)
title("Resistive Pressure Sensor Calibration")
xlabel("Weight (g)")
ylabel("Sensor Reading (0-1023)")

figure
plot(distance, polarity_2_adc, "LineWidth", 1.5)
hold on
plot(distance, polarity_1_adc, "LineWidth", 1.5)
yline(equilibrium_adc, "--")
xlabel("Distance (mm)")
ylabel("Sensor Reading (0–1023)")
title("Hall Effect Sensor Calibration (ADC Scale)")
legend("North Side", "South Side", "Equilibrium")
