"""Gera app/semente/oficial.py: o qarchi das amostras e os eventos iniciais,
assinados pelo admin. Rode de novo quando as amostras mudarem:

    SEMENTE_SENHA_ADMIN='...' python3 tools/gerar_oficial.py

A senha nunca é gravada em lugar nenhum.
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "app"))
# oficial.py ainda pode não existir: cria um vazio para o pacote importar
alvo = os.path.join(RAIZ, "app", "semente", "oficial.py")
if not os.path.exists(alvo):
    open(alvo, "w").write("EVENTOS_INICIAIS = []\nQARCHI_OFICIAL = None\n")

from semente import cripto, dados, qarchi  # noqa: E402
from semente.config import ADMIN_USUARIO, ADMIN_RAIZ, SITE  # noqa: E402

senha = os.environ.get("SEMENTE_SENHA_ADMIN") or sys.exit("Defina SEMENTE_SENHA_ADMIN.")
sk = cripto.chave_da_senha(ADMIN_USUARIO, senha)
if cripto.publica(sk) != ADMIN_RAIZ:
    sys.exit("Essa senha não é a do admin configurado em config.py.")

pasta = os.path.join(RAIZ, "site", "amostras")
arquivos = sorted(os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith((".pdf", ".epub")))
q = qarchi.cultivar(arquivos, "Wallace Ross: amostras oficiais (6 idiomas)",
                    "Prólogo e começo do livro em português, inglês, espanhol, mandarim, hindi e árabe. "
                    "Gratuito para compartilhar, sem alterações e sem cobrança.",
                    sk, base=pasta, fontes=[SITE + "/amostras"])
t0 = q["info"]["criado"]
evs = [
    dados.criar_evento(sk, "perfil", {"usuario": ADMIN_USUARIO, "nome": "Ailig Qarchi", "sobre": "Autor de Wallace Ross."}, t0),
    dados.criar_evento(sk, "qarchi", {"qarchi": q, "descricao": q["info"]["descricao"]}, t0 + 1),
    dados.criar_evento(sk, "topico", {"categoria": "Avisos do autor", "titulo": "Bem-vindos à Semente",
                                      "texto": "Este é o lugar dos leitores de Wallace Ross. Leiam as regras, apresentem-se, "
                                               "contem o que acharam do começo do livro e passem as amostras adiante. "
                                               "Eu leio tudo por aqui.\n\nAilig Qarchi"}, t0 + 2),
]
evs.append(dados.criar_evento(sk, "fixar", {"topico": evs[2]["id"], "fixo": True}, t0 + 3))
assert all(dados.formato_valido(e) for e in evs) and qarchi.valido(q)
with open(alvo, "w", encoding="utf-8") as f:
    f.write("# Gerado por tools/gerar_oficial.py. Assinado pelo admin; não editar à mão.\n")
    f.write("import json\n\nEVENTOS_INICIAIS = json.loads(r\'\'\'" + json.dumps(evs, ensure_ascii=False, indent=1) + "\'\'\')\n")
    f.write("QARCHI_OFICIAL = EVENTOS_INICIAIS[1][\"dados\"][\"qarchi\"]\n")
print("ok:", q["qid"])
