class QRType:
    """
        Used with DecodeQR and EncodeQR to communicate qr encoding type
    """
    KEY__KEYQR = "key__keyqr"
    KEY__COMPACTKEYQR = "key__compactkeyqr"
    KEY__UR2 = "key__ur2"
    SECRECT__COMPONENT = "se1"
    SPEND_BUNDLE= "bls"

    SETTINGS = "settings"

    OUTPUT__UR = "output__ur"
    ACCOUNT__UR = "account__ur"
    BYTES__UR = "bytes__ur"

    INVALID = "invalid"