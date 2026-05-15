# ============================================================
# SCRIPT DE LANZAMIENTO INTELIGENTE
# Detecta Java, activa venv, instala dependencias si es necesario,
# y lanza Uvicorn.
# ============================================================

param(
    [string]$HostAddr = "0.0.0.0",
    [int]$Port = 8000,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"

# Rutas
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvPath = Join-Path $ScriptDir "venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$VenvPip = Join-Path $VenvPath "Scripts\pip.exe"
$VenvUvicorn = Join-Path $VenvPath "Scripts\uvicorn.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SWAL SEMICONDUCTORS - WEB SERVICE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que el venv existe
if (-not (Test-Path $VenvPython)) {
    Write-Error "Entorno virtual no encontrado en $VenvPath. Ejecute primero: python -m venv venv"
    exit 1
}
Write-Host "[OK] Entorno virtual encontrado" -ForegroundColor Green

# 2. Detectar Java (metodo robusto con multiples fallbacks)
$JavaExe = $null
$JavaVersion = $null

# Guardar preferencia de error original
$OldErrorAction = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"

# Metodo 1: Rutas conocidas
$JavaPaths = @(
    "C:\Program Files\Java\jdk-21.0.11\bin\java.exe",
    "C:\Program Files\Java\jdk-26.0.1\bin\java.exe"
)
if ($env:JAVA_HOME) {
    $JavaPaths = @("$env:JAVA_HOME\bin\java.exe") + $JavaPaths
}

foreach ($jp in $JavaPaths) {
    if ([System.IO.File]::Exists($jp)) {
        $JavaExe = $jp
        break
    }
}

# Metodo 2: Buscar en PATH con where.exe
if (-not $JavaExe) {
    $whereJava = & where.exe java 2>$null
    if ($whereJava) {
        $JavaExe = $whereJava | Select-Object -First 1
    }
}

# Metodo 3: Get-Command
if (-not $JavaExe) {
    $cmd = Get-Command "java.exe" -ErrorAction SilentlyContinue
    if ($cmd) {
        $JavaExe = $cmd.Source
    }
}

# Obtener version sin lanzar excepcion
if ($JavaExe) {
    try {
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = $JavaExe
        $pinfo.Arguments = "-version"
        $pinfo.RedirectStandardError = $true
        $pinfo.RedirectStandardOutput = $true
        $pinfo.UseShellExecute = $false
        $pinfo.CreateNoWindow = $true
        $proc = New-Object System.Diagnostics.Process
        $proc.StartInfo = $pinfo
        $proc.Start() | Out-Null
        $verLine = $proc.StandardError.ReadLine()
        $proc.WaitForExit(5000) | Out-Null
        if ($verLine) { $JavaVersion = $verLine }
    } catch {
        $JavaVersion = "Version desconocida"
    }

    $javaBin = Split-Path -Parent $JavaExe
    $javaHome = Split-Path -Parent $javaBin
    $env:JAVA_HOME = $javaHome
    $env:PATH = "$javaBin;" + $env:PATH
    Write-Host "[OK] Java detectado: $JavaVersion" -ForegroundColor Green
    Write-Host "     JAVA_HOME = $javaHome" -ForegroundColor DarkGray
} else {
    Write-Warning "Java NO detectado. El modelo PMML no funcionara."
    Write-Warning "Instale JDK 21 o 26 en C:\Program Files\Java\"
}

# Restaurar preferencia de error
$ErrorActionPreference = $OldErrorAction

# 3. Activar entorno virtual (modificar PATH para esta sesion)
$env:PATH = "$ScriptDir\venv\Scripts;" + $env:PATH
Write-Host "[OK] Entorno virtual activado en sesion" -ForegroundColor Green

# 4. Verificar/instalar dependencias
Write-Host "Verificando dependencias..." -ForegroundColor Yellow
& $VenvPip install -q -r "$ScriptDir\requirements.txt" | Out-Null
Write-Host "[OK] Dependencias verificadas" -ForegroundColor Green

# 5. Lanzar Uvicorn
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INICIANDO SERVIDOR FASTAPI" -ForegroundColor Cyan
Write-Host "  URL: http://${HostAddr}:$Port" -ForegroundColor Cyan
Write-Host "  Docs: http://${HostAddr}:$Port/docs" -ForegroundColor Cyan
Write-Host "  Presione Ctrl+C para detener" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$UvicornArgs = @("app.main:app", "--host", $HostAddr, "--port", $Port)
if ($Reload) {
    $UvicornArgs += "--reload"
}

Set-Location -Path $ScriptDir
& $VenvUvicorn @UvicornArgs