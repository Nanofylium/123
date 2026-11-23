"""Modo servidor: sobe o PocketBase que o autor mantém ligado 24h.

Isto roda na máquina do autor (`Semente.exe --servidor`). Ele:
  1. baixa o PocketBase certo para o sistema, se ainda não tiver;
  2. garante um superusuário (para o painel do PocketBase em /_/);
  3. aplica as coleções e regras do fórum;
  4. garante a conta do autor (admin do fórum);
  5. fica servindo.

O app dos leitores é só um cliente que se conecta a este servidor pela internet
(via Cloudflare Tunnel apontando sementes.ailigqarchi.com.br para esta máquina).
Não há nada que se instale ou se espalhe sozinho entre as máquinas dos leitores.
"""
import os
import platform
import secrets
import subprocess
import sys
import time
import urllib.request
import zipfile

from . import api
from .config import AUTOR_USUARIO, CATEGORIAS_PADRAO, PASTA, POCKETBASE_VERSAO, REGRAS_PADRAO

PASTA_SERVIDOR = os.path.join(PASTA, "servidor")
PASTA_DADOS = os.path.join(PASTA_SERVIDOR, "pb_data")
ARQUIVO_SENHAS = os.path.join(PASTA_SERVIDOR, "SENHAS-GUARDE-BEM.txt")


def _nome_binario():
    return "pocketbase.exe" if sys.platform == "win32" else "pocketbase"


def _alvo_download():
    so = {"windows": "windows", "linux": "linux", "darwin": "darwin"}.get(sys.platform.replace("win32", "windows")
                                                                           if sys.platform == "win32" else sys.platform, sys.platform)
    m = platform.machine().lower()
    arch = "arm64" if m in ("arm64", "aarch64") else "amd64"
    return so, arch


def baixar_pocketbase(log=print):
    destino = os.path.join(PASTA_SERVIDOR, _nome_binario())
    if os.path.exists(destino):
        return destino
    os.makedirs(PASTA_SERVIDOR, exist_ok=True)
    so, arch = _alvo_download()
    nome = f"pocketbase_{POCKETBASE_VERSAO}_{so}_{arch}.zip"
    url = f"https://github.com/pocketbase/pocketbase/releases/download/v{POCKETBASE_VERSAO}/{nome}"
    log(f"Baixando o PocketBase ({nome})...")
    zip_path = os.path.join(PASTA_SERVIDOR, nome)
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path) as z:
        z.extract(_nome_binario(), PASTA_SERVIDOR)
    os.remove(zip_path)
    if sys.platform != "win32":
        os.chmod(destino, 0o755)
    log("PocketBase pronto.")
    return destino


def _senha_guardada(chave, env):
    """Senha vinda do ambiente, ou gerada e guardada em arquivo local (uma vez)."""
    if os.environ.get(env):
        return os.environ[env], False
    guardadas = {}
    if os.path.exists(ARQUIVO_SENHAS):
        for linha in open(ARQUIVO_SENHAS, encoding="utf-8"):
            if "=" in linha:
                k, _, v = linha.strip().partition("=")
                guardadas[k] = v
    if chave in guardadas:
        return guardadas[chave], False
    nova = secrets.token_urlsafe(18)
    guardadas[chave] = nova
    os.makedirs(PASTA_SERVIDOR, exist_ok=True)
    with open(ARQUIVO_SENHAS, "w", encoding="utf-8") as f:
        f.write("# Guarde este arquivo num lugar seguro. Estas senhas não existem em outro lugar.\n")
        for k, v in guardadas.items():
            f.write(f"{k}={v}\n")
    return nova, True


def _esperar_servidor(base, proc=None, segundos=40):
    """Espera o servidor responder. Exige duas respostas seguidas (evita pegar
    a janelinha em que o serve aceita a conexão mas ainda está subindo)."""
    cli = api.Cliente(base, timeout=3)
    seguidas = 0
    for _ in range(segundos * 2):
        if proc is not None and proc.poll() is not None:
            return False  # o serve morreu
        try:
            cli.pedir("GET", "/api/health")
            seguidas += 1
            if seguidas >= 2:
                return True
        except api.ErroAPI:
            seguidas += 1
            if seguidas >= 2:
                return True
        except api.Offline:
            seguidas = 0
        time.sleep(0.5)
    return False


# ---------------------------------------------------------------- schema
def _txt(nome, obrigatorio=False, maximo=None):
    return {"name": nome, "type": "text", "required": obrigatorio, "unique": False,
            "options": {"min": None, "max": maximo, "pattern": ""}}


def _bool(nome):
    return {"name": nome, "type": "bool", "required": False, "options": {}}


