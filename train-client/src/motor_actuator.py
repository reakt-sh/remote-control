

from globals import MAX_SPEED, SCALE_FACTOR_PWM
from app_logger import logger

try:
    import RPi.GPIO as GPIO
except ImportError:
    logger.error("RPi.GPIO library not found. MotorActuator will not function properly.")
    GPIO = None  # Running on non-Pi hardware

# Use bluetooth speaker
import pygame

class MotorActuator:
    def __init__(self, input1_pin=19, input2_pin=26, enable_pin=13, pwm_freq=1000, led_pin=17):
        self.input1_pin = input1_pin                # GPIO pin for IN1, used for forward direction
        self.input2_pin = input2_pin                # GPIO pin for IN2, used for backward direction
        self.enable_pin = enable_pin                # GPIO pin for EN, used for PWM control
        self.led_pin = led_pin                      # GPIO pin for LED indicator
        self.pwm_freq = pwm_freq                    # Frequency for PWM control
        self.direction = 1                          # 1 for forward, -1 for backward
        self.scale_factor = SCALE_FACTOR_PWM        # Scale factor to convert speed to PWM duty cycle
        self.max_speed = MAX_SPEED * self.scale_factor
        self.current_speed = 0

        if GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.input1_pin, GPIO.OUT)
            GPIO.setup(self.input2_pin, GPIO.OUT)
            GPIO.setup(self.enable_pin, GPIO.OUT)
            GPIO.setup(self.led_pin, GPIO.OUT)

        # initial state: motor stopped, LED off
        if GPIO:
            GPIO.output(self.input1_pin, GPIO.LOW)
            GPIO.output(self.input2_pin, GPIO.LOW)
            GPIO.output(self.led_pin, GPIO.LOW)
            self.pwm = GPIO.PWM(self.enable_pin, self.pwm_freq)
            self.pwm.start(0)  # Default to speed 0
            logger.info(f"MotorActuator initialized with max speed: {self.max_speed}")
        else:
            logger.warning("GPIO not available. MotorActuator will not control hardware.")

        # Use bluetooth speaker for horn sound
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound("./asset/train_horn_sample.wav")
    def start_motor(self):
        if self.direction == 1:
            if GPIO:
                GPIO.output(self.input1_pin, GPIO.HIGH)
                GPIO.output(self.input2_pin, GPIO.LOW)
        else:
            if GPIO:
                GPIO.output(self.input1_pin, GPIO.LOW)
                GPIO.output(self.input2_pin, GPIO.HIGH)

    def stop_motor(self):
        if GPIO:
            GPIO.output(self.input1_pin, GPIO.LOW)
            GPIO.output(self.input2_pin, GPIO.LOW)

    def set_direction(self, d):
        self.direction = d
        self.start_motor()

    def set_speed(self, speed):
        self.current_speed = int(speed * self.scale_factor) # Scale speed to match PWM range
        self.current_speed = max(0, min(self.current_speed, self.max_speed))
        if GPIO:
            self.pwm.ChangeDutyCycle(self.current_speed)

    def get_speed(self):
        return int(self.current_speed / self.scale_factor)  # Convert back to original speed scale

    def set_led_turn_on(self):
        if GPIO:
            GPIO.output(self.led_pin, GPIO.HIGH)

    def set_led_turn_off(self):
        if GPIO:
            GPIO.output(self.led_pin, GPIO.LOW)

    def horn_on(self):
        logger.info("Playing horn sound.")
        self.sound.play(loops=-1)  # Play the sound in a loop

    def horn_off(self):
        logger.info("Stopping horn sound.")
        self.sound.stop()

    def cleanup(self):
        self.stop_motor()
        if GPIO:
            self.pwm.stop()
            GPIO.cleanup([self.input1_pin, self.input2_pin, self.enable_pin, self.led_pin])