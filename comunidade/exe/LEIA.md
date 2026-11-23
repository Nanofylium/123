# Ligar_Comunidade.exe (fonte)

PocketBase 0.22.21 usado como biblioteca + a configuração da Comunidade (snapshot.json, seed.json) + o site
(copiar ../../palacio/index.html para site/index.html antes de compilar) + túnel srv.us pelo ssh do Windows.

Compilar (Go 1.24):
    mkdir site && cp ../../palacio/index.html site/
    GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" -o Ligar_Comunidade.exe .

Sempre que o site mudar, recompile para o .exe levar o index.html novo.
Teste fora do Windows: COMUNIDADE_SENHA=... go run .  (pula a pergunta da senha)
