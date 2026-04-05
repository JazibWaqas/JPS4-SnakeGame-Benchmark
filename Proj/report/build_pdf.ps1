$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

$candidates = @(
    "pdflatex",
    "${env:ProgramFiles}\MiKTeX\miktex\bin\x64\pdflatex.exe",
    "${env:ProgramFiles(x86)}\MiKTeX\miktex\bin\pdflatex.exe",
    "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"
)

$exe = $null
foreach ($c in $candidates) {
    if ($c -eq "pdflatex") {
        $cmd = Get-Command pdflatex -ErrorAction SilentlyContinue
        if ($cmd) { $exe = $cmd.Source; break }
    } elseif (Test-Path $c) { $exe = $c; break }
}

if (-not $exe) {
    Write-Host "pdflatex not found. Install MiKTeX or TeX Live, or upload this folder to Overleaf and compile progress_report_acl.tex"
    exit 1
}

& $exe -interaction=nonstopmode progress_report_acl.tex
& $exe -interaction=nonstopmode progress_report_acl.tex
Write-Host "Done: $here\progress_report_acl.pdf"
