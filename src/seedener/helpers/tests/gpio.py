import RPi.GPIO as GPIO


if GPIO.RPI_INFO['TYPE'] == 'Compute Module 4':
    print("Detected 40pin GPIO (Raspberry pi compute modul 4)")
    
elif GPIO.RPI_INFO['TYPE'] == 'Zero':
    print("Detected 40pin GPIO (Rasbperry Pi Zero)")
    
elif GPIO.RPI_INFO['P1_REVISION'] == 3:
    print("Detected 40pin GPIO (Rasbperry Pi 2 and above)")
    
else:
    print("Assuming 26 Pin GPIO (Raspberry P1 1)")

print(GPIO.RPI_INFO)