def _rel(nome, col_id, obrigatorio=False):
    return {"name": nome, "type": "relation", "required": obrigatorio,
            "options": {"collectionId": col_id, "cascadeDelete": False, "minSelect": None,
                        "maxSelect": 1, "displayFields": None}}


def _json(nome):
    return {"name": nome, "type": "json", "required": False, "options": {"maxSize": 200000}}


def _num(nome):
    return {"name": nome, "type": "number", "required": False, "options": {"min": None, "max": None, "noDecimal": True}}


def _file(nome, maxsel, maxsize, mimes=None):
    return {"name": nome, "type": "file", "required": False,
            "options": {"mimeTypes": mimes or [], "thumbs": None, "maxSelect": maxsel, "maxSize": maxsize, "protected": False}}


def _com_ids(spec, atual):
    """Reaproveita os ids dos campos que já existem: rodar de novo não tenta recriá-los."""
    ids = {f["name"]: f["id"] for f in atual.get("schema", []) if f.get("id")}
    schema = [{**f, "id": ids[f["name"]]} if f["name"] in ids else f for f in spec.get("schema", [])]
    return {**spec, "id": atual["id"], "schema": schema}


def configurar_schema(cli):
    """Cria/atualiza as coleções e regras do fórum (idempotente)."""
    def upsert(spec):
        try:
            atual = cli.pedir("GET", "/api/collections/" + spec["name"])
            return cli.pedir("PATCH", "/api/collections/" + atual["id"], _com_ids(spec, atual))["id"]
        except api.ErroAPI as e:
            if e.codigo == 404:
                return cli.pedir("POST", "/api/collections", spec)["id"]
            raise

    users = cli.pedir("GET", "/api/collections/users")
    schema = [f for f in users["schema"] if f["name"] in ("name", "avatar")]
    ids = {f["name"]: f["id"] for f in users["schema"] if f.get("id")}  # rodar de novo não recria campos
    schema += [{**f, "id": ids[f["name"]]} if f["name"] in ids else f for f in
               [_txt("sobre", maximo=600), _txt("local", maximo=40), _bool("aprovado"), _bool("banido"),
                _txt("banido_motivo", maximo=300), _bool("autor")]]
    sem_escalar = ("@request.data.autor:isset = false && @request.data.aprovado:isset = false "
                   "&& @request.data.banido:isset = false && @request.data.banido_motivo:isset = false")
    cli.pedir("PATCH", "/api/collections/" + users["id"], {
        **users, "schema": schema, "listRule": "", "viewRule": "", "createRule": sem_escalar,
        "updateRule": "(@request.auth.id = id && " + sem_escalar + ") || @request.auth.autor = true",
        "deleteRule": None})
    uid = users["id"]

    cfg_id = upsert({"name": "config", "type": "base",
                     "schema": [_txt("regras_texto", maximo=4000), _txt("aviso", maximo=300),
                                _bool("so_aprovados"), _bool("qarchis_de_membros"), _json("categorias")],
                     "listRule": "", "viewRule": "", "createRule": None,
                     "updateRule": "@request.auth.autor = true", "deleteRule": None})

    aberto = "(@collection.config.so_aprovados = false || @request.auth.aprovado = true || @request.auth.autor = true)"
    pode_postar = ('@request.auth.id != "" && @request.auth.banido != true && '
                   "@request.data.autor = @request.auth.id && " + aberto)

    top_id = upsert({"name": "topicos", "type": "base",
                     "schema": [_txt("titulo", True, 140), _txt("texto", True, 20000), _txt("categoria", True, 40),
                                _rel("autor", uid, True), _bool("fixado")],
                     "listRule": "autor.banido != true", "viewRule": "autor.banido != true",
                     "createRule": pode_postar + " && @request.data.fixado:isset = false",
                     "updateRule": "@request.auth.autor = true",
                     "deleteRule": "@request.auth.id = autor || @request.auth.autor = true"})

    upsert({"name": "respostas", "type": "base",
            "schema": [_rel("topico", top_id, True), _txt("texto", True, 20000), _rel("autor", uid, True)],
            "listRule": "autor.banido != true && topico.autor.banido != true",
            "viewRule": "autor.banido != true && topico.autor.banido != true",
            "createRule": pode_postar, "updateRule": None,
            "deleteRule": "@request.auth.id = autor || @request.auth.autor = true"})

    upsert({"name": "curtidas", "type": "base",
            "schema": [_txt("alvo", True, 64), _rel("autor", uid, True)],
            "indexes": ["CREATE UNIQUE INDEX idx_curtida ON curtidas (alvo, autor)"],
            "listRule": "", "viewRule": "",
            "createRule": '@request.auth.id != "" && @request.auth.banido != true && @request.data.autor = @request.auth.id',
            "updateRule": None, "deleteRule": "@request.auth.id = autor"})

    upsert({"name": "qarchis", "type": "base",
            "schema": [_txt("nome", True, 140), _txt("descricao", maximo=2000), _rel("autor", uid, True),
                       _file("arquivos", 30, 524288000), _bool("aprovado")],
            "listRule": "aprovado = true || @request.auth.autor = true || @request.auth.id = autor",
            "viewRule": "aprovado = true || @request.auth.autor = true || @request.auth.id = autor",
            "createRule": ('@request.auth.id != "" && @request.auth.banido != true && '
                           "@request.data.autor = @request.auth.id && @request.data.aprovado:isset = false"),
            "updateRule": "@request.auth.autor = true",
            "deleteRule": "@request.auth.id = autor || @request.auth.autor = true"})

    configurar_comunidade(cli, uid, pode_postar)

    if not cli.listar("config", por_pagina=1):
        cli.criar("config", {"regras_texto": REGRAS_PADRAO, "aviso": "", "so_aprovados": False,
                             "qarchis_de_membros": True, "categorias": list(CATEGORIAS_PADRAO)})
    return cfg_id


