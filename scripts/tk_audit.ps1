$ProjectRoot    = "%USERPROFILE%\Documents\Claude\Projects\TricorderKit Autonome"
$PluginDir      = "$ProjectRoot\plugins\security-audit-cli"
$LogDir         = "C:\ProgramData\TricorderKit\logs"
$LogFile        = "$LogDir\audit_$(Get-Date -Format 'yyyy-MM-dd_HH-mm').log"
$SecurityRunner = "C:\Python314\Scripts\security-runner.exe"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Start-Sleep -Seconds 30

"================================================" | Out-File -FilePath $LogFile -Encoding UTF8
"TricorderKit Security Audit -- $(Get-Date)" | Out-File -FilePath $LogFile -Encoding UTF8 -Append
"================================================" | Out-File -FilePath $LogFile -Encoding UTF8 -Append

Set-Location $PluginDir
$Output = & $SecurityRunner "full-audit" $ProjectRoot "--strict" 2>&1
$ExitCode = if ($LASTEXITCODE -ne $null) { $LASTEXITCODE } else { 1 }
$Output | Out-File -FilePath $LogFile -Encoding UTF8 -Append

Get-ChildItem "$LogDir\audit_*.log" -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Shield
$notify.Visible = $true
if ($ExitCode -eq 0) {
    $notify.ShowBalloonTip(8000, "TricorderKit Audit OK", "5/5 PASS -- Systeme securise", [System.Windows.Forms.ToolTipIcon]::Info)
} else {
    $notify.ShowBalloonTip(15000, "TricorderKit -- FINDINGS", "Vulnerabilites detectees. Log : $LogFile", [System.Windows.Forms.ToolTipIcon]::Warning)
}
Start-Sleep -Seconds 3
$notify.Dispose()
exit $ExitCode
