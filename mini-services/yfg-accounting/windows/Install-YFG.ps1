$ErrorActionPreference = 'Stop'
$source = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$root = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Programs\YFG Accounting Desk'
New-Item -ItemType Directory -Path $root -Force | Out-Null
foreach ($item in @('app', 'windows', 'requirements.txt', 'README.md', 'راهنمای-کاربری.md', 'راهنمای-یکپارچه-نصب.md')) {
  Copy-Item -Path (Join-Path $source $item) -Destination $root -Recurse -Force
}
$runner = Join-Path $root 'windows\Run-YFG.bat'
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'YFG Accounting Desk.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $runner
$shortcut.WorkingDirectory = $root
$shortcut.Description = 'راه‌اندازی میزکار حسابداری YFG'
$shortcut.Save()
Write-Host "YFG Accounting Desk installed to: $root"
Write-Host "Desktop shortcut created: $shortcutPath"
Write-Host 'The first launch prepares the Python environment. Your database and uploads remain in LocalAppData\YFG\AccountingDesk.'
