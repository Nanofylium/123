"""O formato .qarchi (o "torrent" da Semente) e o armazém de peças.

Um .qarchi é um arquivo pequeno (JSON) que descreve um conjunto de arquivos:
nomes, tamanhos e a impressão digital SHA-256 de cada peça. Quem tem o .qarchi
consegue baixar os arquivos de várias pessoas ao mesmo tempo, peça por peça, e
conferir cada uma. O qid (identidade do qarchi) é o SHA-256 da descrição, então
ninguém consegue trocar o conteúdo sem mudar o qid.

Ele é assinado por quem o cultivou. No fórum, um qarchi só é espalhado pela rede
se for do admin ou se o admin aprovar: é assim que o fórum continua legal.
"""
import hashlib
import json
import os
import threading
import time

from . import cripto

FORMATO = "qarchi/1"
MAX_TOTAL = 1024 * 1024 * 1024      # 1 GB por qarchi
MAX_PECAS = 4000


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def tamanho_de_peca(total):
    ps = 256 * 1024
    while total / ps > MAX_PECAS // 2 and ps < 16 * 1024 * 1024:
        ps *= 2
    return ps


def _seguro(caminho):
    partes = caminho.replace("\\", "/").split("/")
    return all(p not in ("", ".", "..") and ":" not in p for p in partes) and len(caminho) < 300


def mapa_relativo(arquivos, base=None):
    """{caminho dentro do qarchi: caminho no disco}."""
    base = base or os.path.commonpath([os.path.dirname(os.path.abspath(a)) for a in arquivos])
    return {os.path.relpath(os.path.abspath(a), base).replace("\\", "/"): os.path.abspath(a) for a in arquivos}


def cultivar(arquivos, nome, descricao, sk, base=None, fontes=()):
    """Cria um qarchi a partir de arquivos locais. Devolve o dicionário .qarchi."""
    lista = sorted(mapa_relativo(arquivos, base).items())
    total = sum(os.path.getsize(c) for _, c in lista)
    if total == 0 or total > MAX_TOTAL:
        raise ValueError("O qarchi precisa ter entre 1 byte e 1 GB.")
    ps = tamanho_de_peca(total)
    pecas, buf, descr = [], b"", []
    for rel, c in lista:
        h = hashlib.sha256()
        with open(c, "rb") as f:
            for bloco in iter(lambda: f.read(1 << 20), b""):
                h.update(bloco)
                buf += bloco
                while len(buf) >= ps:
                    pecas.append(hashlib.sha256(buf[:ps]).hexdigest())
                    buf = buf[ps:]
        descr.append({"caminho": rel, "tamanho": os.path.getsize(c), "sha256": h.hexdigest()})
    if buf:
        pecas.append(hashlib.sha256(buf).hexdigest())
    info = {"nome": nome.strip()[:120], "descricao": descricao.strip()[:2000], "tamanho_peca": ps,
            "arquivos": descr, "pecas": pecas, "criado": int(time.time()), "fontes": list(fontes)}
    qid = hashlib.sha256(_canon(info).encode()).hexdigest()
    return {"formato": FORMATO, "qid": qid, "info": info, "cultivador": cripto.publica(sk),
            "sig": cripto.assinar(bytes.fromhex(qid), sk)}


def valido(q):
    try:
        if q.get("formato") != FORMATO:
            return False
        info = q["info"]
        if hashlib.sha256(_canon(info).encode()).hexdigest() != q["qid"]:
            return False
        total = sum(a["tamanho"] for a in info["arquivos"])
        ps = info["tamanho_peca"]
        if not (0 < total <= MAX_TOTAL) or not isinstance(ps, int) or ps < 16 * 1024:
            return False
        if len(info["pecas"]) != -(-total // ps) or len(info["pecas"]) > MAX_PECAS:
            return False
        if not all(_seguro(a["caminho"]) for a in info["arquivos"]):
            return False
        return cripto.verificar(bytes.fromhex(q["qid"]), q["cultivador"], q["sig"])
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def salvar(q, caminho):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False, indent=1)


def abrir(caminho):
    with open(caminho, encoding="utf-8") as f:
        q = json.load(f)
    if not valido(q):
        raise ValueError("Este arquivo .qarchi está corrompido ou foi alterado.")
    return q


class Lavoura:
    """Os arquivos de um qarchi em disco, com o mapa das peças já conferidas."""

    def __init__(self, q, pasta_base):
        self.q, self.info = q, q["info"]
        self.qid = q["qid"]
        self.ps = self.info["tamanho_peca"]
        self.pasta = os.path.join(pasta_base, _nome_pasta(self.info["nome"], self.qid))
        self.total = sum(a["tamanho"] for a in self.info["arquivos"])
        self.trava = threading.Lock()
        os.makedirs(self.pasta, exist_ok=True)
        for a in self.info["arquivos"]:
            c = self._caminho(a)
            os.makedirs(os.path.dirname(c), exist_ok=True)
            if not os.path.exists(c) or os.path.getsize(c) != a["tamanho"]:
                with open(c, "ab") as f:
                    f.truncate(a["tamanho"])
        self.tem = [self._confere(i) for i in range(len(self.info["pecas"]))]

    def _caminho(self, a):
        return os.path.join(self.pasta, *a["caminho"].split("/"))

    def _trechos(self, i):
        """Em quais arquivos (e onde) cai a peça i."""
        ini, fim = i * self.ps, min((i + 1) * self.ps, self.total)
        pos = 0
        for a in self.info["arquivos"]:
            a_ini, a_fim = pos, pos + a["tamanho"]
            if a_fim > ini and a_ini < fim:
                yield self._caminho(a), max(ini, a_ini) - a_ini, min(fim, a_fim) - max(ini, a_ini)
            pos = a_fim

    def ler(self, i):
        if not (0 <= i < len(self.tem)) or not self.tem[i]:
            return None
        partes = []
        for c, off, n in self._trechos(i):
            with open(c, "rb") as f:
                f.seek(off)
                partes.append(f.read(n))
        return b"".join(partes)

    def _confere(self, i):
        partes = []
        for c, off, n in self._trechos(i):
            with open(c, "rb") as f:
                f.seek(off)
                partes.append(f.read(n))
        return hashlib.sha256(b"".join(partes)).hexdigest() == self.info["pecas"][i]

    def gravar(self, i, dados):
        if not (0 <= i < len(self.tem)) or hashlib.sha256(dados).hexdigest() != self.info["pecas"][i]:
            return False
        with self.trava:
            if self.tem[i]:
                return True
            pos = 0
            for c, off, n in self._trechos(i):
                with open(c, "r+b") as f:
                    f.seek(off)
                    f.write(dados[pos:pos + n])
                pos += n
            self.tem[i] = True
        return True

    def progresso(self):
        return sum(self.tem) / len(self.tem) if self.tem else 1.0

    def completo(self):
        return all(self.tem)

    def faltam(self):
        return [i for i, ok in enumerate(self.tem) if not ok]


def _nome_pasta(nome, qid):
    limpo = "".join(c if c.isalnum() or c in " -_." else "_" for c in nome).strip() or "qarchi"
    return f"{limpo[:60]} [{qid[:8]}]"
