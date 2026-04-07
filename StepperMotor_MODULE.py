import RPi.GPIO as GPIO
from time import sleep

class StepperMotor:
    '''
    For 28BYJ-48 stepper motor with 1/64 gear reduction and ULN2003 driver.
    '''
    
    def __init__(self, defaultPins = [22, 24, 26, 32], defaultGB=64, defaultDir='CCW',
                 defaultMode='full'):
        self.gearRatio = defaultGB
        self._stepAngle = None
        self.pins = defaultPins
        self.dir = defaultDir
        self._stepDelay = 0.015
        self.outputRotation = None
        self.numSteps = None
        self.driveMode = defaultMode
        self._mod = None
        self.speed = None
        self.printOutput = False
        # Set up the motor
        self.GPIO_motorSetup()
        
    
    
    def setDriveMode(self, mode):

        if mode == 'wave':
            self.driveMode = 'wave'
            self._stepAngle = 11.25
            self._mod = 4
            self._seq = [[0,0,0,1],
                        [1,0,0,0],
                        [0,1,0,0],
                        [0,0,1,0]]
            
        elif mode == 'full':
            self.driveMode = 'full'
            self._stepAngle = 11.25
            self._mod = 4
            self._seq = [[1,1,0,0],
                        [0,1,1,0],
                        [0,0,1,1],
                        [1,0,0,1]]
              
        elif mode == 'half':
            self.driveMode = 'half'
            self._stepAngle = 5.625
            self._mod = 8
            self._seq = [[1,0,0,1],
                         [1,0,0,0],
                         [1,1,0,0],
                         [0,1,0,0],
                         [0,1,1,0],
                         [0,0,1,0],
                         [0,0,1,1],
                         [0,0,0,1]]               
 

    def GPIO_motorSetup(self):
        # Set up the GPIO for stepper motor
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        for i in range(4):
            GPIO.setup(self.pins[i], GPIO.OUT)


    def _steps(self):
        # Calculate how many steps are needed for
        # the desired out shaft rotation
        motorRotation = self.outputRotation * self.gearRatio
        return int(motorRotation / self._stepAngle)

        
        
    def rotate(self, degrees, direction, speed, mode):
        # Rotate the base platform through desired steps in the
        # specified direction

        # Motion parameters
        self.outputRotation = degrees
        self.dir = direction
        # Set the speed (delay)
        if speed == 's':
            self._stepDelay = 0.015
        elif speed == 'f':
            self._stepDelay = 0.002
        # Set drive mode
        self.setDriveMode(mode)
        # Number of steps required for ths motion
        self.numSteps = self._steps()
        
        if self.printOutput:
            # print parameters
            print(f"Output rotation = {self.outputRotation} deg")
            print(f"Num of steps = {self.numSteps}")
            print(f"Mode = {self.driveMode}")
            print(f"Step angle = {self._stepAngle}")
            print(f"Speed = {speed}")
            print(f"Direction = {self.dir}")


        # Rotate    
        for i in range(self._steps()):
            # Write each step pattern to all 4 pins at once. (% (modulo) is used to
            # prevent running out of the number of rows in step sequence)
            if self.dir == 'CCW':
                GPIO.output(self.pins, self._seq[i % self._mod])
                # print output?
                if self.printOutput:
                    print(f"CCW, step= {i:<3}, mod= {(i % self._mod)}, pins= {self._seq[i % self._mod]}")
            else:
                GPIO.output(self.pins, self._seq[-(i+1) % self._mod])
                # print output?
                if self.printOutput:
                    print(f"CW, step= {i:<3}, mod= {-(i+1) % self._mod}, pins= {self._seq[-(i+1) % self._mod]}")
            sleep(self._stepDelay)            

        # Turn off all pins (to prevent heating of the motor and driver)
        GPIO.output(self.pins, [0,0,0,0])

