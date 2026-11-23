# Liga a Comunidade de Wallace Ross neste computador (Windows).
# 1) baixa o PocketBase 0.22.21 (github.com/pocketbase/pocketbase) e o bore (github.com/ekzhang/bore), ambos do GitHub;
# 2) na primeira vez, cria o banco, os canais e a sua conta de autor (usuário ailigqarchi);
# 3) liga o servidor e o site, e abre um túnel pelo bore.pub para os leitores chegarem até aqui.
# Tudo fica em %USERPROFILE%\Comunidade_Wallace_Ross. Para desligar, feche esta janela.
$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = "SilentlyContinue"

$Aqui   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Casa   = Join-Path $env:USERPROFILE "Comunidade_Wallace_Ross"
$PB     = Join-Path $Casa "pocketbase.exe"
$CF     = Join-Path $Casa "bore.exe"
$Dados  = Join-Path $Casa "pb_data"
$Mig    = Join-Path $Casa "pb_migrations"
$Pub    = Join-Path $Casa "pb_public"
$Senhas = Join-Path $Casa "SENHAS-GUARDE-BEM.txt"
$PortaF = Join-Path $Casa "PORTA-DO-TUNEL.txt"
$LogCF  = Join-Path $Casa "tunel.log"
$LogPB  = Join-Path $Casa "servidor.log"
$Porta  = 8090

function Linha { Write-Host ("=" * 64) -ForegroundColor DarkYellow }
function Diga($t, $cor = "Gray") { Write-Host $t -ForegroundColor $cor }

Linha; Diga "  COMUNIDADE DE WALLACE ROSS" Yellow; Linha
New-Item -ItemType Directory -Force -Path $Casa | Out-Null

if (-not (Test-Path $PB)) {
  Diga "Baixando o PocketBase (uma vez só)..."
  $zip = Join-Path $Casa "pocketbase.zip"
  Invoke-WebRequest "https://github.com/pocketbase/pocketbase/releases/download/v0.22.21/pocketbase_0.22.21_windows_amd64.zip" -OutFile $zip -UseBasicParsing
  Expand-Archive -Path $zip -DestinationPath $Casa -Force
  Remove-Item $zip
}
if (-not (Test-Path $CF)) {
  Diga "Baixando o túnel bore (uma vez só)..."
  $zip = Join-Path $Casa "bore.zip"
  Invoke-WebRequest "https://github.com/ekzhang/bore/releases/download/v0.6.0/bore-v0.6.0-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
  Expand-Archive -Path $zip -DestinationPath $Casa -Force
  Remove-Item $zip
}

# a configuração da Comunidade e o site vêm desta pasta (atualizam quando você baixar uma versão nova)
New-Item -ItemType Directory -Force -Path $Mig, $Pub | Out-Null
Copy-Item -Path (Join-Path $Aqui "pb_migrations\*") -Destination $Mig -Force
Copy-Item -Path (Join-Path $Aqui "pb_public\*") -Destination $Pub -Force

if (-not (Test-Path (Join-Path $Dados "data.db"))) {
  Linha; Diga "Primeira vez: vamos criar a sua conta de autor." Yellow
  Diga "Usuário: ailigqarchi  (é com ele que você entra na Comunidade)"
  while ($true) {
    $a = Read-Host "Escolha uma senha (mínimo 8 caracteres)" -AsSecureString
    $b = Read-Host "Repita a senha" -AsSecureString
    $sa = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($a))
    $sb = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($b))
    if ($sa.Length -lt 8) { Diga "Precisa de pelo menos 8 caracteres." Red; continue }
    if ($sa -ne $sb) { Diga "As senhas não são iguais. De novo." Red; continue }
    break
  }
  $env:AUTOR_SENHA = $sa
  & $PB migrate up "--dir=$Dados" "--migrationsDir=$Mig" | Out-Null
  Remove-Item Env:AUTOR_SENHA
  # o painel de administração do PocketBase (http://127.0.0.1:8090/_/) ganha uma senha própria, gerada aqui
  $bytes = New-Object byte[] 18; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  $admin = [Convert]::ToBase64String($bytes).Replace("+", "x").Replace("/", "y")
  & $PB admin create "autor@ailigqarchi.com.br" $admin "--dir=$Dados" | Out-Null
  @(
    "# Guarde este arquivo. Estas senhas não existem em outro lugar.",
    "Painel do PocketBase: http://127.0.0.1:$Porta/_/   login: autor@ailigqarchi.com.br",
    "PAINEL_SENHA=$admin",
    "Conta de autor na Comunidade: usuário ailigqarchi, com a senha que você escolheu."
  ) | Set-Content -Path $Senhas -Encoding UTF8
  Diga "Conta criada. A senha do painel ficou guardada em $Senhas" Green
}

