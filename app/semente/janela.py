"""A janela da Semente (Tkinter), com a paleta do site: noite azul e engrenagens douradas.

A Semente é um cliente: tudo que aparece aqui vem do servidor que o autor
mantém ligado. Não há rede entre computadores dos leitores.
"""
import os
import queue
import sys
import threading
import time
import webbrowser

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from . import assets
from .config import COR, NOME, VERSAO, SITE, AMAZON, PASTA, PASTA_DOWNLOADS
from .nucleo import Nucleo, Erro

C = COR
FONTE = ("Segoe UI", 10) if sys.platform == "win32" else ("TkDefaultFont", 10)
FAM = FONTE[0]


def tamanho(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def quando(t):
    d = int(time.time() - t)
    if d < 60:
        return "agora"
    if d < 3600:
        return f"há {d // 60} min"
    if d < 86400:
        return f"há {d // 3600} h"
    if d < 86400 * 7:
        return f"há {d // 86400} d"
    return time.strftime("%d/%m/%Y", time.localtime(t))


def aplicar_tema(raiz):
    raiz.configure(bg=C["fundo"])
    e = ttk.Style(raiz)
    e.theme_use("clam")
    e.configure(".", background=C["fundo"], foreground=C["texto"], fieldbackground=C["cartao"], bordercolor=C["linha"],
                darkcolor=C["fundo"], lightcolor=C["linha"], troughcolor=C["painel"], focuscolor=C["ouro"],
                selectbackground=C["ouro_escuro"], selectforeground=C["fundo"], insertcolor=C["ouro"], font=FONTE)
    e.configure("TFrame", background=C["fundo"])
    e.configure("Painel.TFrame", background=C["painel"])
    e.configure("Cartao.TFrame", background=C["cartao"])
    e.configure("TLabel", background=C["fundo"], foreground=C["texto"])
    e.configure("Painel.TLabel", background=C["painel"], foreground=C["texto"])
    e.configure("Suave.TLabel", background=C["fundo"], foreground=C["suave"])
    e.configure("PainelSuave.TLabel", background=C["painel"], foreground=C["suave"])
    e.configure("Secao.TLabel", background=C["painel"], foreground=C["ouro"], font=(FAM, 8, "bold"))
    e.configure("Titulo.TLabel", background=C["fundo"], foreground=C["ouro"], font=(FAM, 16, "bold"))
    e.configure("Marca.TLabel", background=C["painel"], foreground=C["ouro"], font=(FAM, 15, "bold"))
    e.configure("TButton", background=C["cartao"], foreground=C["ouro"], bordercolor=C["ouro_escuro"], padding=(10, 5),
                focusthickness=1, focuscolor=C["ouro"])
    e.map("TButton", background=[("active", C["ouro"]), ("disabled", C["painel"])],
          foreground=[("active", C["fundo"]), ("disabled", C["linha"])])
    e.configure("Ouro.TButton", background=C["ouro"], foreground=C["fundo"], font=(FAM, 10, "bold"))
    e.map("Ouro.TButton", background=[("active", C["ouro_claro"])])
    e.configure("Perigo.TButton", foreground=C["perigo"], bordercolor=C["perigo"])
    e.map("Perigo.TButton", background=[("active", C["perigo"])], foreground=[("active", C["fundo"])])
    for w in ("TRadiobutton", "TCheckbutton"):
        e.configure(w, background=C["painel"], foreground=C["texto"], indicatorcolor=C["cartao"], indicatorbackground=C["cartao"])
        e.map(w, background=[("active", C["cartao"])], indicatorcolor=[("selected", C["ouro"])], foreground=[("active", C["ouro_claro"])])
    e.configure("Fundo.TCheckbutton", background=C["fundo"])
    e.configure("TEntry", fieldbackground=C["cartao"], foreground=C["texto"], insertcolor=C["ouro"], bordercolor=C["linha"], padding=5)
    e.map("TEntry", bordercolor=[("focus", C["ouro"])])
    e.configure("TCombobox", fieldbackground=C["cartao"], foreground=C["texto"], background=C["cartao"], arrowcolor=C["ouro"])
    e.map("TCombobox", fieldbackground=[("readonly", C["cartao"])], foreground=[("readonly", C["texto"])])
    e.configure("TNotebook", background=C["fundo"], borderwidth=0, tabmargins=(6, 4, 6, 0))
    e.configure("TNotebook.Tab", background=C["painel"], foreground=C["suave"], padding=(16, 7), borderwidth=0, font=(FAM, 10))
    e.map("TNotebook.Tab", background=[("selected", C["fundo"])], foreground=[("selected", C["ouro"])])
    e.configure("Treeview", background=C["cartao"], fieldbackground=C["cartao"], foreground=C["texto"], rowheight=28, borderwidth=0)
    e.map("Treeview", background=[("selected", C["ouro_escuro"])], foreground=[("selected", C["fundo"])])
    e.configure("Treeview.Heading", background=C["painel"], foreground=C["ouro"], relief="flat", font=(FAM, 9, "bold"), padding=(6, 5))
    e.map("Treeview.Heading", background=[("active", C["cartao"])])
    e.configure("TScrollbar", background=C["painel"], troughcolor=C["fundo"], arrowcolor=C["ouro"], bordercolor=C["fundo"])
    e.configure("TPanedwindow", background=C["linha"])
    e.configure("TSeparator", background=C["linha"])
    raiz.option_add("*TCombobox*Listbox.background", C["cartao"])
    raiz.option_add("*TCombobox*Listbox.foreground", C["texto"])
    raiz.option_add("*TCombobox*Listbox.selectBackground", C["ouro_escuro"])


def texto_tk(pai, **kw):
    t = tk.Text(pai, bg=C["cartao"], fg=C["texto"], insertbackground=C["ouro"], relief="flat", padx=12, pady=10,
                wrap="word", highlightthickness=1, highlightbackground=C["linha"], highlightcolor=C["ouro"],
                selectbackground=C["ouro_escuro"], selectforeground=C["fundo"], font=(FAM, 11), **kw)
    return t


class App:
    def __init__(self):
        self.registro = queue.Queue()
        self.n = Nucleo(log=lambda m: self.registro.put(f"{time.strftime('%H:%M:%S')}  {m}"))
        self.raiz = tk.Tk()
        self.raiz.title(f"{NOME} · Wallace Ross")
        self.raiz.geometry("1180x740")
        self.raiz.minsize(900, 580)
        aplicar_tema(self.raiz)
        self.img_quadros = [tk.PhotoImage(data=q) for q in assets.ENGRENAGEM_QUADROS]
        self.img_icone = tk.PhotoImage(data=assets.ENGRENAGEM_ICONE)
        self.img_fundo_azul = tk.PhotoImage(data=assets.ENGRENAGEM_FUNDO_AZUL)
        self.img_fundo_ouro = tk.PhotoImage(data=assets.ENGRENAGEM_FUNDO_OURO)
        self.raiz.iconphoto(True, self.img_icone)
        self.versao_vista = -1
        self.topico_aberto = None
        self._cabecalho()
        self.corpo = ttk.Frame(self.raiz)
        self.corpo.pack(fill="both", expand=True)
        # conecta ao servidor e começa a sincronizar em segundo plano
        self.n.iniciar()
        self.tela_entrada()
        self._girar(0)
        self._ciclo()

    # ------------------------------------------------------------ moldura
    def _cabecalho(self):
        topo = ttk.Frame(self.raiz, style="Painel.TFrame", padding=(12, 6))
        topo.pack(fill="x")
        self.engrenagem = tk.Canvas(topo, width=46, height=46, bg=C["painel"], highlightthickness=0)
        self.engrenagem.pack(side="left")
        self.eng_id = self.engrenagem.create_image(23, 23, image=self.img_quadros[0])
        ttk.Label(topo, text=" SEMENTE", style="Marca.TLabel").pack(side="left")
        ttk.Label(topo, text="   Wallace Ross · Ailig Qarchi", style="PainelSuave.TLabel").pack(side="left")
        self.lbl_usuario = ttk.Label(topo, text="", style="Painel.TLabel")
        self.lbl_usuario.pack(side="right", padx=(12, 0))
        self.lbl_resumo = ttk.Label(topo, text="", style="PainelSuave.TLabel")
        self.lbl_resumo.pack(side="right")
        tk.Frame(self.raiz, height=2, bg=C["ouro_escuro"]).pack(fill="x")

    def _girar(self, i):
        self.engrenagem.itemconfigure(self.eng_id, image=self.img_quadros[i % len(self.img_quadros)])
        self.raiz.after(90, lambda: self._girar(i + 1))

    def limpar_corpo(self):
        for w in self.corpo.winfo_children():
            w.destroy()

    def erro(self, e):
        messagebox.showerror(NOME, str(e), parent=self.raiz)

    # ------------------------------------------------------------ entrada
    def tela_entrada(self):
        self.limpar_corpo()
        self.lbl_usuario.config(text="")
        f = ttk.Frame(self.corpo)
        f.pack(fill="both", expand=True)
        tk.Label(f, image=self.img_fundo_azul, bg=C["fundo"]).place(relx=0.08, rely=0.55, anchor="center")
        tk.Label(f, image=self.img_fundo_ouro, bg=C["fundo"]).place(relx=0.92, rely=0.25, anchor="center")
        caixa = ttk.Frame(f, style="Cartao.TFrame", padding=28)
        caixa.place(relx=0.5, rely=0.48, anchor="center")
        tk.Label(caixa, image=self.img_icone, bg=C["cartao"]).pack()
        tk.Label(caixa, text="O fórum dos leitores", bg=C["cartao"], fg=C["ouro"], font=(FAM, 18, "bold")).pack(pady=(6, 0))
        tk.Label(caixa, text="Converse com outros leitores e com o autor,\ne baixe as amostras do livro.",
                 bg=C["cartao"], fg=C["suave"], font=(FAM, 10), justify="center").pack(pady=(4, 14))
        abas = ttk.Notebook(caixa)
        abas.pack(fill="x")
        # entrar
        e1 = ttk.Frame(abas, padding=14)
        abas.add(e1, text="Entrar")
        u = tk.StringVar(value=self.n.cfg.get("ultimo_usuario", ""))
        s = tk.StringVar()
        ttk.Label(e1, text="Usuário").pack(anchor="w")
        eu = ttk.Entry(e1, textvariable=u, width=34)
        eu.pack(fill="x", pady=(2, 8))
        ttk.Label(e1, text="Senha").pack(anchor="w")
        es = ttk.Entry(e1, textvariable=s, show="•", width=34)
        es.pack(fill="x", pady=(2, 12))

        def entrar(*_):
            try:
                self.n.entrar(u.get(), s.get())
            except Erro as ex:
                return self.erro(ex)
            self.tela_principal()
        ttk.Button(e1, text="Entrar", style="Ouro.TButton", command=entrar).pack(fill="x")
        es.bind("<Return>", entrar)
        # cadastro
        e2 = ttk.Frame(abas, padding=14)
        abas.add(e2, text="Criar conta")
        cu, cn, cs, cs2 = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
        for rot, var, show in (("Usuário (letras minúsculas, números, . ou _)", cu, None), ("Como quer ser chamado", cn, None),
                               ("Senha (mínimo 10 caracteres)", cs, "•"), ("Repita a senha", cs2, "•")):
            ttk.Label(e2, text=rot).pack(anchor="w")
            ttk.Entry(e2, textvariable=var, show=show or "", width=34).pack(fill="x", pady=(2, 8))

        def cadastrar():
            if cs.get() != cs2.get():
                return self.erro("As senhas não são iguais.")
            try:
                self.n.cadastrar(cu.get(), cs.get(), cn.get())
            except Erro as ex:
                return self.erro(ex)
            self.tela_principal()
        ttk.Button(e2, text="Criar conta", style="Ouro.TButton", command=cadastrar).pack(fill="x")
        ttk.Button(caixa, text="Só ler, sem entrar", command=self.tela_principal).pack(fill="x", pady=(12, 0))
        self.lbl_conexao = tk.Label(caixa, text="", bg=C["cartao"], fg=C["suave"], font=(FAM, 9))
        self.lbl_conexao.pack(pady=(10, 0))
        self._mostrar_conexao()
        (eu if not u.get() else es).focus_set()

    def _mostrar_conexao(self):
        if not hasattr(self, "lbl_conexao") or not self.lbl_conexao.winfo_exists():
            return
        if self.n.online:
            self.lbl_conexao.config(text="● Conectado ao servidor da Semente.", foreground=C["ok"])
        else:
            self.lbl_conexao.config(text="○ Sem conexão com o servidor. O laptop do autor pode\nestar desligado agora. Você ainda pode tentar entrar.",
                                    foreground=C["perigo"])

    # ------------------------------------------------------------ principal
    def tela_principal(self):
        self.limpar_corpo()
        est = self.n.estado
        if self.n.pub:
            self.lbl_usuario.config(text=f"{est.nome(self.n.pub)}  {est.usuario(self.n.pub)}" + ("  ✦ ADMIN" if self.n.e_admin() else ""),
                                    foreground=C["ouro"] if self.n.e_admin() else C["texto"])
        else:
            self.lbl_usuario.config(text="lendo sem conta")
        self.abas = ttk.Notebook(self.corpo)
        self.abas.pack(fill="both", expand=True, pady=(4, 0))
        self.aba_forum()
        self.aba_qarchis()
        self.aba_membros()
        self.aba_regras()
        self.aba_perfil()
        if self.n.e_admin():
            self.aba_admin()
        self.aba_sobre()
        self.versao_vista = -1

    def lateral(self, pai):
        lat = ttk.Frame(pai, style="Painel.TFrame", padding=(12, 12), width=200)
        tk.Label(lat, image=self.img_fundo_ouro, bg=C["painel"]).place(relx=0.5, rely=1.0, anchor="s")
        return lat

    # ---------------- FÓRUM ----------------
    def aba_forum(self):
        aba = ttk.Frame(self.abas)
        self.abas.add(aba, text="  Fórum  ")
        pan = ttk.PanedWindow(aba, orient="horizontal")
        pan.pack(fill="both", expand=True)
        lat = self.lateral(pan)
        pan.add(lat, weight=0)
        ttk.Label(lat, text="CATEGORIAS", style="Secao.TLabel").pack(anchor="w", pady=(0, 6))
        self.cat = tk.StringVar(value="")
        self.cat_frame = ttk.Frame(lat, style="Painel.TFrame")
        self.cat_frame.pack(anchor="w", fill="x")
        ttk.Separator(lat).pack(fill="x", pady=10)
        self.btn_novo = ttk.Button(lat, text="＋ Novo tópico", style="Ouro.TButton", command=self.novo_topico)
        self.btn_novo.pack(fill="x")
        self.lbl_aviso = tk.Label(lat, text="", bg=C["painel"], fg=C["ouro_claro"], wraplength=180, justify="left", font=(FAM, 9))
        self.lbl_aviso.pack(anchor="w", pady=10)
        self.forum_dir = ttk.Frame(pan, padding=10)
        pan.add(self.forum_dir, weight=1)
        self.mostrar_lista_topicos()

    def desenhar_categorias(self):
        for w in self.cat_frame.winfo_children():
            w.destroy()
        for c in [""] + list(self.n.estado.regras["categorias"]):
            ttk.Radiobutton(self.cat_frame, text=c or "Todos os tópicos", value=c, variable=self.cat,
                            command=self.mostrar_lista_topicos).pack(anchor="w", pady=1)
        self.lbl_aviso.config(text=("📣 " + self.n.estado.aviso) if self.n.estado.aviso else "")

    def mostrar_lista_topicos(self):
        self.topico_aberto = None
        for w in self.forum_dir.winfo_children():
            w.destroy()
        self.desenhar_categorias()
        ttk.Label(self.forum_dir, text=self.cat.get() or "Todos os tópicos", style="Titulo.TLabel").pack(anchor="w", pady=(0, 8))
        cols = ("titulo", "autor", "resp", "curt", "ult")
        self.tv_topicos = ttk.Treeview(self.forum_dir, columns=cols, show="headings")
        for c, t, w in (("titulo", "Tópico", 420), ("autor", "Autor", 160), ("resp", "Respostas", 80), ("curt", "♥", 50), ("ult", "Atividade", 110)):
            self.tv_topicos.heading(c, text=t)
            self.tv_topicos.column(c, width=w, anchor="w" if c in ("titulo", "autor") else "center")
        self.tv_topicos.tag_configure("autor", foreground=C["ouro_claro"])
        self.tv_topicos.tag_configure("fixo", foreground=C["ouro"])
        self.tv_topicos.pack(fill="both", expand=True)
        self.tv_topicos.bind("<Double-1>", lambda e: self.abrir_topico(self.tv_topicos.focus()))
        self.tv_topicos.bind("<Return>", lambda e: self.abrir_topico(self.tv_topicos.focus()))
        ttk.Label(self.forum_dir, text="Clique duas vezes num tópico para abrir.", style="Suave.TLabel").pack(anchor="w", pady=(6, 0))
        self.encher_topicos()

    def encher_topicos(self):
        est = self.n.estado
        tv = self.tv_topicos
        tv.delete(*tv.get_children())
        for t in est.lista_topicos(self.cat.get() or None):
            rs = est.respostas_de(t["id"])
            ult = max([t["criado"]] + [r["criado"] for r in rs])
            titulo = ("📌 " if t["id"] in est.fixados else "") + t["dados"]["titulo"]
            autor = est.nome(t["autor"]) + (" ✦" if est.e_admin(t["autor"]) else "")
            tags = ("fixo",) if t["id"] in est.fixados else ("autor",) if est.e_admin(t["autor"]) else ()
            tv.insert("", "end", iid=t["id"], values=(titulo, autor, len(rs), len(est.curtidas.get(t["id"], ())), quando(ult)), tags=tags)

    def abrir_topico(self, tid):
        if not tid:
            return
        self.topico_aberto = tid
        for w in self.forum_dir.winfo_children():
            w.destroy()
        barra = ttk.Frame(self.forum_dir)
        barra.pack(fill="x", pady=(0, 6))
        ttk.Button(barra, text="← Voltar", command=self.mostrar_lista_topicos).pack(side="left")
        self.barra_topico = ttk.Frame(barra)
        self.barra_topico.pack(side="right")
        self.txt_topico = texto_tk(self.forum_dir, cursor="arrow")
        sb = ttk.Scrollbar(self.forum_dir, command=self.txt_topico.yview)
        self.txt_topico.configure(yscrollcommand=sb.set)
        caixa = ttk.Frame(self.forum_dir)
        caixa.pack(side="bottom", fill="x", pady=(8, 0))
        self.txt_resposta = texto_tk(caixa, height=4)
        self.txt_resposta.pack(side="left", fill="x", expand=True)
        ttk.Button(caixa, text="Responder", style="Ouro.TButton", command=self.responder).pack(side="right", padx=(8, 0), fill="y")
        sb.pack(side="right", fill="y")
        self.txt_topico.pack(fill="both", expand=True)
        t = self.txt_topico
        t.tag_configure("titulo", font=(FAM, 17, "bold"), foreground=C["ouro"], spacing3=4)
        t.tag_configure("nome", font=(FAM, 11, "bold"), foreground=C["texto"])
        t.tag_configure("admin", font=(FAM, 11, "bold"), foreground=C["ouro"])
        t.tag_configure("selo", background=C["ouro"], foreground=C["fundo"], font=(FAM, 8, "bold"))
        t.tag_configure("meta", foreground=C["suave"], font=(FAM, 9))
        t.tag_configure("corpo", font=(FAM, 11), spacing1=2, spacing3=2, lmargin1=4, lmargin2=4)
        t.tag_configure("resp", lmargin1=28, lmargin2=28)
        t.tag_configure("link", foreground=C["ouro_claro"], underline=True)
        t.tag_configure("perigo", foreground=C["perigo"], underline=True)
        t.tag_configure("sep", foreground=C["linha"])
        self.encher_topico()

    def _link(self, texto, cmd, tag="link"):
        t = self.txt_topico
        nome = "l%d" % id(cmd)
        t.tag_bind(nome, "<Button-1>", lambda e: cmd())
        t.tag_bind(nome, "<Enter>", lambda e: t.config(cursor="hand2"))
        t.tag_bind(nome, "<Leave>", lambda e: t.config(cursor="arrow"))
        t.insert("end", texto, (tag, nome))

    def encher_topico(self):
        est, tid = self.n.estado, self.topico_aberto
        top = est.topicos.get(tid)
        t = self.txt_topico
        y = t.yview()[0]
        t.configure(state="normal")
        t.delete("1.0", "end")
        for w in self.barra_topico.winfo_children():
            w.destroy()
        if not top or not est.visivel(top):
            t.insert("end", "Este tópico foi apagado.", ("meta",))
            t.configure(state="disabled")
            return
        if self.n.e_admin():
            fixo = tid in est.fixados
            ttk.Button(self.barra_topico, text="Desafixar" if fixo else "📌 Fixar",
                       command=lambda: self.acao(lambda: self.n.admin("fixar", topico=tid, fixo=not fixo))).pack(side="left", padx=2)
        t.insert("end", top["dados"]["titulo"] + "\n", ("titulo",))
        t.insert("end", top["dados"]["categoria"] + "\n\n", ("meta",))
        for i, ev in enumerate([top] + est.respostas_de(tid)):
            extra = ("resp",) if i else ()
            adm = est.e_admin(ev["autor"])
            t.insert("end", est.nome(ev["autor"]), ("admin" if adm else "nome",) + extra)
            if adm:
                t.insert("end", " ✦ AUTOR ", ("selo",))
            t.insert("end", f"  {est.usuario(ev['autor'])} · {quando(ev['criado'])}\n", ("meta",) + extra)
            t.insert("end", ev["dados"]["texto"].strip() + "\n", ("corpo",) + extra)
            t.insert("end", "", extra)
            curt = est.curtidas.get(ev["id"], set())
            if i:
                t.insert("end", "    ", extra)
            self._link(f"♥ {len(curt)}" + (" (curtido)" if self.n.pub in curt else " Curtir"),
                       lambda e=ev: self.acao(lambda: self.n.curtir(e["id"])))
            if self.n.pub and (ev["autor"] == self.n.pub or self.n.e_admin()):
                t.insert("end", "    ")
                self._link("Apagar", lambda e=ev: self.apagar(e), "perigo")
            if self.n.e_admin() and not adm:
                t.insert("end", "    ")
                self._link("Remover membro", lambda e=ev: self.banir(e["autor"]), "perigo")
            t.insert("end", "\n" + ("─" * 70 if not i else "") + "\n", ("sep",))
        t.configure(state="disabled")
        t.yview_moveto(y)

    def acao(self, f):
        try:
            f()
        except Erro as e:
            self.erro(e)
        self.atualizar(forcar=True)

    def responder(self):
        texto = self.txt_resposta.get("1.0", "end").strip()
        if not texto:
            return
        try:
            self.n.responder(self.topico_aberto, texto)
        except Erro as e:
            return self.erro(e)
        self.txt_resposta.delete("1.0", "end")
        self.atualizar(forcar=True)
        self.txt_topico.yview_moveto(1.0)

    def apagar(self, ev):
        if messagebox.askyesno(NOME, "Apagar este post? Ele some para todos.", parent=self.raiz):
            self.acao(lambda: self.n.apagar(ev["id"]))
            if ev["tipo"] == "topico":
                self.mostrar_lista_topicos()

    def janela(self, titulo, largura=560):
        j = tk.Toplevel(self.raiz, bg=C["fundo"])
        j.title(titulo)
        j.transient(self.raiz)
        j.geometry(f"{largura}x10")
        f = ttk.Frame(j, padding=18)
        f.pack(fill="both", expand=True)
        j.after(10, lambda: j.geometry(""))
        return j, f

    def novo_topico(self):
        if not self.n.pub:
            return self.erro("Entre na sua conta para escrever.")
        j, f = self.janela("Novo tópico", 640)
        ttk.Label(f, text="Novo tópico", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(f, text="Título").pack(anchor="w", pady=(10, 0))
        tit = ttk.Entry(f)
        tit.pack(fill="x")
        ttk.Label(f, text="Categoria").pack(anchor="w", pady=(10, 0))
        cats = [c for c in self.n.estado.regras["categorias"] if c != "Avisos do autor" or self.n.e_admin()]
        cat = ttk.Combobox(f, values=cats, state="readonly")
        cat.set(self.cat.get() if self.cat.get() in cats else (cats[0] if cats else ""))
        cat.pack(fill="x")
        ttk.Label(f, text="Texto").pack(anchor="w", pady=(10, 0))
        txt = texto_tk(f, height=12)
        txt.pack(fill="both", expand=True)

        def publicar():
            try:
                ev = self.n.novo_topico(tit.get(), txt.get("1.0", "end"), cat.get())
            except Erro as e:
                return self.erro(e)
            j.destroy()
            self.atualizar(forcar=True)
            if ev:
                self.abrir_topico(ev["id"])
        ttk.Button(f, text="Publicar", style="Ouro.TButton", command=publicar).pack(anchor="e", pady=(10, 0))
        tit.focus_set()

    # ---------------- QARCHIS (downloads do servidor) ----------------
    def aba_qarchis(self):
        aba = ttk.Frame(self.abas)
        self.abas.add(aba, text="  Qarchis  ")
        barra = ttk.Frame(aba, padding=(8, 6))
        barra.pack(fill="x")
        ttk.Button(barra, text="⇩ Baixar", style="Ouro.TButton", command=self.baixar).pack(side="left", padx=2)
        ttk.Button(barra, text="✿ Enviar qarchi", command=self.enviar).pack(side="left", padx=2)
        ttk.Button(barra, text="✕ Excluir", style="Perigo.TButton", command=self.excluir).pack(side="left", padx=2)
        ttk.Button(barra, text="📂 Pasta de downloads", command=self.abrir_downloads).pack(side="left", padx=2)
        pan = ttk.PanedWindow(aba, orient="horizontal")
        pan.pack(fill="both", expand=True)
        lat = self.lateral(pan)
        pan.add(lat, weight=0)
        ttk.Label(lat, text="MOSTRAR", style="Secao.TLabel").pack(anchor="w", pady=(0, 6))
        self.q_filtro = tk.StringVar(value="todos")
        filtros = [("todos", "Todos"), ("disponiveis", "Disponíveis")]
        if self.n.e_admin():
            filtros.append(("aguardando", "Aguardando aprovação"))
        for v, t in filtros:
            ttk.Radiobutton(lat, text=t, value=v, variable=self.q_filtro,
                            command=lambda: self.atualizar(forcar=True)).pack(anchor="w", pady=1)
        dir_ = ttk.PanedWindow(pan, orient="vertical")
        pan.add(dir_, weight=1)
        topo = ttk.Frame(dir_, padding=(8, 6))
        dir_.add(topo, weight=3)
        cols = ("nome", "arqs", "situacao", "por")
        self.tv_q = ttk.Treeview(topo, columns=cols, show="headings")
        for c, t, w in (("nome", "Nome", 320), ("arqs", "Arquivos", 90), ("situacao", "Situação", 200), ("por", "Enviado por", 160)):
            self.tv_q.heading(c, text=t)
            self.tv_q.column(c, width=w, anchor="w" if c in ("nome", "situacao", "por") else "center")
        self.tv_q.tag_configure("pendente", foreground=C["suave"])
        self.tv_q.pack(fill="both", expand=True)
        self.tv_q.bind("<Double-1>", lambda e: self.baixar())
        self.tv_q.bind("<<TreeviewSelect>>", lambda e: self.encher_detalhe_qarchi())
        det = ttk.Notebook(dir_)
        dir_.add(det, weight=2)
        self.q_geral = texto_tk(det, height=7, state="disabled")
        self.q_arquivos = ttk.Treeview(det, columns=("arq",), show="headings")
        self.q_arquivos.heading("arq", text="Arquivo")
        self.q_arquivos.column("arq", width=500, anchor="w")
        det.add(self.q_geral, text="Geral")
        det.add(self.q_arquivos, text="Arquivos")

    def qarchi_sel(self):
        return self.tv_q.focus() if hasattr(self, "tv_q") else None

    def _linhas_qarchi(self):
        est = self.n.estado
        f = self.q_filtro.get()
        linhas = []
        for qid, d in est.qarchis.items():
            aprovado = d["aprovado"]
            if f == "disponiveis" and not aprovado:
                continue
            if f == "aguardando" and aprovado:
                continue
            if aprovado:
                sit = "Disponível para baixar"
            elif self.n.e_admin() and d["evento"]["autor"] != self.n.pub:
                sit = "Aguardando sua aprovação"
            else:
                sit = "Enviado — aguardando o autor"
            linhas.append((qid, (d["qarchi"]["info"]["nome"], len(d["arquivos"]), sit, est.nome(d["evento"]["autor"])),
                           () if aprovado else ("pendente",)))
        return linhas

    def encher_qarchis(self):
        tv = self.tv_q
        sel = tv.focus()
        tv.delete(*tv.get_children())
        for iid, vals, tags in self._linhas_qarchi():
            tv.insert("", "end", iid=iid, values=vals, tags=tags)
        if sel and tv.exists(sel):
            tv.focus(sel)
            tv.selection_set(sel)
        self.encher_detalhe_qarchi()

    def encher_detalhe_qarchi(self):
        if not hasattr(self, "q_geral") or not self.q_geral.winfo_exists():
            return
        est = self.n.estado
        q = est.qarchis.get(self.qarchi_sel())
        g = self.q_geral
        g.configure(state="normal")
        g.delete("1.0", "end")
        self.q_arquivos.delete(*self.q_arquivos.get_children())
        if q:
            i = q["qarchi"]["info"]
            g.insert("end", f"{i['nome']}\n\n{i.get('descricao', '')}\n\n"
                            f"Arquivos: {len(q['arquivos'])}\nEnviado por: {est.nome(q['evento']['autor'])}\n"
                            + ("Disponível para baixar." if q["aprovado"] else "Ainda não aprovado pelo autor."))
            for nome in q["arquivos"]:
                self.q_arquivos.insert("", "end", values=(nome,))
        else:
            g.insert("end", "Selecione um qarchi para ver os detalhes.\n\nUm qarchi é um conjunto de arquivos que o autor "
                            "disponibiliza (por exemplo, as amostras do livro). Clique em Baixar para trazê-lo do servidor "
                            "para o seu computador.")
        g.configure(state="disabled")

    def baixar(self):
        qid = self.qarchi_sel()
        if not qid or qid not in self.n.estado.qarchis:
            return
        nome = self.n.estado.qarchis[qid]["qarchi"]["info"]["nome"]
        self.registro.put(f"{time.strftime('%H:%M:%S')}  Baixando '{nome}'...")

        def tarefa():
            try:
                destino = self.n.baixar_qarchi(qid)
            except Erro as e:
                self.raiz.after(0, lambda: self.erro(e))
                return
            self.raiz.after(0, lambda: messagebox.showinfo(NOME, f"'{nome}' baixado em:\n{destino}", parent=self.raiz))
        threading.Thread(target=tarefa, daemon=True).start()

    def enviar(self):
        if not self.n.pub:
            return self.erro("Entre na sua conta para enviar um qarchi.")
        arquivos = filedialog.askopenfilenames(title="Escolha os arquivos do qarchi", parent=self.raiz)
        if not arquivos:
            return
        j, f = self.janela("Enviar qarchi")
        ttk.Label(f, text="Enviar um qarchi", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(f, text=f"{len(arquivos)} arquivo(s) · {tamanho(sum(os.path.getsize(a) for a in arquivos))}", style="Suave.TLabel").pack(anchor="w")
        ttk.Label(f, text="Nome").pack(anchor="w", pady=(10, 0))
        nome = ttk.Entry(f)
        nome.insert(0, os.path.splitext(os.path.basename(arquivos[0]))[0])
        nome.pack(fill="x")
        ttk.Label(f, text="Descrição").pack(anchor="w", pady=(10, 0))
        desc = texto_tk(f, height=5)
        desc.pack(fill="x")
        aviso = "" if self.n.e_admin() else "\nComo você não é o autor, o qarchi só fica disponível depois que ele aprovar."
        ttk.Label(f, text="Só envie o que você tem direito de compartilhar." + aviso, style="Suave.TLabel", justify="left").pack(anchor="w", pady=8)

        def ok():
            lista = list(arquivos)
            nm, ds = nome.get(), desc.get("1.0", "end")
            j.destroy()
            self.registro.put(f"{time.strftime('%H:%M:%S')}  Enviando '{nm}'...")

            def tarefa():
                try:
                    self.n.enviar_qarchi(lista, nm, ds)
                except Erro as e:
                    self.raiz.after(0, lambda: self.erro(e))
                    return
                self.raiz.after(0, lambda: (self.atualizar(forcar=True),
                                            messagebox.showinfo(NOME, f"'{nm}' enviado ao servidor.", parent=self.raiz)))
            threading.Thread(target=tarefa, daemon=True).start()
        ttk.Button(f, text="Enviar ao servidor", style="Ouro.TButton", command=ok).pack(anchor="e")

    def excluir(self):
        qid = self.qarchi_sel()
        if not qid or qid not in self.n.estado.qarchis:
            return
        if messagebox.askyesno(NOME, "Excluir este qarchi do servidor? Ele some para todos.", parent=self.raiz):
            self.acao(lambda: self.n.excluir_qarchi(qid))

    def abrir_downloads(self):
        os.makedirs(PASTA_DOWNLOADS, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(PASTA_DOWNLOADS)  # noqa: S606
        else:
            webbrowser.open("file://" + os.path.abspath(PASTA_DOWNLOADS))

    # ---------------- MEMBROS ----------------
    def aba_membros(self):
        aba = ttk.Frame(self.abas, padding=10)
        self.abas.add(aba, text="  Membros  ")
        barra = ttk.Frame(aba)
        barra.pack(fill="x", pady=(0, 6))
        ttk.Label(barra, text="Membros", style="Titulo.TLabel").pack(side="left")
        if self.n.e_admin():
            for txt, cmd, st in (("Aprovar", lambda: self.membro_acao("aprovar"), "TButton"),
                                 ("Reprovar", lambda: self.membro_acao("reprovar"), "TButton"),
                                 ("Remover", lambda: self.banir(self.tv_m.focus()), "Perigo.TButton"),
                                 ("Readmitir", lambda: self.membro_acao("desbanir"), "TButton")):
                ttk.Button(barra, text=txt, style=st, command=cmd).pack(side="right", padx=2)
        cols = ("nome", "usuario", "desde", "posts", "situacao")
        self.tv_m = ttk.Treeview(aba, columns=cols, show="headings")
        for c, t, w in (("nome", "Nome", 220), ("usuario", "Usuário", 160), ("desde", "Desde", 120), ("posts", "Posts", 70), ("situacao", "Situação", 200)):
            self.tv_m.heading(c, text=t)
            self.tv_m.column(c, width=w, anchor="w" if c != "posts" else "center")
        self.tv_m.tag_configure("admin", foreground=C["ouro"])
        self.tv_m.tag_configure("banido", foreground=C["perigo"])
        self.tv_m.pack(fill="both", expand=True)
        self.tv_m.bind("<Double-1>", lambda e: self.ver_perfil(self.tv_m.focus()))

    def encher_membros(self):
        est = self.n.estado
        tv = self.tv_m
        sel = tv.focus()
        tv.delete(*tv.get_children())
        contagem = {}
        for t in est.topicos.values():
            contagem[t["autor"]] = contagem.get(t["autor"], 0) + 1
        for rs in est.respostas.values():
            for r in rs:
                contagem[r["autor"]] = contagem.get(r["autor"], 0) + 1
        for pub, p in sorted(est.perfis.items(), key=lambda kv: (not est.e_admin(kv[0]), kv[1]["desde"])):
            if pub in est.banidos and not self.n.e_admin():
                continue
            if est.e_admin(pub):
                sit, tags = "✦ Autor (admin)", ("admin",)
            elif pub in est.banidos:
                sit, tags = "Removido: " + (est.banidos[pub] or ""), ("banido",)
            elif est.regras.get("so_aprovados") and pub not in est.aprovados:
                sit, tags = "Aguardando aprovação", ()
            else:
                sit, tags = "Membro" + (" aprovado" if pub in est.aprovados else ""), ()
            tv.insert("", "end", iid=pub, values=(p["nome"], "@" + p["usuario"], time.strftime("%d/%m/%Y", time.localtime(p["desde"])),
                                                  contagem.get(pub, 0), sit), tags=tags)
        if sel and tv.exists(sel):
            tv.focus(sel)
            tv.selection_set(sel)

    def membro_acao(self, tipo):
        pub = self.tv_m.focus()
        if pub:
            self.acao(lambda: self.n.admin(tipo, membro=pub))

    def banir(self, pub):
        if not pub or self.n.estado.e_admin(pub):
            return
        motivo = simpledialog.askstring(NOME, f"Remover {self.n.estado.nome(pub)} do fórum?\nTodos os posts dessa pessoa somem.\n\nMotivo:", parent=self.raiz)
        if motivo is not None:
            self.acao(lambda: self.n.admin("banir", membro=pub, motivo=motivo.strip()[:300]))
            if self.topico_aberto:
                self.abrir_topico(self.topico_aberto)

    def ver_perfil(self, pub):
        p = self.n.estado.perfis.get(pub)
        if p:
            messagebox.showinfo("Perfil", f"{p['nome']}  @{p['usuario']}\n\n{p.get('sobre', '')}\n\nMembro desde "
                                          f"{time.strftime('%d/%m/%Y', time.localtime(p['desde']))}", parent=self.raiz)

    # ---------------- REGRAS ----------------
    def aba_regras(self):
        aba = ttk.Frame(self.abas, padding=14)
        self.abas.add(aba, text="  Regras  ")
        ttk.Label(aba, text="Regras do fórum", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(aba, text="Definidas pelo autor. Valem para todos.", style="Suave.TLabel").pack(anchor="w", pady=(0, 8))
        self.txt_regras = texto_tk(aba, height=14)
        self.txt_regras.pack(fill="both", expand=True)
        self.txt_regras.insert("1.0", self.n.estado.regras["texto"])
        if not self.n.e_admin():
            self.txt_regras.configure(state="disabled")
            return
        opc = ttk.Frame(aba)
        opc.pack(fill="x", pady=8)
        self.so_aprov = tk.BooleanVar(value=self.n.estado.regras.get("so_aprovados", False))
        self.q_membros = tk.BooleanVar(value=self.n.estado.regras.get("qarchis_de_membros", True))
        ttk.Checkbutton(opc, text="Só membros aprovados por mim podem postar", variable=self.so_aprov, style="Fundo.TCheckbutton").pack(anchor="w")
        ttk.Checkbutton(opc, text="Membros podem enviar qarchis (com minha aprovação)", variable=self.q_membros, style="Fundo.TCheckbutton").pack(anchor="w")
        ttk.Label(opc, text="Categorias (separadas por vírgula)").pack(anchor="w", pady=(8, 0))
        self.ent_cats = ttk.Entry(opc)
        self.ent_cats.insert(0, ", ".join(self.n.estado.regras["categorias"]))
        self.ent_cats.pack(fill="x")

        def publicar():
            cats = [c.strip() for c in self.ent_cats.get().split(",") if c.strip()][:20]
            self.acao(lambda: self.n.admin("regras", texto=self.txt_regras.get("1.0", "end").strip(), so_aprovados=self.so_aprov.get(),
                                           qarchis_de_membros=self.q_membros.get(), categorias=cats or ["Conversa livre"]))
            messagebox.showinfo(NOME, "Regras publicadas para todos.", parent=self.raiz)
        ttk.Button(aba, text="Publicar regras", style="Ouro.TButton", command=publicar).pack(anchor="e")

    # ---------------- PERFIL ----------------
    def aba_perfil(self):
        aba = ttk.Frame(self.abas, padding=18)
        self.abas.add(aba, text="  Meu perfil  ")
        est = self.n.estado
        if self.n.pub:
            p = est.perfis.get(self.n.pub, {})
            ttk.Label(aba, text=f"{p.get('nome', '')}  @{p.get('usuario', '')}", style="Titulo.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
            ttk.Label(aba, text="Nome").grid(row=1, column=0, sticky="w", pady=4)
            nome = ttk.Entry(aba, width=40)
            nome.insert(0, p.get("nome", ""))
            nome.grid(row=1, column=1, sticky="w")
            ttk.Label(aba, text="Sobre você").grid(row=2, column=0, sticky="nw", pady=4)
            sobre = texto_tk(aba, width=50, height=4)
            sobre.insert("1.0", p.get("sobre", ""))
            sobre.grid(row=2, column=1, sticky="w")
            ttk.Button(aba, text="Salvar perfil", style="Ouro.TButton",
                       command=lambda: self.acao(lambda: self.n.editar_perfil(nome.get(), sobre.get("1.0", "end")))).grid(row=3, column=1, sticky="w", pady=6)
            ttk.Button(aba, text="Trocar minha senha", command=self.trocar_senha).grid(row=4, column=1, sticky="w")
            ttk.Button(aba, text="Sair da conta", command=lambda: (self.n.sair(), self.tela_entrada())).grid(row=5, column=1, sticky="w", pady=6)
        else:
            ttk.Button(aba, text="Entrar ou criar conta", style="Ouro.TButton", command=self.tela_entrada).grid(row=0, column=0, sticky="w")
        ttk.Separator(aba).grid(row=6, column=0, columnspan=2, sticky="we", pady=16)
        ttk.Label(aba, text="Servidor", style="Titulo.TLabel").grid(row=7, column=0, columnspan=2, sticky="w")
        estado_txt = "● conectado" if self.n.online else "○ sem conexão agora"
        ttk.Label(aba, text=f"A Semente fala com o servidor do autor:\n{self.n.servidor}   ({estado_txt})",
                  style="Suave.TLabel", justify="left").grid(row=8, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Label(aba, text=f"Seus downloads ficam em {PASTA_DOWNLOADS}", style="Suave.TLabel").grid(row=9, column=0, columnspan=2, sticky="w", pady=8)

    def trocar_senha(self):
        if not self.n.pub:
            return
        atual = simpledialog.askstring(NOME, "Sua senha atual:", show="•", parent=self.raiz)
        if not atual:
            return
        nova = simpledialog.askstring(NOME, "Nova senha (mínimo 10 caracteres):", show="•", parent=self.raiz)
        if not nova:
            return
        nova2 = simpledialog.askstring(NOME, "Repita a nova senha:", show="•", parent=self.raiz)
        if nova != nova2:
            return self.erro("As senhas não são iguais.")
        try:
            self.n.trocar_senha(atual, nova)
        except Erro as e:
            return self.erro(e)
        messagebox.showinfo(NOME, "Senha trocada. Use a nova a partir de agora.", parent=self.raiz)

    # ---------------- ADMIN ----------------
    def aba_admin(self):
        aba = ttk.Frame(self.abas, padding=14)
        self.abas.add(aba, text="  ✦ Admin  ")
        ttk.Label(aba, text="Painel do autor", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(aba, text="O servidor garante que só você faz o que está aqui: aprovar, apagar, banir e mudar as regras.",
                  style="Suave.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Label(aba, text="Qarchis aguardando aprovação").pack(anchor="w")
        self.tv_pend = ttk.Treeview(aba, columns=("nome", "por", "arqs"), show="headings", height=6)
        for c, t in (("nome", "Nome"), ("por", "Enviado por"), ("arqs", "Arquivos")):
            self.tv_pend.heading(c, text=t)
        self.tv_pend.pack(fill="x")
        b = ttk.Frame(aba)
        b.pack(fill="x", pady=4)
        ttk.Button(b, text="Baixar para conferir", command=lambda: self._pend(self._baixar_pendente)).pack(side="left")
        ttk.Button(b, text="Aprovar", style="Ouro.TButton", command=lambda: self._pend(lambda q: self.n.admin("aprovar_qarchi", qid=q))).pack(side="left", padx=4)
        ttk.Button(b, text="Recusar e apagar", style="Perigo.TButton",
                   command=lambda: self._pend(lambda q: self.n.excluir_qarchi(q))).pack(side="left")
        ttk.Label(aba, text="\nAviso no topo do fórum").pack(anchor="w")
        aviso = ttk.Entry(aba)
        aviso.insert(0, self.n.estado.aviso)
        aviso.pack(fill="x")
        ttk.Button(aba, text="Publicar aviso", command=lambda: self.acao(lambda: self.n.admin("aviso", texto=aviso.get().strip()[:300]))).pack(anchor="w", pady=4)

    def _baixar_pendente(self, qid):
        nome = self.n.estado.qarchis.get(qid, {}).get("qarchi", {}).get("info", {}).get("nome", qid)
        self.registro.put(f"{time.strftime('%H:%M:%S')}  Baixando '{nome}' para conferir...")
        threading.Thread(target=lambda: self._tenta(lambda: self.n.baixar_qarchi(qid), nome), daemon=True).start()

    def _tenta(self, funcao, nome):
        try:
            destino = funcao()
        except Erro as e:
            self.raiz.after(0, lambda: self.erro(e))
            return
        self.raiz.after(0, lambda: messagebox.showinfo(NOME, f"'{nome}' baixado em:\n{destino}", parent=self.raiz))

    def _pend(self, f):
        q = self.tv_pend.focus()
        if q:
            self.acao(lambda: f(q))

    def encher_admin(self):
        if not hasattr(self, "tv_pend") or not self.tv_pend.winfo_exists():
            return
        est = self.n.estado
        sel = self.tv_pend.focus()
        self.tv_pend.delete(*self.tv_pend.get_children())
        for qid, d in est.qarchis.items():
            if not d["aprovado"]:
                self.tv_pend.insert("", "end", iid=qid, values=(d["qarchi"]["info"]["nome"], est.nome(d["evento"]["autor"]), len(d["arquivos"])))
        if sel and self.tv_pend.exists(sel):
            self.tv_pend.focus(sel)
            self.tv_pend.selection_set(sel)

    # ---------------- SOBRE ----------------
    def aba_sobre(self):
        aba = ttk.Frame(self.abas, padding=14)
        self.abas.add(aba, text="  Sobre  ")
        t = texto_tk(aba)
        t.pack(fill="both", expand=True)
        t.tag_configure("t", font=(FAM, 15, "bold"), foreground=C["ouro"])
        t.tag_configure("m", foreground=C["suave"])
        t.insert("end", "Semente\n", ("t",))
        t.insert("end", "O fórum dos leitores de Wallace Ross, de Ailig Qarchi.\n\n")
        t.insert("end", "Como funciona\n", ("t",))
        t.insert("end", "• A Semente é um aplicativo comum que se conecta ao servidor que o autor mantém ligado. "
                        "Tudo — contas, posts e qarchis — fica nesse servidor.\n"
                        "• Quando o servidor do autor está no ar, a Semente acorda; quando não está, ela avisa e você tenta mais tarde.\n"
                        "• O autor é o admin: só ele aprova e remove membros, apaga posts, muda as regras e aprova os qarchis. "
                        "O próprio servidor garante isso.\n"
                        "• Qarchis são conjuntos de arquivos que o autor disponibiliza, como as amostras do livro. "
                        "Você os baixa do servidor para o seu computador.\n\n")
        t.insert("end", f"Site: {SITE}\n" + (f"Livro completo: {AMAZON}\n" if AMAZON else "Livro completo: na Amazon.\n"))
        t.insert("end", f"\nVersão {VERSAO} · servidor {self.n.servidor}\n", ("m",))
        t.configure(state="disabled")

    # ------------------------------------------------------------ ciclo
    def atualizar(self, forcar=False):
        online = self.n.online
        self.lbl_resumo.config(text=("● conectado   " if online else "○ sem conexão com o servidor   "),
                               foreground=C["ok"] if online else C["perigo"])
        self._mostrar_conexao()
        mudou = forcar or self.n.versao != self.versao_vista
        self.versao_vista = self.n.versao
        if not hasattr(self, "abas") or not self.abas.winfo_exists():
            return
        try:
            if mudou:
                if self.topico_aberto:
                    self.encher_topico()
                elif hasattr(self, "tv_topicos") and self.tv_topicos.winfo_exists():
                    self.encher_topicos()
                    self.desenhar_categorias()
                self.encher_membros()
                self.encher_admin()
                self.encher_qarchis()
        except tk.TclError:
            pass

    def _ciclo(self):
        try:
            self.atualizar()
        finally:
            self.raiz.after(1500, self._ciclo)

    def rodar(self):
        # teste de fumaça: monta todas as telas e fecha sozinho (usado no CI)
        if os.environ.get("SEMENTE_AUTOTESTE"):
            self.raiz.after(300, self._autoteste)
        self.raiz.mainloop()

    def _autoteste(self):
        try:
            self.tela_principal()
        finally:
            self.raiz.after(400, self.raiz.destroy)
