"""Cliente do servidor da Semente (PocketBase), só com a biblioteca padrão.

A Semente é um cliente comum: fala com um servidor que o autor mantém ligado.
Não há rede entre computadores dos leitores; tudo passa pelo servidor.
"""
import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid


class ErroAPI(Exception):
    def __init__(self, mensagem, codigo=0, dados=None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.dados = dados or {}


class Offline(ErroAPI):
    """O servidor não respondeu (laptop do autor desligado ou sem internet)."""


def _mensagem_do_erro(dados):
    if isinstance(dados, dict):
        if dados.get("message"):
            campos = dados.get("data") or {}
            if isinstance(campos, dict) and campos:
                primeiro = next(iter(campos.values()))
                if isinstance(primeiro, dict) and primeiro.get("message"):
                    return f"{dados['message']} ({primeiro['message']})"
            return dados["message"]
    return "Erro no servidor."


class Cliente:
    def __init__(self, base, timeout=12):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.token = ""

    # ------------------------------------------------------------ baixo nível
    def _abrir(self, req):
        if self.token:
            req.add_header("Authorization", self.token)
        try:
            return urllib.request.urlopen(req, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            corpo = e.read()
            try:
                dados = json.loads(corpo or b"{}")
            except ValueError:
                dados = {}
            raise ErroAPI(_mensagem_do_erro(dados), e.code, dados)
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise Offline("O servidor da Semente não respondeu. O laptop do autor pode estar "
                          "desligado agora. Tente de novo mais tarde.") from e

    def pedir(self, metodo, caminho, corpo=None, params=None):
        url = self.base + caminho
        if params:
            url += "?" + urllib.parse.urlencode(params)
        dados = json.dumps(corpo).encode() if corpo is not None else None
        req = urllib.request.Request(url, data=dados, method=metodo)
        if dados is not None:
            req.add_header("Content-Type", "application/json")
        with self._abrir(req) as r:
            texto = r.read()
        return json.loads(texto or b"{}")

    def pedir_multipart(self, metodo, caminho, campos, arquivos):
        """campos: dict de texto; arquivos: lista de (campo, nome, bytes)."""
        limite = "----semente" + uuid.uuid4().hex
        corpo = bytearray()
        for k, v in campos.items():
            corpo += f'--{limite}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        for campo, nome, conteudo in arquivos:
            tipo = mimetypes.guess_type(nome)[0] or "application/octet-stream"
            corpo += (f'--{limite}\r\nContent-Disposition: form-data; name="{campo}"; '
                      f'filename="{nome}"\r\nContent-Type: {tipo}\r\n\r\n').encode()
            corpo += conteudo + b"\r\n"
        corpo += f"--{limite}--\r\n".encode()
        req = urllib.request.Request(self.base + caminho, data=bytes(corpo), method=metodo)
        req.add_header("Content-Type", f"multipart/form-data; boundary={limite}")
        with self._abrir(req) as r:
            return json.loads(r.read() or b"{}")

    # ------------------------------------------------------------ conta
    def entrar(self, usuario, senha):
        d = self.pedir("POST", "/api/collections/users/auth-with-password",
                       {"identity": usuario, "password": senha})
        self.token = d["token"]
        return d["record"]

    def cadastrar(self, usuario, senha, nome, sobre=""):
        return self.pedir("POST", "/api/collections/users/records",
                          {"username": usuario, "password": senha, "passwordConfirm": senha,
                           "name": nome, "sobre": sobre})

    def renovar(self):
        d = self.pedir("POST", "/api/collections/users/auth-refresh")
        self.token = d["token"]
        return d["record"]

    def sair(self):
        self.token = ""

    # ------------------------------------------------------------ registros
    def listar(self, colecao, filtro=None, ordem=None, pagina=1, por_pagina=200, expand=None):
        p = {"page": pagina, "perPage": por_pagina, "skipTotal": 1}
        if filtro:
            p["filter"] = filtro
        if ordem:
            p["sort"] = ordem
        if expand:
            p["expand"] = expand
        return self.pedir("GET", f"/api/collections/{colecao}/records", params=p).get("items", [])

    def listar_tudo(self, colecao, **kw):
        itens, pagina = [], 1
        while True:
            lote = self.listar(colecao, pagina=pagina, **kw)
            itens += lote
            if len(lote) < kw.get("por_pagina", 200):
                break
            pagina += 1
        return itens

    def criar(self, colecao, dados):
        return self.pedir("POST", f"/api/collections/{colecao}/records", dados)

    def atualizar(self, colecao, rid, dados):
        return self.pedir("PATCH", f"/api/collections/{colecao}/records/{rid}", dados)

    def apagar(self, colecao, rid):
        return self.pedir("DELETE", f"/api/collections/{colecao}/records/{rid}")

    def url_arquivo(self, colecao, rid, nome):
        return f"{self.base}/api/files/{colecao}/{rid}/{urllib.parse.quote(nome)}"

    def baixar_arquivo(self, colecao, rid, nome, destino):
        req = urllib.request.Request(self.url_arquivo(colecao, rid, nome))
        with self._abrir(req) as r, open(destino, "wb") as f:
            while True:
                pedaco = r.read(65536)
                if not pedaco:
                    break
                f.write(pedaco)
        return destino
