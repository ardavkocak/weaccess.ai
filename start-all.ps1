# Tüm weaccess.ai alt-projelerini Docker Compose ile tek seferde başlatır.
#
# Kullanım:
#   ./start-all.ps1            -> tümünü derle + başlat (arka planda)
#   ./start-all.ps1 -Down      -> tümünü durdur
#   ./start-all.ps1 -Logs      -> tümünün loglarını izle (Ctrl+C ile çık)
#
# Not: ofis-gorev-takibi önce başlatılır çünkü office-portal onun ürettiği
# SQLite dosyasını (ofis-gorev-takibi/ofis-data/ofis.sqlite) bind-mount ile okur.

param(
    [switch]$Down,
    [switch]$Logs
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$projects = @(
    "ofis-gorev-takibi",
    "office-portal",
    "aylik-takip",
    "dokumantasyon-otomasyon",
    "ik-otomasyon",
    "zimmet-sistemi"
)

$ports = @{
    "aylik-takip"             = "(host ağına açık değil, sadece build)"
    "dokumantasyon-otomasyon" = "http://localhost:5000"
    "ik-otomasyon"            = "http://localhost:3002"
    "ofis-gorev-takibi"       = "http://localhost:8110"
    "office-portal"           = "http://localhost:8000"
    "zimmet-sistemi"          = "http://localhost:8001"
}

if ($Down) {
    foreach ($p in $projects) {
        Write-Host "== $p durduruluyor ==" -ForegroundColor Cyan
        Push-Location (Join-Path $root $p)
        docker compose down
        Pop-Location
    }
    exit 0
}

if ($Logs) {
    foreach ($p in $projects) {
        Write-Host "== $p logları (arka planda ayrı pencerede açın) ==" -ForegroundColor Cyan
    }
    Write-Host "Tek proje logu için: cd <proje>; docker compose logs -f" -ForegroundColor Yellow
    exit 0
}

foreach ($p in $projects) {
    $path = Join-Path $root $p
    if (-not (Test-Path $path)) {
        Write-Warning "$p klasörü bulunamadı, atlanıyor."
        continue
    }
    Write-Host "== $p derleniyor ve başlatılıyor ==" -ForegroundColor Cyan
    Push-Location $path
    docker compose up -d --build
    Pop-Location
}

Write-Host ""
Write-Host "Tüm servisler başlatıldı." -ForegroundColor Green
foreach ($p in $projects) {
    Write-Host ("  {0,-26} {1}" -f $p, $ports[$p])
}
Write-Host ""
Write-Host "Durdurmak için: ./start-all.ps1 -Down" -ForegroundColor Yellow
