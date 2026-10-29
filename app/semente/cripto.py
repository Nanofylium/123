"""Chaves e assinaturas (secp256k1 / Schnorr BIP-340) em Python puro.

Cada membro é uma chave. A chave secreta é derivada do nome de usuário e da
senha com scrypt, então a pessoa entra de qualquer computador só com usuário e
senha, sem servidor guardando contas.
"""
import hashlib
import secrets

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)


def _dobra(p):
    x, y, z = p
    if y == 0:
        return (0, 0, 0)
    ysq = y * y % P
    s = 4 * x * ysq % P
    m = 3 * x * x % P
    nx = (m * m - 2 * s) % P
    return (nx, (m * (s - nx) - 8 * ysq * ysq) % P, 2 * y * z % P)


def _soma(p, q):
    if p[2] == 0:
        return q
    if q[2] == 0:
        return p
    z1, z2 = p[2] * p[2] % P, q[2] * q[2] % P
    u1, u2 = p[0] * z2 % P, q[0] * z1 % P
    s1, s2 = p[1] * q[2] * z2 % P, q[1] * p[2] * z1 % P
    if u1 == u2:
        return _dobra(p) if s1 == s2 else (0, 0, 0)
    h, r = (u2 - u1) % P, (s2 - s1) % P
    h2 = h * h % P
    h3 = h * h2 % P
    u1h2 = u1 * h2 % P
    nx = (r * r - h3 - 2 * u1h2) % P
    return (nx, (r * (u1h2 - nx) - s1 * h3) % P, h * p[2] * q[2] % P)


def _afim(r):
    if r[2] == 0:
        return None
    zi = pow(r[2], P - 2, P)
    return (r[0] * zi * zi % P, r[1] * zi * zi * zi % P)


def _mul(pt, k):
    r, a = (0, 0, 0), (pt[0], pt[1], 1)
    while k:
        if k & 1:
            r = _soma(r, a)
        a = _dobra(a)
        k >>= 1
    return _afim(r)


def _somar_pontos(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return _afim(_soma((a[0], a[1], 1), (b[0], b[1], 1)))


def _th(tag, dados):
    t = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(t + t + dados).digest()


def _x_para_ponto(x):
    if x >= P:
        return None
    ysq = (pow(x, 3, P) + 7) % P
    y = pow(ysq, (P + 1) // 4, P)
    if y * y % P != ysq:
        return None
    return (x, y if y % 2 == 0 else P - y)


def publica(sk: bytes) -> str:
    return _mul(G, int.from_bytes(sk, "big"))[0].to_bytes(32, "big").hex()


def assinar(msg: bytes, sk: bytes, aux: bytes = None) -> str:
    d0 = int.from_bytes(sk, "big")
    pt = _mul(G, d0)
    d = d0 if pt[1] % 2 == 0 else N - d0
    aux = aux if aux is not None else secrets.token_bytes(32)
    t = (d ^ int.from_bytes(_th("BIP0340/aux", aux), "big")).to_bytes(32, "big")
    px = pt[0].to_bytes(32, "big")
    k0 = int.from_bytes(_th("BIP0340/nonce", t + px + msg), "big") % N
    R = _mul(G, k0)
    k = k0 if R[1] % 2 == 0 else N - k0
    e = int.from_bytes(_th("BIP0340/challenge", R[0].to_bytes(32, "big") + px + msg), "big") % N
    return (R[0].to_bytes(32, "big") + ((k + e * d) % N).to_bytes(32, "big")).hex()


def verificar(msg: bytes, pub_hex: str, sig_hex: str) -> bool:
    try:
        pub, sig = bytes.fromhex(pub_hex), bytes.fromhex(sig_hex)
    except ValueError:
        return False
    if len(pub) != 32 or len(sig) != 64:
        return False
    pt = _x_para_ponto(int.from_bytes(pub, "big"))
    r, s = int.from_bytes(sig[:32], "big"), int.from_bytes(sig[32:], "big")
    if pt is None or r >= P or s >= N:
        return False
    e = int.from_bytes(_th("BIP0340/challenge", sig[:32] + pub + msg), "big") % N
    R = _somar_pontos(_mul(G, s), _mul(pt, N - e))
    return R is not None and R[1] % 2 == 0 and R[0] == r


def chave_da_senha(usuario: str, senha: str) -> bytes:
    """Mesma pessoa, mesmo usuário e senha, mesma chave, em qualquer computador."""
    sal = ("semente/qarchi/v1/" + usuario.strip().lower()).encode()
    bruto = hashlib.scrypt(senha.encode(), salt=sal, n=2 ** 15, r=8, p=1, maxmem=64 * 1024 * 1024, dklen=32)
    k = int.from_bytes(bruto, "big") % (N - 1) + 1
    return k.to_bytes(32, "big")
