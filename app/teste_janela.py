"""Teste de fumaça: monta a janela inteira e fecha sozinha.

Usado no GitHub Actions para pegar erros de opção de widget do Tkinter que o
simples 'import' não pega (o servidor é apontado para um endereço morto, então
o app roda offline). Se o Tk nem conseguir iniciar (runner sem display), o
teste é pulado em vez de quebrar o build.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SEMENTE_AUTOTESTE", "1")
os.environ.setdefault("SEMENTE_SERVIDOR", "http://127.0.0.1:1")

import tkinter

try:
    _r = tkinter.Tk()
    _r.destroy()
except tkinter.TclError as e:
    print("Sem display; teste de janela pulado:", e)
    sys.exit(0)

from semente.janela import App

App().rodar()
print("janela ok")
