// Ligar_Comunidade.exe — a Comunidade de Wallace Ross num arquivo só (Windows).
//
// Dentro deste .exe estão: o servidor PocketBase 0.22.21 (github.com/pocketbase/pocketbase, MIT,
// usado como biblioteca), a configuração da Comunidade (canais, regras, conta do autor) e o site-palácio.
// Para a internet chegar até aqui ele usa o srv.us (github.com/pcarrier/srv.us) pelo ssh que já vem no
// Windows: nenhum outro programa é baixado. Dados em %USERPROFILE%\Comunidade_Wallace_Ross.
package main

import (
	"bufio"
	"crypto/rand"
	"embed"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"sync"
	"time"

	"github.com/pocketbase/dbx"
	"github.com/pocketbase/pocketbase"
	"github.com/pocketbase/pocketbase/apis"
	"github.com/pocketbase/pocketbase/core"
	"github.com/pocketbase/pocketbase/daos"
	m "github.com/pocketbase/pocketbase/migrations"
	"github.com/pocketbase/pocketbase/models"
	"golang.org/x/term"
)

//go:embed snapshot.json seed.json
var dadosFS embed.FS

//go:embed site
var siteFS embed.FS

const porta = "8090"

var (
	casa       string
	senhaAutor string
	ler        = bufio.NewReader(os.Stdin)
)

func diga(cor, t string) { // cores ANSI (o console do Windows 10/11 entende)
	fmt.Printf("\x1b[%sm%s\x1b[0m\n", cor, t)
}
func linha() { diga("33", strings.Repeat("=", 64)) }

func pausa() {
	fmt.Println()
	fmt.Print("Aperte Enter para fechar.")
	ler.ReadString('\n')
}

func senhaNova() string {
	if s := os.Getenv("COMUNIDADE_SENHA"); len(s) >= 8 { // para testes automáticos
		return s
	}
	for {
		fmt.Print("Escolha uma senha (mínimo 8 caracteres): ")
		a, _ := term.ReadPassword(int(os.Stdin.Fd()))
		fmt.Println()
		fmt.Print("Repita a senha: ")
		b, _ := term.ReadPassword(int(os.Stdin.Fd()))
		fmt.Println()
		if len(a) < 8 {
			diga("31", "Precisa de pelo menos 8 caracteres.")
			continue
		}
		if string(a) != string(b) {
			diga("31", "As senhas não são iguais. De novo.")
			continue
		}
		return string(a)
	}
}

func aleatorio() string {
	b := make([]byte, 18)
	rand.Read(b)
	return strings.NewReplacer("+", "x", "/", "y", "=", "").Replace(base64.StdEncoding.EncodeToString(b))
}

// a migração: coleções e regras da Comunidade e do fórum, canais, config e a conta do autor
func init() {
	m.Register(func(db dbx.Builder) error {
		dao := daos.New(db)
		raw, _ := dadosFS.ReadFile("snapshot.json")
		var cols []*models.Collection
		if err := json.Unmarshal(raw, &cols); err != nil {
			return err
		}
		if err := dao.ImportCollections(cols, false, nil); err != nil {
			return err
		}
		var seed struct {
			Canais     [][]any  `json:"canais"`
			Regras     string   `json:"regras"`
			Categorias []string `json:"categorias"`
		}
		raw, _ = dadosFS.ReadFile("seed.json")
		if err := json.Unmarshal(raw, &seed); err != nil {
			return err
		}
		vazio := func(nome string) bool {
			r, _ := dao.FindRecordsByFilter(nome, "id != ''", "", 1, 0)
			return len(r) == 0
		}
		if vazio("canais") {
			col, err := dao.FindCollectionByNameOrId("canais")
			if err != nil {
				return err
			}
			for i, c := range seed.Canais {
				r := models.NewRecord(col)
				r.Set("nome", c[0])
				r.Set("descricao", c[1])
				r.Set("ordem", i)
				r.Set("so_autor", c[2])
				if err := dao.SaveRecord(r); err != nil {
					return err
				}
			}
		}
		if vazio("config") {
			col, err := dao.FindCollectionByNameOrId("config")
			if err != nil {
				return err
			}
			r := models.NewRecord(col)
			r.Set("regras_texto", seed.Regras)
			r.Set("so_aprovados", false)
			r.Set("qarchis_de_membros", true)
			r.Set("categorias", seed.Categorias)
			if err := dao.SaveRecord(r); err != nil {
				return err
			}
		}
		autor, _ := dao.FindAuthRecordByUsername("users", "ailigqarchi")
		if autor == nil && senhaAutor != "" {
			col, err := dao.FindCollectionByNameOrId("users")
			if err != nil {
				return err
			}
			autor = models.NewRecord(col)
			autor.SetUsername("ailigqarchi")
			autor.SetPassword(senhaAutor)
			autor.Set("name", "Ailig Qarchi")
			autor.Set("sobre", "Autor de Wallace Ross.")
		}
		if autor != nil {
			autor.Set("autor", true)
			autor.Set("aprovado", true)
			autor.Set("banido", false)
			return dao.SaveRecord(autor)
		}
		return nil
	}, nil, "1763900000_comunidade.go")
}

