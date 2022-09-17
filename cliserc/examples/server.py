
from simplex    import Simplex
from bnot       import BNot

def on_send(bnot: BNot, dt: float) -> BNot:
    return BNot({'response': Simplex.RES_OK})

server = Simplex(
    '192.168.0.200',
    6000,
    True,
    on_send=on_send
)

if server.start():
    try:
        while True:
            server.wait()
    except KeyboardInterrupt:
        pass
server.close()
