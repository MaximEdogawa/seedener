class QRType:
    """
        Used with DecodeQR and EncodeQR to communicate qr encoding type
    """
    KEY__KEYQR = "key__keyqr"
    BUNDLE__QR = "bundle__qr"
    KEY__COMPACTKEYQR = "key__compactkeyqr"
    KEY__UR2 = "key__ur2"
    SECRECT_COMPONENT = "se1"
    ENCRYPTED_KEY="Salted__"
    QR_SEQUENCE_MODE = 'mode'
    MODE_HASH = 1
    MODE_CHUNK = 0
    BUNDLE_CHUNK = 'chunk'
    BUNDLE_TOTAL_CHUNKS = 'chunks'


    SETTINGS = "settings"

    OUTPUT__UR = "output__ur"
    ACCOUNT__UR = "account__ur"
    BYTES__UR = "bytes__ur"

    INVALID = "invalid"