func abrir(url string) {
	if runtime.GOOS == "windows" {
		exec.Command("rundll32", "url.dll,FileProtocolHandler", url).Start()
	}
}

func copiar(t string) bool {
	if runtime.GOOS != "windows" {
		return false
	}
	c := exec.Command("clip")
	c.Stdin = strings.NewReader(t)
	return c.Run() == nil
}

var reURL = regexp.MustCompile(`https://[a-z0-9.-]+\.srv\.us`)

// túnel pelo srv.us: o endereço vem da chave (sempre o mesmo); volta sozinho se cair
func tunel() {
	ssh, err1 := exec.LookPath("ssh")
	keygen, err2 := exec.LookPath("ssh-keygen")
	if err1 != nil || err2 != nil {
		linha()
		diga("31", "  Este Windows está sem o cliente SSH, então o túnel não abriu.")
		diga("37", "  Instale em: Configurações > Aplicativos > Recursos opcionais > Adicionar > Cliente OpenSSH.")
		diga("37", "  Neste computador a Comunidade abre em http://127.0.0.1:"+porta)
		linha()
		abrir("http://127.0.0.1:" + porta)
		return
	}
	chave := filepath.Join(casa, "chave_tunel")
	if _, err := os.Stat(chave); err != nil {
		exec.Command(keygen, "-q", "-t", "ed25519", "-N", "", "-C", "comunidade-wallace-ross", "-f", chave).Run()
	}
	login := "nomatch"
	if b, err := os.ReadFile(filepath.Join(casa, "GITHUB.txt")); err == nil && strings.TrimSpace(string(b)) != "" {
		login = strings.ToLower(strings.TrimSpace(string(b)))
	}
	primeira := true
	for {
		cmd := exec.Command(ssh, "-T", "-i", chave, "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=accept-new",
			"-o", "ServerAliveInterval=20", "-o", "ServerAliveCountMax=3", "-o", "ExitOnForwardFailure=yes",
			"-R", "1:localhost:"+porta, login+"@srv.us")
		out, _ := cmd.StdoutPipe()
		cmd.Stderr = cmd.Stdout
		achou := make(chan string, 4)
		if err := cmd.Start(); err != nil {
			diga("31", "Não consegui abrir o túnel: "+err.Error())
			time.Sleep(15 * time.Second)
			continue
		}
		var log strings.Builder
		var once sync.Once
		go func() {
			sc := bufio.NewScanner(io.Reader(out))
			var urls []string
			for sc.Scan() {
				l := sc.Text()
				log.WriteString(l + "\n")
				urls = append(urls, reURL.FindAllString(l, -1)...)
				if len(urls) > 0 {
					u := urls[0]
					for _, x := range urls {
						if strings.HasSuffix(x, ".gh.srv.us") {
							u = x
						}
					}
					once.Do(func() { time.AfterFunc(1500*time.Millisecond, func() { achou <- u }) })
				}
			}
			close(achou)
		}()
		url, ok := <-achou
		if ok && url != "" {
			os.WriteFile(filepath.Join(casa, "ENDERECO.txt"), []byte(url+"\n"), 0o644)
			if primeira {
				primeira = false
				linha()
				diga("32", "  A COMUNIDADE ESTÁ NO AR")
				diga("33", "  Site + Comunidade:  "+url)
				diga("37", "  Entre com o usuário ailigqarchi e a sua senha, e monte seu perfil em MEU PERFIL.")
				diga("37", "  Este endereço é sempre o mesmo (vem da chave guardada na pasta da Comunidade).")
				if !strings.HasSuffix(url, ".gh.srv.us") {
					diga("37", "  Para ele virar https://nanofylium.gh.srv.us, veja o LEIA.txt na pasta da Comunidade.")
				}
				if copiar(url) {
					diga("37", "  (o endereço já está copiado: é só colar e mandar)")
				}
				linha()
				diga("33", "  Deixe esta janela aberta enquanto quiser a Comunidade no ar.")
				diga("37", "  Para desligar, feche a janela.")
				linha()
				abrir(url)
			} else {
				diga("32", "Túnel de volta: "+url)
			}
		}
		cmd.Wait()
		if primeira {
			diga("31", "O túnel não abriu. Detalhes:")
			fmt.Println(strings.TrimSpace(log.String()))
			diga("37", "Tentando de novo em 15 s. Neste computador a Comunidade abre em http://127.0.0.1:"+porta)
			time.Sleep(15 * time.Second)
		} else {
			diga("33", "Túnel caiu; religando...")
			time.Sleep(3 * time.Second)
		}
	}
}