# liga o servidor (ele também serve o site, de pb_public)
Diga "Ligando o servidor..."
$procPB = Start-Process -FilePath $PB -ArgumentList @("serve", "--http=127.0.0.1:$Porta", "`"--dir=$Dados`"", "`"--migrationsDir=$Mig`"", "`"--publicDir=$Pub`"") `
      -NoNewWindow -PassThru -RedirectStandardOutput $LogPB -RedirectStandardError "$LogPB.erro"
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Milliseconds 500
  try { if ((Invoke-WebRequest "http://127.0.0.1:$Porta/api/health" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { $ok = $true; break } } catch {}
}
if (-not $ok) { Diga "O servidor não respondeu. Veja $LogPB.erro (talvez outro programa esteja usando a porta $Porta)." Red; exit 1 }

# o túnel: bore.pub, sempre na mesma porta (sorteada na primeira vez e guardada), para o endereço não mudar
function AbrirTunel($remota) {
  Remove-Item -Path @($LogCF, "$LogCF.erro") -ErrorAction SilentlyContinue
  $script:procCF = Start-Process -FilePath $CF -ArgumentList @("local", "$Porta", "--to", "bore.pub", "--port", "$remota") -NoNewWindow -PassThru -RedirectStandardOutput $LogCF -RedirectStandardError "$LogCF.erro"
  for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    if ($script:procCF.HasExited) { return $false }
    if (Select-String -Path @($LogCF, "$LogCF.erro") -Pattern "bore\.pub:\d+|remote_port" -Quiet -ErrorAction SilentlyContinue) { return $true }
  }
  return -not $script:procCF.HasExited
}
Diga "Abrindo o túnel para a internet..."
$procCF = $null; $url = $null
$remota = if (Test-Path $PortaF) { [int](Get-Content $PortaF -Raw).Trim() } else { Get-Random -Minimum 20000 -Maximum 60000 }
$abriu = AbrirTunel $remota
if (-not $abriu) {  # a porta guardada estava ocupada no bore.pub: sorteia outra (o endereço muda desta vez)
  for ($k = 0; $k -lt 4 -and -not $abriu; $k++) { $remota = Get-Random -Minimum 20000 -Maximum 60000; $abriu = AbrirTunel $remota }
  if ($abriu -and (Test-Path $PortaF)) { Diga "A porta de sempre estava ocupada; desta vez o endereço é outro." Red }
}
if ($abriu) { Set-Content -Path $PortaF -Value $remota; $url = "http://bore.pub:$remota" }

Linha
if ($url) {
  Diga "  A COMUNIDADE ESTÁ NO AR" Green
  Diga "  Site + Comunidade:  $url" Yellow
  Diga "  Entre com o usuário ailigqarchi e a sua senha."
  Diga ""
  Diga "  Este endereço fica o mesmo toda vez que você ligar (porta guardada em PORTA-DO-TUNEL.txt)."
  Diga "  Ele é http, sem cadeado: não use nele uma senha que você usa em outros lugares."
  try { Set-Clipboard -Value $url; Diga "  (o endereço já está copiado: é só colar e mandar)" } catch {}
  Start-Process $url
} else {
  Diga "  O servidor está ligado, mas o túnel não abriu." Red
  Diga "  Neste computador, a Comunidade abre em http://127.0.0.1:$Porta"
  Diga "  Veja $LogCF.erro para o motivo (internet, firewall)."
  Start-Process "http://127.0.0.1:$Porta"
}
Linha
Diga "  Deixe esta janela aberta enquanto quiser a Comunidade no ar." Yellow
Diga "  Para desligar, feche a janela."
Linha
try { Wait-Process -Id $procPB.Id } finally {
  foreach ($p in @($procCF, $procPB)) { if ($p -and -not $p.HasExited) { try { Stop-Process -Id $p.Id -Force } catch {} } }
}