IMAGENS = ["image/jpeg", "image/png", "image/webp", "image/gif"]
CANAIS_PADRAO = [  # (nome, descrição, só o autor posta)
    ("avisos-do-autor", "Novidades de Ailig Qarchi. Só o autor escreve aqui.", True),
    ("apresente-se", "Diga quem você é, de onde lê e como achou Wallace Ross.", False),
    ("conversa-geral", "Sobre a série, sobre livros, sobre a vida.", False),
    ("teorias", "Teorias e perguntas sobre o que já foi lido. Marque spoilers com ||assim||.", False),
    ("fan-art", "Desenhos, mapas, cartões e tudo o que a obra inspirar.", False),
    ("ideias", "Ideias para a série, o site e a comunidade.", False),
]


def configurar_comunidade(cli, uid, pode_postar):
    """A Comunidade do site (estilo Discord): canais, mensagens em tempo real,
    reações, mensagens diretas e denúncias. Mesmas regras de segurança do fórum:
    quem está banido não escreve, ninguém escreve em nome de outro, e só o autor
    cria canais e modera."""
    def upsert(spec):
        try:
            atual = cli.pedir("GET", "/api/collections/" + spec["name"])
            return cli.pedir("PATCH", "/api/collections/" + atual["id"], _com_ids(spec, atual))["id"]
        except api.ErroAPI as e:
            if e.codigo == 404:
                return cli.pedir("POST", "/api/collections", spec)["id"]
            raise

    so_autor = "@request.auth.autor = true"
    canal_id = upsert({"name": "canais", "type": "base",
                       "schema": [_txt("nome", True, 40), _txt("descricao", maximo=200), _num("ordem"), _bool("so_autor")],
                       "listRule": "", "viewRule": "", "createRule": so_autor, "updateRule": so_autor, "deleteRule": so_autor})
    upsert({"name": "mensagens", "type": "base",
            "schema": [_rel("canal", canal_id, True), _txt("texto", maximo=4000), _rel("autor", uid, True),
                       _txt("resposta", maximo=15), _file("imagem", 1, 5242880, IMAGENS), _bool("editado")],
            "indexes": ["CREATE INDEX idx_msg_canal ON mensagens (canal, created)"],
            "listRule": "autor.banido != true", "viewRule": "autor.banido != true",
            "createRule": pode_postar + " && (@request.data.canal.so_autor != true || @request.auth.autor = true)",
            "updateRule": ("@request.auth.id = autor && @request.auth.banido != true && @request.data.autor:isset = false "
                           "&& @request.data.canal:isset = false"),
            "deleteRule": "@request.auth.id = autor || @request.auth.autor = true"})
    upsert({"name": "reacoes", "type": "base",
            "schema": [_txt("mensagem", True, 15), _txt("emoji", True, 8), _rel("autor", uid, True)],
            "indexes": ["CREATE UNIQUE INDEX idx_reacao ON reacoes (mensagem, emoji, autor)"],
            "listRule": "", "viewRule": "",
            "createRule": '@request.auth.id != "" && @request.auth.banido != true && @request.data.autor = @request.auth.id',
            "updateRule": None, "deleteRule": "@request.auth.id = autor"})
    upsert({"name": "diretas", "type": "base",
            "schema": [_rel("de", uid, True), _rel("para", uid, True), _txt("texto", True, 4000)],
            "indexes": ["CREATE INDEX idx_dm ON diretas (de, para, created)"],
            "listRule": "@request.auth.id = de || @request.auth.id = para",
            "viewRule": "@request.auth.id = de || @request.auth.id = para",
            "createRule": ('@request.auth.id != "" && @request.auth.banido != true && @request.data.de = @request.auth.id '
                           "&& @request.data.para != @request.auth.id && @request.data.para.banido != true"),
            "updateRule": None, "deleteRule": "@request.auth.id = de"})
    upsert({"name": "denuncias", "type": "base",
            "schema": [_txt("alvo", True, 15), _txt("tipo", True, 20), _txt("motivo", maximo=500), _rel("autor", uid, True)],
            "listRule": so_autor, "viewRule": so_autor,
            "createRule": '@request.auth.id != "" && @request.data.autor = @request.auth.id',
            "updateRule": None, "deleteRule": so_autor})
    if not cli.listar("canais", por_pagina=1):
        for i, (nome, desc, so) in enumerate(CANAIS_PADRAO):
            cli.criar("canais", {"nome": nome, "descricao": desc, "ordem": i, "so_autor": so})