const leia = `COMUNIDADE DE WALLACE ROSS

Tudo o que o Ligar_Comunidade.exe guarda fica nesta pasta:
  pb_data                o banco com perfis e mensagens (faça cópia de vez em quando, com o programa fechado)
  SENHAS-GUARDE-BEM.txt  a senha do painel de administração (http://127.0.0.1:8090/_/ , só neste computador)
  chave_tunel            a chave que mantém o endereço https://….srv.us sempre o mesmo (não apague)
  ENDERECO.txt           o endereço atual da Comunidade

ENDEREÇO COM O SEU NOME DO GITHUB (opcional): https://nanofylium.gh.srv.us
  1) Abra chave_tunel.pub no Bloco de Notas e copie a linha inteira.
  2) No GitHub: Settings > SSH and GPG keys > New SSH key. Título "Comunidade", cole a linha, salve.
  3) Nesta pasta, crie o arquivo GITHUB.txt contendo só: nanofylium
  4) Feche e abra o Ligar_Comunidade.exe de novo.

Sobre o túnel srv.us (github.com/pcarrier/srv.us): é gratuito e feito por uma pessoa. Segundo o projeto, ele não
grava o conteúdo do tráfego, mas guarda por até 1 dia IPs, chaves e volume; uso muito pesado pode pedir contribuição.
`

func main() {
	console()
	home, _ := os.UserHomeDir()
	casa = filepath.Join(home, "Comunidade_Wallace_Ross")
	dados := filepath.Join(casa, "pb_data")
	os.MkdirAll(casa, 0o755)
	os.WriteFile(filepath.Join(casa, "LEIA.txt"), []byte(strings.ReplaceAll(leia, "\n", "\r\n")), 0o644)
	// limpa restos das versões com .bat/bore
	os.Remove(filepath.Join(casa, "bore.exe"))
	os.Remove(filepath.Join(casa, "PORTA-DO-TUNEL.txt"))

	linha()
	diga("33", "  COMUNIDADE DE WALLACE ROSS")
	linha()

	primeiraVez := false
	if _, err := os.Stat(filepath.Join(dados, "data.db")); err != nil {
		primeiraVez = true
	} else {
		// banco de uma versão anterior (.bat): se a conta do autor ainda não existe, a migração cria
	}
	if primeiraVez {
		diga("33", "Primeira vez: vamos criar a sua conta de autor.")
		diga("37", "Usuário: ailigqarchi  (é com ele que você entra na Comunidade)")
		senhaAutor = senhaNova()
	}

	app := pocketbase.NewWithConfig(pocketbase.Config{DefaultDataDir: dados, HideStartBanner: true})
	app.OnBeforeServe().Add(func(e *core.ServeEvent) error {
		if n, _ := app.Dao().TotalAdmins(); n == 0 {
			senha := aleatorio()
			adm := &models.Admin{}
			adm.Email = "autor@ailigqarchi.com.br"
			adm.SetPassword(senha)
			if err := app.Dao().SaveAdmin(adm); err == nil {
				txt := "# Guarde este arquivo. Estas senhas não existem em outro lugar.\r\n" +
					"Painel do PocketBase: http://127.0.0.1:" + porta + "/_/   login: autor@ailigqarchi.com.br\r\n" +
					"PAINEL_SENHA=" + senha + "\r\n" +
					"Conta de autor na Comunidade: usuário ailigqarchi, com a senha que você escolheu.\r\n"
				os.WriteFile(filepath.Join(casa, "SENHAS-GUARDE-BEM.txt"), []byte(txt), 0o600)
				diga("32", "Conta criada. A senha do painel ficou em "+filepath.Join(casa, "SENHAS-GUARDE-BEM.txt"))
			}
		}
		site, _ := fs.Sub(siteFS, "site")
		e.Router.GET("/*", apis.StaticDirectoryHandler(site, false))
		go func() {
			for i := 0; i < 60; i++ {
				time.Sleep(500 * time.Millisecond)
				if r, err := http.Get("http://127.0.0.1:" + porta + "/api/health"); err == nil {
					r.Body.Close()
					if r.StatusCode == 200 {
						break
					}
				}
			}
			diga("37", "Servidor ligado. Abrindo o túnel para a internet...")
			tunel()
		}()
		return nil
	})
	os.Args = []string{os.Args[0], "serve", "--http=127.0.0.1:" + porta}
	if err := app.Start(); err != nil {
		diga("31", "O servidor não ligou: "+err.Error())
		diga("37", "Talvez outro programa (ou outra janela da Comunidade) esteja usando a porta "+porta+".")
		pausa()
		os.Exit(1)
	}
}
