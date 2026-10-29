"""A rede entre os computadores: sincroniza o fórum e cultiva os qarchis.

Cada Semente é um nó. Os nós se acham na rede local (anúncio UDP), pelos pontos
de encontro configurados e trocando listas de pares. Eles trocam eventos do
fórum (só os de assinatura válida) e peças de qarchis (só as que batem com a
impressão digital). Não existe servidor central: um ponto de encontro é só um
nó que fica sempre ligado.
"""
import json
import random
import socket
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import qarchi as qmod
from .config import PORTA, PORTA_ANUNCIO, PONTOS_DE_ENCONTRO, ADMIN_RAIZ, VERSAO

ID_REDE = ADMIN_RAIZ[:16]   # nós de fóruns diferentes não se misturam


class Limite:
    def __init__(self, bps):
        self.bps, self.fichas, self.t, self.trava = bps, bps, time.time(), threading.Lock()

    def esperar(self, n):
        while True:
            with self.trava:
                t = time.time()
                self.fichas = min(self.bps, self.fichas + (t - self.t) * self.bps)
                self.t = t
                if self.fichas >= n:
                    self.fichas -= n
                    return
                falta = (n - self.fichas) / self.bps
            time.sleep(min(falta, 1))


class Medidor:
    def __init__(self):
        self.amostras, self.total, self.trava = [], 0, threading.Lock()

    def somar(self, n):
        with self.trava:
            self.amostras.append((time.time(), n))
            self.total += n

    def bps(self):
        with self.trava:
            corte = time.time() - 5
            self.amostras = [a for a in self.amostras if a[0] > corte]
            return sum(n for _, n in self.amostras) / 5


def _get(url, timeout=8, limite=None):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read(limite) if limite else r.read()


def _post(url, corpo, timeout=8):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def ips_locais():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return [ip]
    except OSError:
        return []


