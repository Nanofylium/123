"""O núcleo do app: conta, fórum, qarchis e poderes do admin, sem janela."""
import json
import os
import shutil
import threading

from . import cripto, dados, qarchi as qmod
from .config import BANCO, CONFIG, PASTA, PASTA_QARCHIS, ADMIN_USUARIO
from .rede import No
from .oficial import EVENTOS_INICIAIS, QARCHI_OFICIAL


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


class Erro(Exception):
    pass


class Nucleo:
    def __init__(self, log=print, pasta=None):
        os.makedirs(PASTA_QARCHIS, exist_ok=True)
        self.log = log
        self.cfg = ler_cfg()
        self.banco = dados.Banco(BANCO)
        for ev in EVENTOS_INICIAIS:
            self.banco.adicionar(ev, recalcular=False)
        self.banco.recalcular()
        self.no = No(self.banco, PASTA_QARCHIS, log)
        self.no.configurar(self.cfg.get("limite_kbps", 512), self.cfg.get("conexoes", 6))
        for p in self.cfg.get("pares", []):
            self.no.conhecer(p, fixo=True)
        self.sk = None
        self.pub = None
        # o qarchi oficial (as amostras) e os que a pessoa já plantou
        self.no.plantar(QARCHI_OFICIAL)
        for q in self.cfg.get("qarchis", []):
            try:
                if qmod.valido(q):
                    self.no.plantar(q)
            except (OSError, ValueError):
                pass
        self.no.pausados = set(self.cfg.get("pausados", []))

    @property
    def estado(self):
        return self.banco.estado

    def iniciar_rede(self, compartilhar):
        self.cfg["compartilhar"] = compartilhar
        gravar_cfg(self.cfg)
        if compartilhar:
            self.no.iniciar_servidor()
        threading.Thread(target=self.no.escutar, daemon=True).start()
        threading.Thread(target=self.no.sincronizar_sempre, daemon=True).start()
        threading.Thread(target=self.no.cultivar_sempre, daemon=True).start()

    def alternar_compartilhar(self, sim):
        self.cfg["compartilhar"] = sim
        gravar_cfg(self.cfg)
        self.no.iniciar_servidor() if sim else self.no.parar_servidor()

    # ------------------------------------------------------------ conta
    def entrar(self, usuario, senha):
        usuario = usuario.strip().lower()
        sk = cripto.chave_da_senha(usuario, senha)
        pub = cripto.publica(sk)
        perfil = self.estado.perfis.get(pub)
        if pub == self.estado.admin:
            self._sessao(sk, pub, usuario)
            if not perfil:
                self.publicar("perfil", {"usuario": ADMIN_USUARIO, "nome": "Ailig Qarchi", "sobre": "Autor de Wallace Ross."})
            return pub
        if pub in self.estado.banidos:
            raise Erro("Esta conta foi removida pelo autor. Motivo: " + (self.estado.banidos[pub] or "não informado"))
        if not perfil or perfil["usuario"] != usuario:
            raise Erro("Usuário ou senha incorretos. (Se você criou a conta agora e está em outro computador, "
                       "espere o fórum sincronizar e tente de novo.)")
        self._sessao(sk, pub, usuario)
        return pub

    def cadastrar(self, usuario, senha, nome, sobre=""):
        usuario = usuario.strip().lower()
        if not dados.USUARIO_OK.match(usuario):
            raise Erro("O usuário deve ter de 3 a 24 letras minúsculas, números, ponto ou _.")
        if any(r in usuario for r in dados.NOMES_RESERVADOS):
            raise Erro("Esse nome de usuário é reservado.")
        if usuario in self.estado.donos_usuario:
            raise Erro("Esse nome de usuário já existe. Escolha outro.")
        if len(senha) < 10:
            raise Erro("A senha precisa ter pelo menos 10 caracteres.")
        if not nome.strip():
            raise Erro("Diga como quer ser chamado.")
        sk = cripto.chave_da_senha(usuario, senha)
        pub = cripto.publica(sk)
        if pub in self.estado.banidos:
            raise Erro("Esta conta foi removida pelo autor.")
        self._sessao(sk, pub, usuario)
        self.publicar("perfil", {"usuario": usuario, "nome": nome.strip()[:40], "sobre": sobre.strip()[:600]})
        return pub

    def _sessao(self, sk, pub, usuario):
        self.sk, self.pub = sk, pub
        self.no.minha_pub = pub
        self.cfg["ultimo_usuario"] = usuario
        gravar_cfg(self.cfg)

    def sair(self):
        self.sk = self.pub = None
        self.no.minha_pub = None

    def e_admin(self):
        return self.pub is not None and self.pub == self.estado.admin

    # ------------------------------------------------------------ publicar
    def publicar(self, tipo, conteudo):
        if not self.sk:
            raise Erro("Entre na sua conta primeiro.")
        if tipo in dados.TIPOS_ADMIN and not self.e_admin():
            raise Erro("Só o autor pode fazer isso.")
        if tipo not in ("perfil", "apagar") and tipo not in dados.TIPOS_ADMIN and not self.estado.pode_postar(self.pub):
            raise Erro("Sua conta ainda não foi aprovada pelo autor, ou foi suspensa.")
        ev = dados.criar_evento(self.sk, tipo, conteudo)
        if not dados.formato_valido(ev):
            raise Erro("O conteúdo não está no formato certo (tamanho ou campos).")
        self.no.publicar(ev)
        return ev

    def novo_topico(self, titulo, texto, categoria):
        return self.publicar("topico", {"titulo": titulo.strip(), "texto": texto.strip(), "categoria": categoria})

    def responder(self, topico_id, texto):
        return self.publicar("resposta", {"topico": topico_id, "texto": texto.strip()})

    def curtir(self, alvo):
        if self.pub in self.estado.curtidas.get(alvo, set()):
            return None
        return self.publicar("curtida", {"alvo": alvo})

    def apagar(self, alvo):
        return self.publicar("apagar", {"alvo": alvo})

    def editar_perfil(self, nome, sobre):
        u = self.estado.perfis.get(self.pub, {}).get("usuario") or self.cfg.get("ultimo_usuario")
        return self.publicar("perfil", {"usuario": u, "nome": nome.strip()[:40], "sobre": sobre.strip()[:600]})

    # ------------------------------------------------------------ qarchis
    def cultivar(self, arquivos, nome, descricao, publicar_no_forum=True):
        if not self.sk:
            raise Erro("Entre na sua conta primeiro.")
        if not self.e_admin() and not self.estado.regras.get("qarchis_de_membros", True):
            raise Erro("No momento só o autor pode cultivar qarchis.")
        q = qmod.cultivar(arquivos, nome, descricao, self.sk)
        lav = self.no.plantar(q)
        # copia os arquivos para a pasta do qarchi (é de lá que ele é servido)
        origens = qmod.mapa_relativo(arquivos)
        for a in q["info"]["arquivos"]:
            destino = os.path.join(lav.pasta, *a["caminho"].split("/"))
            if os.path.abspath(origens[a["caminho"]]) != os.path.abspath(destino):
                shutil.copyfile(origens[a["caminho"]], destino)
        lav.tem = [lav._confere(i) for i in range(len(lav.tem))]
        self._lembrar(q)
        if publicar_no_forum:
            self.publicar("qarchi", {"qarchi": q, "descricao": descricao.strip()[:2000]})
        return q

    def importar_pasta(self, pasta, qid=None):
        """Coloca arquivos que você já tem dentro de um qarchi (só entram se conferirem)."""
        lav = self.no.lavouras[qid or QARCHI_OFICIAL["qid"]]
        n = 0
        for a in lav.info["arquivos"]:
            origem = os.path.join(pasta, *a["caminho"].split("/"))
            if os.path.exists(origem) and os.path.getsize(origem) == a["tamanho"]:
                shutil.copyfile(origem, lav._caminho(a))
                n += 1
        lav.tem = [lav._confere(i) for i in range(len(lav.tem))]
        return n

    def plantar_arquivo(self, caminho):
        q = qmod.abrir(caminho)
        return self.plantar(q)

    def plantar(self, q):
        if q["qid"] != QARCHI_OFICIAL["qid"] and not self.estado.qarchi_liberado(q["qid"]) \
                and q["cultivador"] != self.pub and not self.e_admin():
            raise Erro("Este qarchi ainda não foi aprovado pelo autor, então não circula no fórum.")
        lav = self.no.plantar(q)
        self._lembrar(q)
        return lav

    def _lembrar(self, q):
        lista = [x for x in self.cfg.get("qarchis", []) if x.get("qid") != q["qid"]]
        if q["qid"] != QARCHI_OFICIAL["qid"]:
            lista.append(q)
        self.cfg["qarchis"] = lista
        gravar_cfg(self.cfg)

    def esquecer(self, qid):
        if qid == QARCHI_OFICIAL["qid"]:
            raise Erro("As amostras oficiais ficam sempre aqui.")
        self.no.remover(qid)
        self.cfg["qarchis"] = [x for x in self.cfg.get("qarchis", []) if x.get("qid") != qid]
        gravar_cfg(self.cfg)

    def pausar(self, qid, sim):
        (self.no.pausados.add if sim else self.no.pausados.discard)(qid)
        self.cfg["pausados"] = sorted(self.no.pausados)
        gravar_cfg(self.cfg)

    # ------------------------------------------------------------ admin
    def admin(self, tipo, **conteudo):
        return self.publicar(tipo, conteudo)

    def trocar_senha_admin(self, nova_senha):
        if not self.e_admin():
            raise Erro("Só o autor pode fazer isso.")
        if len(nova_senha) < 20:
            raise Erro("Use uma senha de admin com pelo menos 20 caracteres.")
        sk_novo = cripto.chave_da_senha(ADMIN_USUARIO, nova_senha)
        pub_novo = cripto.publica(sk_novo)
        self.publicar("novo_admin", {"pub": pub_novo})
        self._sessao(sk_novo, pub_novo, ADMIN_USUARIO)
        self.publicar("perfil", {"usuario": ADMIN_USUARIO, "nome": "Ailig Qarchi", "sobre": "Autor de Wallace Ross."})
        return pub_novo
