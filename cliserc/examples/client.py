
from simplex    import Simplex
from bnot       import BNot
import sys

def on_send(bnot: BNot, dt: float) -> BNot:
    if bnot.get('length', 0) != 0:
        print(bnot)
        sys.exit(0)
    return BNot({'response': Simplex.RES_OK})

client = Simplex(
    '192.168.0.200',
    6000,
    False,
    on_send=on_send
)

client.connect()
