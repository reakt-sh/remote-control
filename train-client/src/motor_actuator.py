import RPi.GPIO as GPIO

class MotorActuator:
    def __init__(self, input1_pin=19, input2_pin=26, enable_pin=13, pwm_freq=1000):
        self.input1_pin = input1_pin    # GPIO pin for IN1, used for forward direction
        self.input2_pin = input2_pin    # GPIO pin for IN2, used for backward direction
        self.enable_pin = enable_pin    # GPIO pin for EN, used for PWM control
        self.pwm_freq = pwm_freq        # Frequency for PWM control
        self.direction = 1              # 1 for forward, 0 for backward
        self.speed = 25                 # Default speed (duty cycle for P

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.input1_pin, GPIO.OUT)
        GPIO.setup(self.input2_pin, GPIO.OUT)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.output(self.input1_pin, GPIO.LOW)
        GPIO.output(self.input2_pin, GPIO.LOW)
        self.pwm = GPIO.PWM(self.enable_pin, self.pwm_freq)
        self.pwm.start(self.speed)  # Default to low speed

    def start_motor(self):
        self.speed = max(self.speed, 25) # Ensure minimum speed
        self.set_speed(self.speed)
        if self.direction == 1:
            GPIO.output(self.input1_pin, GPIO.HIGH)
            GPIO.output(self.input2_pin, GPIO.LOW)
        else:
            GPIO.output(self.input1_pin, GPIO.LOW)
            GPIO.output(self.input2_pin, GPIO.HIGH)

    def stop_motor(self):
        GPIO.output(self.input1_pin, GPIO.LOW)
        GPIO.output(self.input2_pin, GPIO.LOW)

    def move_forward(self):
        self.direction = 1
        self.start_motor()

    def move_backward(self):
        self.direction = 0
        self.start_motor()

    def set_speed(self, speed):
        self.speed = int(speed * 1.25) # Scale speed to match PWM range
        self.speed = max(0, min(75, speed))
        self.pwm.ChangeDutyCycle(self.speed)

    def get_speed(self):
        return int(self.speed / 1.25)  # Convert back to original speed scale

    def cleanup(self):
        self.stop()
        self.pwm.stop()
        GPIO.cleanup([self.input1_pin, self.input2_pin, self.enable_pin])