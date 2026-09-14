$ErrorActionPreference = "Stop"

$source = "C:\Users\jusaper\Desktop\CLI-main"
$public = Split-Path -Parent $MyInvocation.MyCommand.Path

$files = @(
    "__init__.py",
    "_compat.py",
    ".gitignore",
    "browser_choice.py",
    "check.bat",
    "cli.py",
    "colors.py",
    "cool.py",
    "help.py",
    "paths.py",
    "README.md",
    "repl.py",
    "THIRD_PARTY_NOTICES.txt",
    "version.py",
    "win_workspace.py",
    "window_registry.py",
    "commands\__init__.py",
    "commands\account.py",
    "commands\urls.py"
)

foreach ($relative in $files) {
    $from = Join-Path $source $relative
    $to = Join-Path $public $relative
    if (-not (Test-Path -LiteralPath $from)) {
        throw "Missing source file: $relative"
    }
    $parent = Split-Path -Parent $to
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Copy-Item -LiteralPath $from -Destination $to -Force
}

@"
# Cool English 課程網址清單範例
# 每行一個網址；請勿提交含個人或私人課程資訊的 urls.txt
"@ | Set-Content -LiteralPath (Join-Path $public "urls.example.txt") -Encoding utf8

Write-Host "Public files synchronized: $public"
Write-Host "Excluded urls.txt, browser.json, windows.json, cookies, account data, and caches."
