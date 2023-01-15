# Python program to generate QR code
from qrtools import QR 
  
# creates the QR object
my_QR = QR(data = u"Example")
  
# encodes to a QR code
my_QR.encode()

print (my_QR.data_type)
print (my_QR.pixel_size)
print (my_QR.margin_size)
print (my_QR.data)