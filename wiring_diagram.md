# Smart Glass Hardware Wiring Diagram

## Component List

- Raspberry Pi 4B
- 3x Push Buttons (momentary)
- 3x 10kΩ Resistors (pull-down)
- HC-SR04 Ultrasonic Sensor
- Pi Camera Module
- Breadboard (optional, for testing)
- Jumper wires

## Button Wiring

### Button 1 (Mode Selection) - Pin 36
```
Button 1:
├── One terminal → GPIO 36 (Pin 36)
├── Other terminal → 3.3V
└── 10kΩ resistor → GPIO 36 to GND (pull-down)
```

### Button 2 (Confirm) - Pin 38
```
Button 2:
├── One terminal → GPIO 38 (Pin 38)
├── Other terminal → 3.3V
└── 10kΩ resistor → GPIO 38 to GND (pull-down)
```

### Button 3 (Exit/Idle) - Pin 40
```
Button 3:
├── One terminal → GPIO 40 (Pin 40)
├── Other terminal → 3.3V
└── 10kΩ resistor → GPIO 40 to GND (pull-down)
```

## Ultrasonic Sensor Wiring

### HC-SR04 Connections
```
HC-SR04:
├── VCC → 5V (Pin 2 or 4)
├── TRIG → GPIO 7 (Pin 7)
├── ECHO → GPIO 11 (Pin 11)
└── GND → GND (Pin 6, 9, 14, 20, 25, 30, 34, 39)
```

## Camera Connection

### Pi Camera Module
```
Camera Module:
├── CSI ribbon cable → CSI port on Pi
└── Secure with camera mount
```

## Power Considerations

- **3.3V**: For GPIO pins and buttons
- **5V**: For ultrasonic sensor
- **GND**: Common ground for all components

## Important Notes

1. **Pull-down resistors are essential** - Without them, buttons may trigger randomly
2. **Use 3.3V for buttons** - GPIO pins are 3.3V logic, not 5V
3. **Secure connections** - Use proper connectors or solder for permanent installation
4. **Test with multimeter** - Verify connections before powering on
5. **Camera orientation** - Ensure camera is mounted correctly

## Testing Sequence

1. Test button connections with `test_buttons.py`
2. Verify ultrasonic sensor with distance measurements
3. Test camera with basic OpenCV capture
4. Run full application with `smart_glass.py`

## Troubleshooting

- **Button not working**: Check pull-down resistor connection
- **False triggers**: Verify debouncing in software
- **Ultrasonic errors**: Check TRIG/ECHO pin connections
- **Camera issues**: Verify CSI cable and enable in raspi-config
