import argparse
import sys
import time


def main():
    ap = argparse.ArgumentParser(prog="Semente", description="O fórum dos leitores de Wallace Ross, com qarchis.")
    ap.add_argument("qarchi", nargs="?", help="um arquivo .qarchi para plantar")
    ap.add_argument("--servidor", action="store_true", help="roda só o nó (ponto de encontro), sem janela")
    ap.add_argument("--porta", type=int, default=None, help="porta do nó (padrão 47474)")
    ap.add_argument("--importar", metavar="PASTA", help="coloca as amostras oficiais que estão nesta pasta")
    a = ap.parse_args()

    if a.servidor or a.importar:
        from .nucleo import Nucleo
        n = Nucleo(log=lambda m: print(time.strftime("%H:%M:%S"), m, flush=True))
        if a.importar:
            print("arquivos importados:", n.importar_pasta(a.importar))
            if not a.servidor:
                return
        n.no.iniciar_servidor(a.porta)
        n.iniciar_rede(True)
        print("Ponto de encontro ativo. Libere a porta", n.no.porta, "(TCP) no roteador/firewall. Ctrl+C para sair.", flush=True)
        try:
            while True:
                time.sleep(30)
                print(time.strftime("%H:%M:%S"), f"pares {len(n.no.vivos())} · eventos v{n.banco.versao}", flush=True)
        except KeyboardInterrupt:
            return
    from .janela import App
    App(abrir_qarchi=a.qarchi).rodar()


if __name__ == "__main__":
    sys.exit(main())