def garantir_autor(cli, usuario, senha):
    """Garante a conta do autor com autor=true (admin do fórum)."""
    existentes = cli.listar("users", filtro=f"username='{usuario}'", por_pagina=1)
    if existentes:
        cli.atualizar("users", existentes[0]["id"], {"autor": True, "aprovado": True, "banido": False})
        return existentes[0]["id"], False
    rec = cli.criar("users", {"username": usuario, "password": senha, "passwordConfirm": senha,
                              "name": "Ailig Qarchi", "sobre": "Autor de Wallace Ross.",
                              "autor": True, "aprovado": True})
    return rec["id"], True


def rodar(porta=8090, log=print):
    binario = baixar_pocketbase(log)
    senha_admin, nova_admin = _senha_guardada("PAINEL_POCKETBASE_SENHA", "SEMENTE_ADMIN_SENHA")
    senha_autor, nova_autor = _senha_guardada("AUTOR_SENHA", "SEMENTE_AUTOR_SENHA")
    email_admin = os.environ.get("SEMENTE_ADMIN_EMAIL", "autor@ailigqarchi.com.br")
    os.makedirs(PASTA_DADOS, exist_ok=True)

    # 1) migrações + superusuário do painel (ignora "já existe")
    subprocess.run([binario, "migrate", "up", "--dir", PASTA_DADOS], check=False)
    subprocess.run([binario, "admin", "create", email_admin, senha_admin, "--dir", PASTA_DADOS],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 2) sobe o servidor
    base = f"http://127.0.0.1:{porta}"
    proc = subprocess.Popen([binario, "serve", f"--http=127.0.0.1:{porta}", "--dir", PASTA_DADOS])
    try:
        if not _esperar_servidor(base, proc):
            log("O servidor não respondeu a tempo.")
            proc.terminate()
            return
        # 3) configura o fórum como superusuário (com algumas tentativas, caso
        #    o serve ainda esteja terminando de subir)
        cli = api.Cliente(base)
        for tentativa in range(8):
            try:
                d = cli.pedir("POST", "/api/admins/auth-with-password",
                              {"identity": email_admin, "password": senha_admin})
                cli.token = d["token"]
                break
            except api.Offline:
                time.sleep(1)
        else:
            log("Não consegui autenticar no servidor para configurá-lo.")
            proc.terminate()
            return
        log("Configurando o fórum...")
        configurar_schema(cli)
        garantir_autor(cli, AUTOR_USUARIO, senha_autor)

        log("\n" + "=" * 64)
        log("  Servidor da Semente no ar em " + base)
        log("  Painel do PocketBase: " + base + "/_/  (login: " + email_admin + ")")
        if nova_admin or nova_autor:
            log("  As senhas foram geradas e guardadas em:\n    " + ARQUIVO_SENHAS)
        log("  Conta de autor no app: usuário '" + AUTOR_USUARIO + "'")
        log("")
        log("  Falta você:")
        log("   • deixar esta máquina ligada enquanto quiser o fórum no ar;")
        log("   • expor este servidor na internet com o Cloudflare Tunnel apontando")
        log("     sementes.ailigqarchi.com.br para http://127.0.0.1:" + str(porta) + ";")
        log("   (o passo a passo do túnel está no README).")
        log("=" * 64 + "\n")
        proc.wait()
    except KeyboardInterrupt:
        log("Encerrando o servidor.")
    finally:
        if proc.poll() is None:
            proc.terminate()
