"""O núcleo do app: conta, fórum e qarchis, falando com o servidor do autor.

Não há rede entre computadores dos leitores. A Semente é um cliente: lê e
escreve no servidor que o autor mantém ligado. O servidor (PocketBase) é quem
garante as regras: ninguém posta banido, ninguém se passa por outra pessoa e só
o autor modera, aprova e apaga o que é dos outros.
"""
import calendar
import json
import os
import threading
import time

from . import api
from .config import (AUTOR_USUARIO, CATEGORIAS_PADRAO, CONFIG, PASTA, PASTA_DOWNLOADS,
                     REGRAS_PADRAO, SERVIDOR)


class Erro(Exception):
    pass


def ler_cfg():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def gravar_cfg(c):
    os.makedirs(PASTA, exist_ok=True)
    tmp = CONFIG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)
    os.replace(tmp, CONFIG)


def _epoch(texto):
    """'2026-10-30 01:56:16.412Z' -> inteiro de segundos."""
    if not texto:
        return 0
    try:
        base = texto.split(".")[0].replace("T", " ").rstrip("Z").strip()
        return calendar.timegm(time.strptime(base, "%Y-%m-%d %H:%M:%S"))
    except (ValueError, TypeError):
        return 0


class Estado:
    """O fórum montado a partir dos registros do servidor.

    Guarda as mesmas estruturas que a janela espera, mas vindas do servidor em
    vez de eventos assinados. 'pub' aqui é o id do usuário no servidor.
    """

    def __init__(self, dados=None):
        d = dados or {}
        self.admin = d.get("autor_id", "")
        cfg = d.get("config") or {}
        self.regras = {
            "texto": cfg.get("regras_texto") or REGRAS_PADRAO,
            "so_aprovados": bool(cfg.get("so_aprovados")),
            "qarchis_de_membros": cfg.get("qarchis_de_membros", True),
            "categorias": cfg.get("categorias") or list(CATEGORIAS_PADRAO),
        }
        self.aviso = cfg.get("aviso", "")
        self.banidos, self.aprovados = {}, set()
        self.perfis = {}
        self.topicos, self.respostas, self.curtidas = {}, {}, {}
        self.fixados = set()
        self.qarchis = {}

        for u in d.get("users", []):
            self.perfis[u["id"]] = {"usuario": u.get("username", ""), "nome": u.get("name") or u.get("username", ""),
                                    "sobre": u.get("sobre", ""), "desde": _epoch(u.get("created"))}
            if u.get("autor"):
                self.admin = u["id"]
            if u.get("banido"):
                self.banidos[u["id"]] = u.get("banido_motivo", "")
            if u.get("aprovado"):
                self.aprovados.add(u["id"])

        for t in d.get("topicos", []):
            self.topicos[t["id"]] = {"id": t["id"], "autor": t.get("autor", ""), "tipo": "topico",
                                     "criado": _epoch(t.get("created")),
                                     "dados": {"titulo": t.get("titulo", ""), "texto": t.get("texto", ""),
                                               "categoria": t.get("categoria", "")}}
            if t.get("fixado"):
                self.fixados.add(t["id"])

        for r in d.get("respostas", []):
            ev = {"id": r["id"], "autor": r.get("autor", ""), "tipo": "resposta", "criado": _epoch(r.get("created")),
                  "dados": {"texto": r.get("texto", ""), "topico": r.get("topico", "")}}
            self.respostas.setdefault(r.get("topico", ""), []).append(ev)

        for c in d.get("curtidas", []):
            self.curtidas.setdefault(c.get("alvo", ""), set()).add(c.get("autor", ""))

        for q in d.get("qarchis", []):
            arquivos = [{"caminho": nome, "tamanho": 0} for nome in q.get("arquivos", [])]
            self.qarchis[q["id"]] = {
                "evento": {"id": q["id"], "autor": q.get("autor", "")},
                "qarchi": {"qid": q["id"], "info": {"nome": q.get("nome", ""), "descricao": q.get("descricao", ""),
                                                    "arquivos": arquivos}},
                "descricao": q.get("descricao", ""),
                "aprovado": bool(q.get("aprovado")),
                "arquivos": q.get("arquivos", []),
            }

    # ---- consultas (mesma interface de antes) ----
    def e_admin(self, pub):
        return bool(pub) and pub == self.admin

    def pode_postar(self, pub):
        if not pub or pub in self.banidos:
            return False
        return pub == self.admin or not self.regras.get("so_aprovados") or pub in self.aprovados

    def visivel(self, ev):
        a = ev["autor"]
        return a not in self.banidos

    def qarchi_liberado(self, qid):
        q = self.qarchis.get(qid)
        return bool(q and q["aprovado"] and q["evento"]["autor"] not in self.banidos)

    def nome(self, pub):
        p = self.perfis.get(pub)
        return p["nome"] if p else (pub[:10] + "…" if pub else "alguém")

    def usuario(self, pub):
        p = self.perfis.get(pub)
        return "@" + p["usuario"] if p and p["usuario"] else ""

    def lista_topicos(self, categoria=None):
        tops = [t for t in self.topicos.values() if self.visivel(t) and (not categoria or t["dados"]["categoria"] == categoria)]

        def ultima(t):
            rs = [r["criado"] for r in self.respostas.get(t["id"], []) if self.visivel(r)]
            return max([t["criado"]] + rs)
        return sorted(tops, key=lambda t: (t["id"] in self.fixados, ultima(t)), reverse=True)

    def respostas_de(self, tid):
        return sorted([r for r in self.respostas.get(tid, []) if self.visivel(r)], key=lambda r: r["criado"])


