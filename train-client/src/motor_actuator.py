import RPi.GPIO as GPIO

class MotorActuator:
    def __init__(self, input1_pin=19, input2_pin=26, enable_pin=13, pwm_freq=1000):
        self.input1_pin = input1_pin    # GPIO pin for IN1, used for forward direction
        self.input2_pin = input2_pin    # GPIO pin for IN2, used for backward direction
        self.enable_pin = enable_pin    # GPIO pin for EN, used for PWM control
        self.pwm_freq = pwm_freq        # Frequency for PWM control
        self.direction = 1              # 1 for forward, 0 for backward

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.input1_pin, GPIO.OUT)
        GPIO.setup(self.input2_pin, GPIO.OUT)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.output(self.input1_pin, GPIO.LOW)
        GPIO.output(self.input2_pin, GPIO.LOW)
        self.pwm = GPIO.PWM(self.enable_pin, self.pwm_freq)
        self.pwm.start(25)  # Default to low speed

    def start_motor(self):
        if self.direction == 1:
            self.move_forward()
        else:
            self.move_backward()

    def stop_motor(self):
        GPIO.output(self.input1_pin, GPIO.LOW)
        GPIO.output(self.input2_pin, GPIO.LOW)

    def move_forward(self):
        GPIO.output(self.input1_pin, GPIO.HIGH)
        GPIO.output(self.input2_pin, GPIO.LOW)
        self.direction = 1

    def move_backward(self):
        GPIO.output(self.input1_pin, GPIO.LOW)
        GPIO.output(self.input2_pin, GPIO.HIGH)
        self.direction = 0

    def set_speed(self, speed):
        self.pwm.ChangeDutyCycle(speed)

    def cleanup(self):
        self.stop()
        self.pwm.stop()
        GPIO.cleanup([self.input1_pin, self.input2_pin, self.enable_pin])