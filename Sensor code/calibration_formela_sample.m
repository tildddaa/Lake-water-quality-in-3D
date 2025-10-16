% calibration:

voltage = [4.2, 3.8, 3.5, 3.1, 2.8, 2.5];  %  volts
ntu =     [0.0, 500, 1000, 1500, 2000, 3000];  % NTU 

% quadratic polynomial: ntu = a*V^2 + b*V + c
p = polyfit(voltage, ntu, 2);  


a = p(1); b = p(2); c = p(3);
fprintf('Fitted: NTU = (%.4f) * V^2 + (%.4f) * V + (%.4f)\n', a, b, c);


% Plot 
figure;
plot(voltage, ntu, 'ro', 'MarkerSize', 8, 'DisplayName', 'Measured data');
hold on;
Vplot = linspace(min(voltage), max(voltage), 200);
plot(Vplot, polyval(p, Vplot), 'b-', 'LineWidth', 2, 'DisplayName', 'Quadratic fit');
xlabel('Voltage (V)');
ylabel('Turbidity (NTU)');
legend('Location', 'best');
grid on;