class Nucleo:
    def __init__(self, log=print, servidor=None):
        os.makedirs(PASTA_DOWNLOADS, exist_ok=True)
        self.log = log
        self.cfg = ler_cfg()
        base = servidor or os.environ.get("SEMENTE_SERVIDOR") or self.cfg.get("servidor") or SERVIDOR
        self.api = api.Cliente(base)
        self.servidor = base
        self.pub = None
        self.perfil = None
        self.online = False
        self.erro_conexao = ""
        self.estado = Estado()
        self.config_id = None
        self.versao = 0
        self._assinatura = None
        self._trava = threading.RLock()
        self._parar = False

    # ------------------------------------------------------------ sessão
    def iniciar(self):
        """Tenta reaproveitar o login salvo e começa a sincronizar em segundo plano."""
        token = self.cfg.get("token")
        if token:
            self.api.token = token
            try:
                rec = self.api.renovar()
                self._guardar_sessao(rec)
            except api.ErroAPI:
                self.api.token = ""
                self.cfg.pop("token", None)
                gravar_cfg(self.cfg)
            except api.Offline:
                pass
        self.sincronizar(forcar=True)
        threading.Thread(target=self._laco, daemon=True).start()

    def _laco(self):
        while not self._parar:
            time.sleep(4)
            self.sincronizar()

    def _guardar_sessao(self, rec):
        self.pub = rec["id"]
        self.perfil = rec
        self.cfg["token"] = self.api.token
        self.cfg["ultimo_usuario"] = rec.get("username", "")
        gravar_cfg(self.cfg)

    def entrar(self, usuario, senha):
        usuario = usuario.strip().lower()
        try:
            rec = self.api.entrar(usuario, senha)
        except api.Offline as e:
            raise Erro(str(e))
        except api.ErroAPI:
            raise Erro("Usuário ou senha incorretos.")
        if rec.get("banido"):
            raise Erro("Esta conta foi removida pelo autor. Motivo: " + (rec.get("banido_motivo") or "não informado"))
        self._guardar_sessao(rec)
        self.sincronizar(forcar=True)
        return self.pub

    def cadastrar(self, usuario, senha, nome, sobre=""):
        usuario = usuario.strip().lower()
        if len(senha) < 10:
            raise Erro("A senha precisa ter pelo menos 10 caracteres.")
        if not nome.strip():
            raise Erro("Diga como quer ser chamado.")
        try:
            self.api.cadastrar(usuario, senha, nome.strip()[:40], sobre.strip()[:600])
        except api.Offline as e:
            raise Erro(str(e))
        except api.ErroAPI as e:
            if e.codigo == 400:
                raise Erro("Não deu para criar a conta. Talvez esse usuário já exista ou a senha seja curta demais.")
            raise Erro(str(e))
        return self.entrar(usuario, senha)

    def sair(self):
        self.api.sair()
        self.pub = self.perfil = None
        self.cfg.pop("token", None)
        gravar_cfg(self.cfg)

    def e_admin(self):
        return self.pub is not None and self.pub == self.estado.admin

    def _preciso_entrar(self):
        if not self.pub:
            raise Erro("Entre na sua conta primeiro.")

    def _fazer(self, funcao):
        """Executa uma ação no servidor, traduzindo os erros e atualizando o fórum."""
        try:
            resultado = funcao()
        except api.Offline as e:
            raise Erro(str(e))
        except api.ErroAPI as e:
            if e.codigo in (401, 403, 404):
                raise Erro("O servidor não permitiu essa ação. Talvez só o autor possa fazê-la, "
                           "ou sua conta precise de aprovação.")
            raise Erro(str(e))
        self.sincronizar(forcar=True)
        return resultado

    # ------------------------------------------------------------ fórum
    def novo_topico(self, titulo, texto, categoria):
        self._preciso_entrar()
        if not titulo.strip() or not texto.strip():
            raise Erro("Dê um título e um texto ao tópico.")
        return self._fazer(lambda: self.api.criar("topicos", {
            "titulo": titulo.strip()[:140], "texto": texto.strip()[:20000],
            "categoria": categoria, "autor": self.pub}))

    def responder(self, topico_id, texto):
        self._preciso_entrar()
        if not texto.strip():
            raise Erro("Escreva uma resposta.")
        return self._fazer(lambda: self.api.criar("respostas", {
            "topico": topico_id, "texto": texto.strip()[:20000], "autor": self.pub}))

    def curtir(self, alvo):
        self._preciso_entrar()
        if self.pub in self.estado.curtidas.get(alvo, set()):
            return None
        return self._fazer(lambda: self.api.criar("curtidas", {"alvo": alvo, "autor": self.pub}))

    def apagar(self, alvo):
        self._preciso_entrar()

        def tentar():
            for colecao in ("topicos", "respostas", "qarchis"):
                try:
                    return self.api.apagar(colecao, alvo)
                except api.ErroAPI as e:
                    if e.codigo == 404:
                        continue
                    raise
            raise api.ErroAPI("Nada para apagar.", 404)
        return self._fazer(tentar)

    def editar_perfil(self, nome, sobre):
        self._preciso_entrar()
        return self._fazer(lambda: self.api.atualizar("users", self.pub, {
            "name": nome.strip()[:40], "sobre": sobre.strip()[:600]}))

    # ------------------------------------------------------------ admin
    def admin(self, tipo, **c):
        self._preciso_entrar()
        if not self.e_admin():
            raise Erro("Só o autor pode fazer isso.")
        cid = self.config_id

        def acao():
            if tipo == "fixar":
                return self.api.atualizar("topicos", c["topico"], {"fixado": bool(c.get("fixo", True))})
            if tipo == "aprovar":
                return self.api.atualizar("users", c["membro"], {"aprovado": True})
            if tipo == "reprovar":
                return self.api.atualizar("users", c["membro"], {"aprovado": False})
            if tipo == "banir":
                return self.api.atualizar("users", c["membro"], {"banido": True, "banido_motivo": c.get("motivo", "")[:300]})
            if tipo == "desbanir":
                return self.api.atualizar("users", c["membro"], {"banido": False, "banido_motivo": ""})
            if tipo == "aprovar_qarchi":
                return self.api.atualizar("qarchis", c["qid"], {"aprovado": True})
            if tipo == "aviso":
                return self.api.atualizar("config", cid, {"aviso": c.get("texto", "")[:300]})
            if tipo == "regras":
                return self.api.atualizar("config", cid, {
                    "regras_texto": c.get("texto", "")[:4000], "so_aprovados": bool(c.get("so_aprovados")),
                    "qarchis_de_membros": bool(c.get("qarchis_de_membros", True)),
                    "categorias": c.get("categorias") or ["Conversa livre"]})
            raise Erro("Ação de admin desconhecida.")
        if tipo in ("aviso", "regras") and not cid:
            raise Erro("O servidor ainda não tem as configurações do fórum. Tente de novo em instantes.")
        return self._fazer(acao)

    def trocar_senha(self, senha_atual, nova_senha):
        self._preciso_entrar()
        if len(nova_senha) < 10:
            raise Erro("Use uma senha com pelo menos 10 caracteres.")
        try:
            self.api.atualizar("users", self.pub, {
                "oldPassword": senha_atual, "password": nova_senha, "passwordConfirm": nova_senha})
        except api.Offline as e:
            raise Erro(str(e))
        except api.ErroAPI:
            raise Erro("Não deu para trocar a senha. Confira a senha atual.")
        # a troca invalida o token; entra de novo com a senha nova
        self.api.entrar(self.perfil.get("username", ""), nova_senha)
        self.cfg["token"] = self.api.token
        gravar_cfg(self.cfg)

    # ------------------------------------------------------------ qarchis
    def enviar_qarchi(self, arquivos, nome, descricao):
        self._preciso_entrar()
        if not arquivos:
            raise Erro("Escolha pelo menos um arquivo.")
        if not self.e_admin() and not self.estado.regras.get("qarchis_de_membros", True):
            raise Erro("No momento só o autor pode enviar qarchis.")
        envio = []
        for caminho in arquivos:
            with open(caminho, "rb") as f:
                envio.append(("arquivos", os.path.basename(caminho), f.read()))

        def acao():
            rec = self.api.pedir_multipart("POST", "/api/collections/qarchis/records",
                                           {"nome": nome.strip()[:140] or "Qarchi", "descricao": descricao.strip()[:2000],
                                            "autor": self.pub}, envio)
            if self.e_admin():
                rec = self.api.atualizar("qarchis", rec["id"], {"aprovado": True})
            return rec
        return self._fazer(acao)

    def baixar_qarchi(self, qid, pasta=None):
        q = self.estado.qarchis.get(qid)
        if not q:
            raise Erro("Qarchi não encontrado.")
        destino = os.path.join(pasta or PASTA_DOWNLOADS, q["qarchi"]["info"]["nome"] or qid)
        os.makedirs(destino, exist_ok=True)
        try:
            for nome in q["arquivos"]:
                self.api.baixar_arquivo("qarchis", qid, nome, os.path.join(destino, nome))
        except api.Offline as e:
            raise Erro(str(e))
        except api.ErroAPI as e:
            raise Erro("Não deu para baixar: " + str(e))
        return destino

    def excluir_qarchi(self, qid):
        return self._fazer(lambda: self.api.apagar("qarchis", qid))

    # ------------------------------------------------------------ sincronização
    def sincronizar(self, forcar=False):
        with self._trava:
            try:
                users = self.api.listar_tudo("users", por_pagina=200)
                config = self.api.listar("config", por_pagina=1)
                topicos = self.api.listar_tudo("topicos", ordem="-created", por_pagina=200)
                respostas = self.api.listar_tudo("respostas", ordem="created", por_pagina=200)
                curtidas = self.api.listar_tudo("curtidas", por_pagina=200)
                qarchis = self.api.listar_tudo("qarchis", ordem="-created", por_pagina=200)
            except api.Offline as e:
                self.online = False
                self.erro_conexao = str(e)
                return
            except api.ErroAPI as e:
                self.online = False
                self.erro_conexao = str(e)
                return
            self.online = True
            self.erro_conexao = ""
            cfg = config[0] if config else {}
            self.config_id = cfg.get("id") or self.config_id
            autor_id = next((u["id"] for u in users if u.get("autor")), "")
            estado = Estado({"users": users, "config": cfg, "topicos": topicos, "respostas": respostas,
                             "curtidas": curtidas, "qarchis": qarchis, "autor_id": autor_id})
            assinatura = (len(topicos), len(respostas), len(curtidas), len(users), len(qarchis),
                          cfg.get("updated", ""),
                          max([t.get("updated", "") for t in topicos] + [""]),
                          max([r.get("updated", "") for r in respostas] + [""]),
                          max([q.get("updated", "") for q in qarchis] + [""]))
            self.estado = estado
            if forcar or assinatura != self._assinatura:
                self._assinatura = assinatura
                self.versao += 1
