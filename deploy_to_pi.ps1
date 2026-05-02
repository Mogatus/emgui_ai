# Deploy Energie-Monitor Web App to Raspberry Pi
# Usage: .\deploy_to_pi.ps1 [-User pi]

param(
    [string]$User = "jojo",
    [string]$PiHost = "192.168.178.100",
    [string]$TargetDir = "/home/jojo/emgui_web"
)

$RemoteDest = "${User}@${PiHost}"

Write-Host "=== Energie-Monitor Web App Deploy ===" -ForegroundColor Cyan
Write-Host "Ziel: ${RemoteDest}:${TargetDir}"
Write-Host ""

# Create target directory on Pi
Write-Host "[1/4] Erstelle Verzeichnis auf Pi..." -ForegroundColor Yellow
ssh $RemoteDest "mkdir -p $TargetDir/src/utils $TargetDir/templates"

# Copy web app files
Write-Host "[2/4] Kopiere Dateien..." -ForegroundColor Yellow
scp web_app.py "${RemoteDest}:${TargetDir}/"
scp .env "${RemoteDest}:${TargetDir}/"
scp templates/index.html "${RemoteDest}:${TargetDir}/templates/"
scp src/__init__.py "${RemoteDest}:${TargetDir}/src/"
scp src/database.py "${RemoteDest}:${TargetDir}/src/"
scp src/models.py "${RemoteDest}:${TargetDir}/src/"
scp src/utils/__init__.py "${RemoteDest}:${TargetDir}/src/utils/"
scp src/utils/config.py "${RemoteDest}:${TargetDir}/src/utils/"

# Copy and set up start scripts
Write-Host "[3/4] Kopiere Start-Skripte..." -ForegroundColor Yellow
scp start_web.sh "${RemoteDest}:/home/${User}/"
scp start_web_daemon.sh "${RemoteDest}:/home/${User}/"
ssh $RemoteDest "chmod +x /home/${User}/start_web.sh /home/${User}/start_web_daemon.sh"

# Set up venv and install deps on Pi
Write-Host "[4/4] Installiere Abhängigkeiten auf Pi..." -ForegroundColor Yellow
ssh $RemoteDest "cd $TargetDir && python3 -m venv venv && venv/bin/pip install --upgrade pip && venv/bin/pip install flask psycopg2-binary python-dotenv"

Write-Host ""
Write-Host "=== Fertig! ===" -ForegroundColor Green
Write-Host "Starte die Web App auf dem Pi mit:"
Write-Host "  ssh ${RemoteDest} '~/start_web.sh'" -ForegroundColor Cyan
Write-Host ""
Write-Host "Oder direkt im Browser oeffnen:"
Write-Host "  http://${PiHost}:5000" -ForegroundColor Cyan
