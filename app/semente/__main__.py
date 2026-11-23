import argparse
import sys


def main():
    ap = argparse.ArgumentParser(prog="Semente", description="O fórum dos leitores de Wallace Ross.")
    ap.add_argument("--servidor", action="store_true",
                    help="roda o servidor do fórum (PocketBase) nesta máquina, para o autor manter ligado")
    ap.add_argument("--porta", type=int, default=8090, help="porta do servidor (padrão 8090)")
    a = ap.parse_args()

    if a.servidor:
        from .servidor import rodar
        rodar(porta=a.porta, log=lambda *m: print(*m, flush=True))
        return

    from .janela import App
    App().rodar()


if __name__ == "__main__":
    sys.exit(main())
