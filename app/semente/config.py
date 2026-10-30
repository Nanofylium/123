"""Configurações fixas do app. Edite aqui antes de gerar o .exe."""
import os

NOME = "Semente"
VERSAO = "4.0"

# Endereço do servidor da Semente (o PocketBase que o autor mantém ligado).
# É um nome (DNS), não um IP, então o computador por trás dele pode mudar sem
# gerar um .exe novo. O Cloudflare Tunnel aponta esse nome para o laptop do
# autor. Para testar contra um servidor local, defina a variável de ambiente
# SEMENTE_SERVIDOR (ex.: http://127.0.0.1:8090) ou o campo "servidor" no
# config.json da pasta do app.
SERVIDOR = "https://sementes.ailigqarchi.com.br"

# Usuário do autor (admin) no servidor. Quem entra com esse usuário e a senha
# de autor ganha o painel ✦ Admin. A senha é definida quando o servidor sobe
# pela primeira vez (veja servidor.py), não fica aqui.
AUTOR_USUARIO = "ailigqarchi"

SITE = "https://ailigqarchi.com.br"
AMAZON = ""  # link do livro completo, quando estiver publicado

# Versão do PocketBase que o modo servidor baixa e roda.
POCKETBASE_VERSAO = "0.22.21"

PASTA = os.path.join(os.path.expanduser("~"), "Semente_Wallace_Ross")
PASTA_DOWNLOADS = os.path.join(PASTA, "downloads")
CONFIG = os.path.join(PASTA, "config.json")

CATEGORIAS_PADRAO = ["Avisos do autor", "Wallace Ross", "Teorias e perguntas", "Leituras em grupo", "Qarchis", "Conversa livre"]
REGRAS_PADRAO = """1. Respeito sempre. Nada de ataques, preconceito, assédio ou ameaças.
2. Nada de pirataria: o livro completo é vendido na Amazon. Qarchis só com conteúdo que você tem o direito de compartilhar.
3. Spoilers do livro completo vão marcados no título com [SPOILER].
4. Nada de dados pessoais seus ou de outras pessoas (endereço, telefone, documentos).
5. O autor modera. Quem quebrar as regras pode ter posts apagados ou ser removido."""

# Paleta do site (projeto Lovable): noite azul e engrenagens douradas
COR = {
    "fundo": "#14152b", "painel": "#1b1d3d", "cartao": "#232651", "linha": "#3b3a5c",
    "texto": "#f1e9d8", "suave": "#a9adc9", "ouro": "#e2b85f", "ouro_claro": "#f5d98f",
    "ouro_escuro": "#a9802f", "azul": "#3a4fb8", "perigo": "#e07a6a", "ok": "#8fd18a",
}