class No:
    def __init__(self, banco, pasta_qarchis, log=print):
        self.banco, self.pasta_qarchis, self.log = banco, pasta_qarchis, log
        self.pares = {}            # "host:porta" -> {"visto", "seq", "fixo"}
        self.lavouras = {}         # qid -> Lavoura
        self.pausados = set()
        self.status = {}           # qid -> {"pares": n}
        self.porta = None
        self.compartilhar = False
        self.limite = Limite(512 * 1024)
        self.vagas = threading.BoundedSemaphore(6)
        self.desce, self.sobe = Medidor(), Medidor()
        self.pendentes = []        # eventos meus ainda não entregues a nenhum par
        self.srv = None
        self.trava = threading.Lock()
        for p in PONTOS_DE_ENCONTRO:
            self.pares[p] = {"visto": 0, "seq": 0, "fixo": True}

    def configurar(self, kbps, conexoes):
        self.limite = Limite(max(16, kbps) * 1024)
        self.vagas = threading.BoundedSemaphore(max(1, conexoes))

    # ------------------------------------------------------------ servidor
    def iniciar_servidor(self, porta=None):
        if self.srv:
            return self.porta
        no = self

        class H(BaseHTTPRequestHandler):
            server_version = "Semente/" + VERSAO
            protocol_version = "HTTP/1.0"

            def log_message(self, *a):
                pass

            def _json(self, obj, codigo=200):
                corpo = json.dumps(obj, ensure_ascii=False).encode()
                self.send_response(codigo)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            def do_GET(self):
                u = urllib.parse.urlparse(self.path)
                p = u.path.strip("/").split("/")
                qs = urllib.parse.parse_qs(u.query)
                if p[:2] != ["semente", ID_REDE]:
                    return self.send_error(404)
                p = p[2:]
                if p == ["ping"]:
                    return self._json({"versao": VERSAO, "porta": no.porta})
                if p == ["eventos"]:
                    desde = int(qs.get("desde", ["0"])[0])
                    lote = no.banco.desde(desde, 400)
                    return self._json({"eventos": [e for _, e in lote], "ultimo": lote[-1][0] if lote else desde})
                if p == ["pares"]:
                    vivos = [k for k, d in list(no.pares.items()) if time.time() - d.get("visto", 0) < 600 and d.get("alcancavel")]
                    return self._json({"pares": vivos[:50]})
                if len(p) >= 2 and p[0] == "qarchi":
                    qid = p[1]
                    lav = no.lavouras.get(qid)
                    if not lav or qid in no.pausados or not no.pode_servir(qid):
                        return self.send_error(404)
                    if len(p) == 2:
                        return self._json(lav.q)
                    if p[2] == "tem":
                        return self._json({"tem": lav.tem})
                    if p[2] == "peca" and len(p) == 4:
                        try:
                            dados = lav.ler(int(p[3]))
                        except ValueError:
                            dados = None
                        if dados is None:
                            return self.send_error(404)
                        if not no.vagas.acquire(blocking=False):
                            return self.send_error(503)
                        try:
                            no.limite.esperar(len(dados))
                            self.send_response(200)
                            self.send_header("Content-Type", "application/octet-stream")
                            self.send_header("Content-Length", str(len(dados)))
                            self.end_headers()
                            self.wfile.write(dados)
                            no.sobe.somar(len(dados))
                        finally:
                            no.vagas.release()
                        return
                self.send_error(404)

            def do_POST(self):
                p = urllib.parse.urlparse(self.path).path.strip("/").split("/")
                if p != ["semente", ID_REDE, "eventos"]:
                    return self.send_error(404)
                n = int(self.headers.get("Content-Length", "0"))
                if n > 4 * 1024 * 1024:
                    return self.send_error(413)
                try:
                    evs = json.loads(self.rfile.read(n))[:300]
                except (ValueError, TypeError):
                    return self.send_error(400)
                novos = sum(1 for e in evs if isinstance(e, dict) and no.banco.adicionar(e, recalcular=False))
                if novos:
                    no.banco.recalcular()
                # quem mandou também vira par (se for alcançável)
                porta = self.headers.get("X-Semente-Porta")
                if porta and porta.isdigit():
                    no.conhecer(f"{self.client_address[0]}:{porta}")
                self._json({"novos": novos})

        portas = [porta] if porta else list(range(PORTA, PORTA + 20))
        for pt in portas:
            try:
                srv = ThreadingHTTPServer(("0.0.0.0", pt), H)
                break
            except OSError:
                continue
        else:
            self.log("Não consegui abrir uma porta para compartilhar.")
            return None
        srv.daemon_threads = True
        self.srv, self.porta = srv, pt
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        threading.Thread(target=self._anunciar, daemon=True).start()
        self.log(f"Nó ativo na porta {pt}.")
        return pt

    def parar_servidor(self):
        if self.srv:
            self.srv.shutdown()
            self.srv.server_close()
            self.srv, self.porta = None, None

    def pode_servir(self, qid):
        est = self.banco.estado
        if est.qarchi_liberado(qid):
            return True
        # quem cultivou serve o próprio qarchi enquanto espera aprovação
        lav = self.lavouras.get(qid)
        return bool(lav and lav.q["cultivador"] == getattr(self, "minha_pub", None))

    # ------------------------------------------------------------ descoberta
    def _anunciar(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self.porta:
            msg = json.dumps({"semente": ID_REDE, "porta": self.porta}).encode()
            for destino in ("<broadcast>", "127.0.0.1"):
                try:
                    s.sendto(msg, (destino, PORTA_ANUNCIO))
                except OSError:
                    pass
            time.sleep(10)

    def escutar(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        try:
            s.bind(("", PORTA_ANUNCIO))
        except OSError:
            return
        locais = ("127.0.0.1",) + tuple(ips_locais())
        while True:
            try:
                dados, (ip, _) = s.recvfrom(2048)
                m = json.loads(dados)
                if m.get("semente") == ID_REDE and isinstance(m.get("porta"), int):
                    if m["porta"] == self.porta and ip in locais:
                        continue
                    self.conhecer(f"{ip}:{m['porta']}", alcancavel=True)
            except (OSError, ValueError):
                continue

    def conhecer(self, par, alcancavel=False, fixo=False):
        par = par if ":" in par else f"{par}:{PORTA}"
        host, _, pt = par.rpartition(":")
        if self.porta and pt == str(self.porta) and host in ("127.0.0.1", "localhost") + tuple(ips_locais()):
            return
        with self.trava:
            novo = par not in self.pares
            d = self.pares.setdefault(par, {"visto": 0, "seq": 0})
            if alcancavel:
                d["alcancavel"], d["visto"] = True, time.time()
            if fixo:
                d["fixo"] = True
        if novo:
            self.log(f"Novo par: {par}")

    def vivos(self):
        return {p: d for p, d in list(self.pares.items()) if d.get("alcancavel") and time.time() - d.get("visto", 0) < 180}

    # ------------------------------------------------------------ fórum
    def publicar(self, ev):
        if not self.banco.adicionar(ev):
            return 0
        self.pendentes.append(ev)
        return self._entregar()

    def _entregar(self):
        if not self.pendentes:
            return 0
        entregues = 0
        cab = {"X-Semente-Porta": str(self.porta)} if self.porta else {}
        for par in list(self.vivos()) + [p for p, d in self.pares.items() if d.get("fixo")]:
            try:
                req = urllib.request.Request(f"http://{par}/semente/{ID_REDE}/eventos", data=json.dumps(self.pendentes).encode(),
                                             headers={"Content-Type": "application/json", **cab})
                urllib.request.urlopen(req, timeout=8).read()
                entregues += 1
            except OSError:
                continue
        if entregues:
            self.pendentes = []
        return entregues

    def sincronizar_sempre(self):
        while True:
            for par, d in list(self.pares.items()):
                if not d.get("fixo") and not d.get("alcancavel"):
                    # par que só se apresentou: testa se é alcançável
                    try:
                        _get(f"http://{par}/semente/{ID_REDE}/ping", 4)
                        self.conhecer(par, alcancavel=True)
                    except OSError:
                        continue
                try:
                    novos = 0
                    for _ in range(20):
                        r = json.loads(_get(f"http://{par}/semente/{ID_REDE}/eventos?desde={d.get('seq', 0)}", 10))
                        for e in r.get("eventos", []):
                            if isinstance(e, dict) and self.banco.adicionar(e, recalcular=False):
                                novos += 1
                        d["seq"] = r.get("ultimo", d.get("seq", 0))
                        if len(r.get("eventos", [])) < 400:
                            break
                    if novos:
                        self.banco.recalcular()
                    d["alcancavel"], d["visto"] = True, time.time()
                    for outro in json.loads(_get(f"http://{par}/semente/{ID_REDE}/pares", 6)).get("pares", [])[:50]:
                        if isinstance(outro, str) and outro.count(":") == 1:
                            self.conhecer(outro)
                except (OSError, ValueError):
                    d["alcancavel"] = d.get("fixo", False) and d.get("alcancavel", False)
            self._entregar()
            time.sleep(12)

    # ------------------------------------------------------------ qarchis
    def plantar(self, q):
        """Começa a cultivar um qarchi (baixar o que falta e, se permitido, servir)."""
        if q["qid"] in self.lavouras:
            return self.lavouras[q["qid"]]
        lav = qmod.Lavoura(q, self.pasta_qarchis)
        self.lavouras[q["qid"]] = lav
        self.status[q["qid"]] = {"pares": 0}
        return lav

    def remover(self, qid):
        self.lavouras.pop(qid, None)
        self.status.pop(qid, None)

    def cultivar_sempre(self):
        espera_fontes = {}
        while True:
            trabalhou = False
            for qid, lav in list(self.lavouras.items()):
                if qid in self.pausados or lav.completo():
                    continue
                pares = list(self.vivos())
                random.shuffle(pares)
                com = 0
                for par in pares:
                    try:
                        tem = json.loads(_get(f"http://{par}/semente/{ID_REDE}/qarchi/{qid}/tem", 5))["tem"]
                    except (OSError, ValueError, KeyError):
                        continue
                    com += 1
                    faltam = [i for i in lav.faltam() if i < len(tem) and tem[i]]
                    random.shuffle(faltam)  # peças em ordem aleatória, como no torrent
                    for i in faltam[:6]:
                        try:
                            dados = _get(f"http://{par}/semente/{ID_REDE}/qarchi/{qid}/peca/{i}", 30, lav.ps + 1)
                        except OSError:
                            continue
                        if len(dados) <= lav.ps and lav.gravar(i, dados):
                            self.desce.somar(len(dados))
                            trabalhou = True
                        else:
                            self.log(f"Peça recusada de {par}: não confere com o qarchi.")
                            self.pares.get(par, {})["alcancavel"] = False
                            break
                self.status[qid] = {"pares": com}
                if lav.completo():
                    self.log(f"Pronto: {lav.info['nome']}")
                if not trabalhou and lav.info.get("fontes") and time.time() > espera_fontes.get(qid, 0):
                    espera_fontes[qid] = time.time() + 120
                    trabalhou = self._das_fontes(lav) or trabalhou
            if not trabalhou:
                time.sleep(2)

    def _das_fontes(self, lav):
        """Fontes web do qarchi (ex.: o site do autor), conferidas peça por peça."""
        ok = False
        for base in lav.info["fontes"]:
            dados = b""
            try:
                for a in lav.info["arquivos"]:
                    dados += _get(base.rstrip("/") + "/" + urllib.parse.quote(a["caminho"]), 60, a["tamanho"] + 1)[:a["tamanho"]]
            except OSError:
                continue
            for i in range(len(lav.tem)):
                if lav.gravar(i, dados[i * lav.ps:(i + 1) * lav.ps]):
                    ok = True
            self.desce.somar(len(dados))
            if lav.completo():
                self.log(f"Pronto (pela fonte {base}): {lav.info['nome']}")
                break
        return ok
