"""Configurações fixas do app. Edite aqui antes de gerar o .exe."""
import os

NOME = "Semente"
VERSAO = "3.0"

# Chave pública do admin (o autor). Ela vem da senha de admin: só quem sabe a
# senha consegue assinar como admin. Para trocar a senha, use o painel Admin
# (ele passa a coroa para a chave nova), sem precisar mexer aqui.
ADMIN_USUARIO = "ailigqarchi"
ADMIN_RAIZ = "6e88963f0487a5244274fe9ed1521225809cedb3f3a585f7756fe87562af4628"

# Pontos de encontro: computadores sempre ligados e alcançáveis pela internet
# (o PC do autor com a porta liberada, ou um servidor barato rodando
# "Semente.exe --servidor"). Sem pelo menos um, o fórum funciona só entre
# computadores da mesma rede local. Formato: "endereco:porta".
PONTOS_DE_ENCONTRO = [
    # "sementes.ailigqarchi.com.br:47474",
]

SITE = "https://ailigqarchi.com.br"
AMAZON = ""  # link do livro completo, quando estiver publicado

PORTA = 47474
PORTA_ANUNCIO = 47475

PASTA = os.path.join(os.path.expanduser("~"), "Semente_Wallace_Ross")
PASTA_QARCHIS = os.path.join(PASTA, "qarchis")
CONFIG = os.path.join(PASTA, "config.json")
BANCO = os.path.join(PASTA, "forum.db")

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
