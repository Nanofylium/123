# Semente

O fórum dos leitores de **Wallace Ross**, de Ailig Qarchi: um `.exe` que é rede social, fórum e cultivador de **qarchis** (o "torrent" próprio da Semente), sem servidor central.

![Fórum](docs/telas/forum.png)

## O que a pessoa encontra ao abrir o Semente.exe

| Aba | O que faz |
|---|---|
| **Entrar / Criar conta** | Cadastro com usuário e senha. A conta é a própria senha: a chave de assinatura é derivada do usuário e da senha (scrypt), então dá para entrar de qualquer computador. Não existe "esqueci a senha". |
| **Fórum** | Categorias, tópicos, respostas, curtidas, tópicos fixados e aviso do autor no topo. Os posts do autor levam o selo ✦ AUTOR. |
| **Qarchis** | Funciona como o qBittorrent: lista com progresso, status, pares e velocidades; plantar `.qarchi`, cultivar novo, pausar, remover, abrir pasta e exportar. As amostras oficiais em 6 idiomas já vêm plantadas. |
| **Membros** | Quem participa do fórum. O autor aprova, reprova, remove e readmite membros por aqui. |
| **Regras** | As regras do fórum. Só o autor edita: texto, categorias, "só aprovados podem postar" e "membros podem cultivar qarchis". |
| **Meu perfil** | Nome, "sobre", sair da conta, compartilhar sim ou não, limite de envio e pontos de encontro. |
| **✦ Admin** | Só para o autor: aprovar ou recusar qarchis, publicar aviso e trocar a senha de admin. |

## Como funciona por dentro

- **Sem servidor central.** Cada Semente é um nó. Todos os nós guardam o fórum num SQLite local e trocam eventos entre si: na rede local, por anúncio UDP; pela internet, pelos pontos de encontro e pela troca de listas de pares.
- **Tudo é assinado.** Perfil, tópico, resposta, curtida, qarchi e cada ação do admin são eventos com assinatura Schnorr (secp256k1, BIP-340), conferida por todos os nós. Ninguém consegue se passar por outra pessoa nem pelo autor.
- **O autor manda.** A chave pública do admin está em `app/semente/config.py`. Regras, remoções, aprovações e apagamentos assinados por ela são obedecidos por todos os nós, e o conteúdo removido é apagado do disco de cada um. A senha de admin pode ser trocada pelo painel: a coroa passa para a chave nova por um evento assinado.
- **Qarchis.** Um `.qarchi` é um JSON que descreve arquivos peça por peça, com SHA-256 de cada peça. O identificador (`qid`) é o hash da descrição, e o qarchi é assinado por quem o cultivou. Pela rede só circulam os qarchis publicados ou aprovados pelo autor. Os qarchis de membros esperam aprovação, e é isso que mantém o fórum legal.
- **Fontes web.** O qarchi oficial também pode ser baixado do site, em `https://ailigqarchi.com.br/amostras/`. Cada peça é conferida do mesmo jeito.

## Para o autor: colocar no ar

1. **Pegue o .exe.** Cada push gera o `Semente.exe` em *Actions → Semente.exe → Artifacts*. Uma tag `v1.0` publica o .exe na página *Releases*.
2. **Entre como admin.** O usuário é `ailigqarchi` e a senha é a senha longa que foi entregue a você. Guarde essa senha num gerenciador de senhas e não a coloque neste repositório.
3. **Ponto de encontro (importante).** Para leitores em casas diferentes se enxergarem, pelo menos um computador precisa ficar ligado e alcançável pela internet. Pode ser o seu PC com a porta TCP 47474 liberada no roteador, ou um servidor barato rodando `Semente.exe --servidor` (ou `python -m semente --servidor` na pasta `app`). Coloque o endereço em `PONTOS_DE_ENCONTRO`, em `app/semente/config.py`, e gere o .exe de novo. Sem isso, o fórum só funciona entre computadores da mesma rede local.
4. **Site.** Suba a pasta `site/` para ailigqarchi.com.br. Ela contém o `index.html` e a pasta `amostras/`.
5. **Livro na Amazon.** Quando sair, preencha `AMAZON` em `config.py`.

Se as amostras mudarem, rode `SEMENTE_SENHA_ADMIN='...' python3 tools/gerar_oficial.py`. Ele regera o qarchi oficial assinado. A senha não é gravada em lugar nenhum.

## Rodar a partir do código

```
cd app
python -m semente                 # janela
python -m semente --servidor      # só o nó, para ponto de encontro
python -m semente arquivo.qarchi  # abre um qarchi
```

Precisa só de Python 3.9+ com Tkinter. Não há dependências externas.

## Limites conhecidos

- Num sistema sem servidor, quem roda uma versão modificada do app pode guardar cópias do que foi apagado. As remoções valem para todos os nós que usam o app oficial.
- Contas novas são fáceis de criar. Contra abuso, o autor pode ligar "só membros aprovados podem postar" nas Regras.
- As traduções das amostras (en, es, zh, hi, ar) foram feitas com ajuda de IA e merecem revisão humana.

## Pastas

- `app/semente/`: o código do app. `cripto.py` faz as assinaturas, `dados.py` cuida dos eventos e do estado do fórum, `qarchi.py` do formato e das peças, `rede.py` dos nós e da sincronização, `nucleo.py` das ações e `janela.py` da interface.
- `site/`: o site de arquivo único e as amostras.
- `traducoes/`: os textos traduzidos e o gerador dos PDF/EPUB.
- `tools/`: o gerador do qarchi oficial.
- `docs/telas/`: capturas de tela.
