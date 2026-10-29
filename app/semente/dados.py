"""Eventos assinados, o banco local (SQLite) e o estado do fórum.

Tudo o que acontece no fórum é um evento assinado: perfil, tópico, resposta,
curtida, qarchi publicado e as ações do admin (regras, banir, apagar, aprovar).
Cada computador guarda os eventos que recebe, confere a assinatura e calcula o
mesmo estado. As ações do admin só valem se assinadas pela chave do admin, e
todos os computadores as obedecem.
"""
import hashlib
import json
import re
import sqlite3
import threading
import time

from . import cripto
from .config import ADMIN_RAIZ, CATEGORIAS_PADRAO, REGRAS_PADRAO

MAX_EVENTO = 256 * 1024
USUARIO_OK = re.compile(r"^[a-z0-9_.]{3,24}$")
NOMES_RESERVADOS = ("admin", "autor", "ailig", "qarchi", "moderador", "semente", "oficial")

TIPOS_MEMBRO = {"perfil", "topico", "resposta", "curtida", "qarchi", "apagar"}
TIPOS_ADMIN = {"regras", "banir", "desbanir", "aprovar", "reprovar", "aprovar_qarchi", "fixar", "novo_admin", "aviso"}


def serializar(autor, tipo, criado, dados):
    return json.dumps([autor, tipo, criado, dados], sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def criar_evento(sk, tipo, dados, criado=None):
    autor = cripto.publica(sk)
    criado = int(criado or time.time())
    eid = hashlib.sha256(serializar(autor, tipo, criado, dados).encode()).hexdigest()
    return {"id": eid, "autor": autor, "tipo": tipo, "criado": criado, "dados": dados,
            "sig": cripto.assinar(bytes.fromhex(eid), sk)}


def _texto(d, campo, maximo, minimo=0):
    v = d.get(campo, "")
    return isinstance(v, str) and minimo <= len(v.strip()) <= maximo


def formato_valido(ev):
    """Confere estrutura, tamanho, id e assinatura. Não depende do estado."""
    try:
        if not isinstance(ev, dict) or set(ev) != {"id", "autor", "tipo", "criado", "dados", "sig"}:
            return False
        if len(json.dumps(ev, ensure_ascii=False)) > MAX_EVENTO:
            return False
        if ev["tipo"] not in TIPOS_MEMBRO | TIPOS_ADMIN or not isinstance(ev["dados"], dict):
            return False
        if not isinstance(ev["criado"], int) or ev["criado"] > time.time() + 600:
            return False
        if hashlib.sha256(serializar(ev["autor"], ev["tipo"], ev["criado"], ev["dados"]).encode()).hexdigest() != ev["id"]:
            return False
        d, t = ev["dados"], ev["tipo"]
        if t == "perfil" and not (isinstance(d.get("usuario"), str) and USUARIO_OK.match(d["usuario"])
                                  and _texto(d, "nome", 40, 1) and _texto(d, "sobre", 600)):
            return False
        if t == "topico" and not (_texto(d, "titulo", 140, 3) and _texto(d, "texto", 20000, 1) and _texto(d, "categoria", 40, 1)):
            return False
        if t == "resposta" and not (_texto(d, "topico", 64, 64) and _texto(d, "texto", 20000, 1)):
            return False
        if t in ("curtida", "apagar") and not _texto(d, "alvo", 64, 64):
            return False
        if t == "qarchi" and not (isinstance(d.get("qarchi"), dict) and _texto(d, "descricao", 2000)):
            return False
        return cripto.verificar(bytes.fromhex(ev["id"]), ev["autor"], ev["sig"])
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


class Banco:
    def __init__(self, caminho):
        self.trava = threading.RLock()
        self.db = sqlite3.connect(caminho, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS eventos(
            seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE, autor TEXT, tipo TEXT,
            criado INTEGER, json TEXT)""")
        self.db.execute("CREATE INDEX IF NOT EXISTS ev_autor ON eventos(autor)")
        self.db.execute("CREATE TABLE IF NOT EXISTS removidos(id TEXT PRIMARY KEY)")
        self.db.commit()
        self.versao = 0
        self.estado = Estado([])
        self.recalcular()

    def todos(self):
        with self.trava:
            return [json.loads(j) for (j,) in self.db.execute("SELECT json FROM eventos ORDER BY criado, seq")]

    def desde(self, seq, limite=500):
        with self.trava:
            linhas = self.db.execute("SELECT seq, json FROM eventos WHERE seq > ? ORDER BY seq LIMIT ?", (seq, limite)).fetchall()
        return [(s, json.loads(j)) for s, j in linhas]

    def tem(self, eid):
        with self.trava:
            return self.db.execute("SELECT 1 FROM eventos WHERE id=? UNION SELECT 1 FROM removidos WHERE id=?", (eid, eid)).fetchone() is not None

    def adicionar(self, ev, recalcular=True):
        """Guarda o evento se for válido e permitido. Devolve True se é novo."""
        if self.tem(ev.get("id", "")) or not formato_valido(ev):
            return False
        if not self.estado.permitido(ev):
            return False
        with self.trava:
            self.db.execute("INSERT OR IGNORE INTO eventos(id, autor, tipo, criado, json) VALUES (?,?,?,?,?)",
                            (ev["id"], ev["autor"], ev["tipo"], ev["criado"], json.dumps(ev, ensure_ascii=False)))
            self.db.commit()
        if recalcular:
            self.recalcular()
        return True

    def recalcular(self):
        with self.trava:
            est = Estado(self.todos())
            # o que foi apagado ou é de membro banido sai do disco também
            lixo = [eid for eid in est.descartar]
            if lixo:
                self.db.executemany("DELETE FROM eventos WHERE id=?", [(i,) for i in lixo])
                self.db.executemany("INSERT OR IGNORE INTO removidos(id) VALUES (?)", [(i,) for i in lixo])
                self.db.commit()
            self.estado = est
            self.versao += 1


class Estado:
    """O fórum calculado a partir dos eventos, aplicando as decisões do admin."""

    def __init__(self, eventos):
        self.admin = ADMIN_RAIZ
        self.regras = {"texto": REGRAS_PADRAO, "so_aprovados": False, "categorias": list(CATEGORIAS_PADRAO), "qarchis_de_membros": True}
        self.aviso = ""
        self.banidos, self.aprovados = {}, set()
        self.perfis, self.donos_usuario = {}, {}
        self.topicos, self.respostas, self.curtidas = {}, {}, {}
        self.qarchis, self.qarchis_aprovados = {}, set()
        self.fixados, self.apagados = set(), set()
        self.descartar = []
        admin_evs = [e for e in eventos if e["tipo"] in TIPOS_ADMIN]
        # 1) ações do admin, em ordem; a cadeia de "novo_admin" passa a coroa
        for e in admin_evs:
            if e["autor"] != self.admin:
                self.descartar.append(e["id"])
                continue
            d, t = e["dados"], e["tipo"]
            if t == "novo_admin" and isinstance(d.get("pub"), str) and len(d["pub"]) == 64:
                self.admin = d["pub"]
            elif t == "regras":
                for k in ("texto", "so_aprovados", "categorias", "qarchis_de_membros"):
                    if k in d:
                        self.regras[k] = d[k]
            elif t == "aviso":
                self.aviso = d.get("texto", "")
            elif t == "banir":
                self.banidos[d.get("membro", "")] = d.get("motivo", "")
            elif t == "desbanir":
                self.banidos.pop(d.get("membro", ""), None)
            elif t == "aprovar":
                self.aprovados.add(d.get("membro", ""))
            elif t == "reprovar":
                self.aprovados.discard(d.get("membro", ""))
            elif t == "aprovar_qarchi":
                self.qarchis_aprovados.add(d.get("qid", ""))
            elif t == "fixar":
                (self.fixados.add if d.get("fixo", True) else self.fixados.discard)(d.get("topico", ""))
        # 2) apagamentos: pelo próprio autor do conteúdo ou pelo admin
        autores = {e["id"]: e["autor"] for e in eventos}
        for e in eventos:
            if e["tipo"] == "apagar":
                alvo = e["dados"].get("alvo")
                if alvo in autores and (e["autor"] == self.admin or autores[alvo] == e["autor"]):
                    self.apagados.add(alvo)
        # 3) conteúdo dos membros
        for e in eventos:
            t, d, a = e["tipo"], e["dados"], e["autor"]
            if t in TIPOS_ADMIN or t == "apagar":
                continue
            if a in self.banidos or e["id"] in self.apagados:
                self.descartar.append(e["id"])
                continue
            if t == "perfil":
                u = d["usuario"].lower()
                if a != self.admin and any(r in u for r in NOMES_RESERVADOS):
                    continue
                dono = self.donos_usuario.get(u)
                if dono and dono != a and a != self.admin:
                    continue  # nome de usuário já é de outra pessoa
                antigo = self.perfis.get(a)
                if antigo and antigo["usuario"] != u:
                    self.donos_usuario.pop(antigo["usuario"], None)
                self.donos_usuario[u] = a
                self.perfis[a] = {"usuario": u, "nome": d["nome"].strip(), "sobre": d.get("sobre", ""),
                                  "desde": (antigo or {}).get("desde", e["criado"])}
            elif t == "topico":
                if d["categoria"] in self.regras["categorias"] or a == self.admin:
                    self.topicos[e["id"]] = e
            elif t == "resposta":
                self.respostas.setdefault(d["topico"], []).append(e)
            elif t == "curtida":
                self.curtidas.setdefault(d["alvo"], set()).add(a)
            elif t == "qarchi":
                q = d["qarchi"]
                self.qarchis[q.get("qid", "")] = {"evento": e, "qarchi": q, "descricao": d.get("descricao", "")}

    # ---- consultas ----
    def e_admin(self, pub):
        return pub == self.admin

    def pode_postar(self, pub):
        if pub in self.banidos:
            return False
        return pub == self.admin or not self.regras.get("so_aprovados") or pub in self.aprovados

    def visivel(self, ev):
        a = ev["autor"]
        return a not in self.banidos and ev["id"] not in self.apagados and (
            a == self.admin or not self.regras.get("so_aprovados") or a in self.aprovados)

    def qarchi_liberado(self, qid):
        q = self.qarchis.get(qid)
        if not q or q["evento"]["id"] in self.apagados or q["evento"]["autor"] in self.banidos:
            return False
        return q["evento"]["autor"] == self.admin or (self.regras.get("qarchis_de_membros", True) and qid in self.qarchis_aprovados)

    def permitido(self, ev):
        """Recusa logo na chegada o que já se sabe proibido."""
        if ev["autor"] in self.banidos and ev["tipo"] not in TIPOS_ADMIN:
            return False
        if ev["id"] in self.apagados:
            return False
        return True

    def nome(self, pub):
        p = self.perfis.get(pub)
        return p["nome"] if p else pub[:10] + "…"

    def usuario(self, pub):
        p = self.perfis.get(pub)
        return "@" + p["usuario"] if p else ""

    def lista_topicos(self, categoria=None):
        tops = [t for t in self.topicos.values() if self.visivel(t) and (not categoria or t["dados"]["categoria"] == categoria)]

        def ultima(t):
            rs = [r["criado"] for r in self.respostas.get(t["id"], []) if self.visivel(r)]
            return max([t["criado"]] + rs)
        return sorted(tops, key=lambda t: (t["id"] in self.fixados, ultima(t)), reverse=True)

    def respostas_de(self, tid):
        return sorted([r for r in self.respostas.get(tid, []) if self.visivel(r)], key=lambda r: r["criado"])
