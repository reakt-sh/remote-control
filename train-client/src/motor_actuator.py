import RPi.GPIO as GPIO
from globals import MAX_SPEED, SCALE_FACTOR_PWM
from loguru import logger

class MotorActuator:
    def __init__(self, input1_pin=19, input2_pin=26, enable_pin=13, pwm_freq=1000):
        self.input1_pin = input1_pin                # GPIO pin for IN1, used for forward direction
        self.input2_pin = input2_pin                # GPIO pin for IN2, used for backward direction
        self.enable_pin = enable_pin                # GPIO pin for EN, used for PWM control
        self.pwm_freq = pwm_freq                    # Frequency for PWM control
        self.direction = 1                          # 1 for forward, 0 for backward
        self.scale_factor = SCALE_FACTOR_PWM        # Scale factor to convert speed to PWM duty cycle
        self.max_speed = MAX_SPEED * self.scale_factor
        self.current_speed = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.input1_pin, GPIO.OUT)
        GPIO.setup(self.input2_pin, GPIO.OUT)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.output(self.input1_pin, GPIO.LOW)
        GPIO.output(self.input2_pin, GPIO.LOW)
        self.pwm = GPIO.PWM(self.enable_pin, self.pwm_freq)
        self.pwm.start(self.max_speed)  # Default to max speed
        logger.info(f"MotorActuator initialized with max speed: {self.max_speed}")

    def start_motor(self):
        self.current_speed = max(self.current_speed, self.max_speed)
        self.set_speed(self.current_speed)
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
        self.current_speed = int(speed * self.scale_factor) # Scale speed to match PWM range

        # clamp speed to [0, max_speed]
        self.current_speed = max(0, min(self.current_speed, self.max_speed))
        self.pwm.ChangeDutyCycle(self.current_speed)

    def get_speed(self):
        return int(self.current_speed / self.scale_factor)  # Convert back to original speed scale

    def cleanup(self):
        self.stop_motor()
        self.pwm.stop()
        GPIO.cleanup([self.input1_pin, self.input2_pin, self.enable_pin])