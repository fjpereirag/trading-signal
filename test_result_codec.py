import unittest

from nacl.exceptions import CryptoError

from result_codec import open_message, seal


class ResultCodecTests(unittest.TestCase):
    def test_roundtrip_and_wrong_password(self):
        password = "Una clave local bastante larga y secreta"
        encoded = seal("1. Acción: Esperar\n2. SL: Mantener\n3. Parcial: No actuar", password)
        self.assertNotIn(b"Esperar", encoded)
        self.assertEqual(open_message(encoded, password).count("\n"), 2)
        with self.assertRaises(CryptoError):
            open_message(encoded, "Una clave diferente bastante larga")


if __name__ == "__main__":
    unittest.main()
