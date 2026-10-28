# ============================================================
# TricorderKit — Security Audit automatique au démarrage
# scripts/security_audit_startup.ps1
# Déclencheur : logon Windows (Task Scheduler)
# ============================================================

$ProjectRoot      = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$PluginDir        = "$ProjectRoot\plugins\security-audit-cli"
$LogDir           = "$ProjectRoot\logs\security"
$LogFile          = "$LogDir\audit_$(Get-Date -Format 'yyyy-MM-dd_HH-mm').log"
$SecurityRunner   = "C:\Python314\Scripts\security-runner.exe"

# ── Créer le dossier de logs si absent ──────────────────────
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# ── Attendre que le bureau soit prêt (30s après logon) ──────
Start-Sleep -Seconds 30

# ── Lancer l'audit ──────────────────────────────────────────
Set-Location $PluginDir

$Header = @"
================================================
TricorderKit Security Audit — $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Cible : $ProjectRoot
================================================
"@

$Header | Out-File -FilePath $LogFile -Encoding UTF8

# Capturer stdout + stderr (chemin absolu — PATH non garanti en tâche planifiée)
$Output = & $SecurityRunner full-audit $ProjectRoot --strict 2>&1
$ExitCode = $LASTEXITCODE

$Output | Out-File -FilePath $LogFile -Encoding UTF8 -Append

# ── Purger les logs > 30 jours ───────────────────────────────
Get-ChildItem "$LogDir\audit_*.log" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force

# ── Notification Windows toast ───────────────────────────────
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$notify          = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon     = [System.Drawing.SystemIcons]::Shield
$notify.Visible  = $true

if ($ExitCode -eq 0) {
    $notify.ShowBalloonTip(
        8000,
        "TricorderKit — Audit OK",
        "5/5 checks PASS — Système sécurisé",
        [System.Windows.Forms.ToolTipIcon]::Info
    )
} else {
    $notify.ShowBalloonTip(
        15000,
        "TricorderKit — FINDINGS DÉTECTÉS",
        "Des vulnérabilités ont été trouvées.`nLog : $LogFile",
        [System.Windows.Forms.ToolTipIcon]::Warning
    )
}

Start-Sleep -Seconds 3
$notify.Dispose()

exit $ExitCode
