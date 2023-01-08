
import qrcode

class QR(object):

    def __init__(self,seed_phrase):
        self.seed_phrase = seed_phrase
        self.qr = qrcode.make(self.seed_phrase)
        type(self.qr)
        self.qr = qrcode.QRCode( version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=5, border=3)
        self.qr.make(fit=True)
        self.qr.make_image(fill_color="black", back_color="white").resize((240,240)).convert('RGB').show()
