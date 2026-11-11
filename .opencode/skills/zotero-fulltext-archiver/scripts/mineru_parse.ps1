<#
.SYNOPSIS
  Parse one PDF with MinerU 4.1.5, with a GPU-free guard and an optional 3.4.0 fallback.

.DESCRIPTION
  Default engine: MinerU 4.1.5 (`mineru-kit parse --tier standard --format zip`).
  The output is a zip containing markdown.md, middle_json.json, structured_content.json and images/.
  If free VRAM is below -MinFreeGB, the script exits with code 75 without touching the GPU.

  -Fallback340 runs the old 3.4.0 `hybrid-engine --effort high` only when 4.1.5 fails.
  Its output uses the old `hybrid_auto/` directory layout and is written to a sibling `<Out>_340` directory.

.EXAMPLE
  .\mineru_parse.ps1 -Pdf .\paper.pdf -Out .\out\paper

.EXAMPLE
  .\mineru_parse.ps1 -Pdf .\paper.pdf -Out .\out\paper -Fallback340 -MinFreeGB 12
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Pdf,
    [Parameter(Mandatory = $true)][string]$Out,
    [ValidateSet("basic", "standard", "advanced")]
    [string]$Tier = "standard",
    [int]$MinFreeGB = 12,
    [switch]$Fallback340,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$Mineru415Home = if ($env:MINERU415_HOME) { $env:MINERU415_HOME } else { "E:\program\MinerU\MinerU-4.1.5\home" }
$Mineru415Kit  = if ($env:MINERU415_KIT)  { $env:MINERU415_KIT }  else { "E:\program\MinerU\MinerU-4.1.5\venv\Scripts\mineru-kit.exe" }
$Mineru340Root = if ($env:MINERU340_ROOT) { $env:MINERU340_ROOT } else { "E:\program\MinerU\MinerU\MinerU" }

if (-not (Test-Path -LiteralPath $Pdf)) { throw "PDF not found: $Pdf" }
if (-not $DryRun -and -not (Test-Path -LiteralPath $Mineru415Kit)) { throw "MinerU 4.1.5 kit not found: $Mineru415Kit" }

$parseArgs = @("parse", $Pdf, "-o", $Out, "--tier", $Tier, "--format", "zip")
if ($DryRun) {
    Write-Output ("mineru-kit " + ($parseArgs -join " "))
    if ($Fallback340) { Write-Output "fallback: MinerU 3.4.0 hybrid-engine --effort high -> ${Out}_340" }
    exit 0
}

if (-not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) {
    throw "nvidia-smi not found; MinerU 4.1.5 lmdeploy requires an NVIDIA GPU."
}
$freeMB = [int](& nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits)
if ($freeMB -lt ($MinFreeGB * 1024)) {
    Write-Warning "GPU free VRAM ${freeMB} MB is below the ${MinFreeGB} GB guard; refusing to start."
    exit 75
}

$env:MINERU_HOME = $Mineru415Home
$env:MINERU_MODEL_SOURCE = "local"
$env:HF_HUB_OFFLINE = "1"
$env:PYTHONUTF8 = "1"

Write-Output "MinerU 4.1.5 | tier=$Tier | free=${freeMB}MB | out=$Out"
& $Mineru415Kit @parseArgs
$code = $LASTEXITCODE
if ($code -eq 0) { exit 0 }

Write-Warning "MinerU 4.1.5 failed with exit code $code"
if (-not $Fallback340) { exit $code }

$fallbackOut = "${Out}_340"
Remove-Item Env:MINERU_HOME -ErrorAction SilentlyContinue
$env:PYTHONPATH = "$Mineru340Root\src"
$env:HF_HOME = "$Mineru340Root\models"
$env:HF_HUB_OFFLINE = "1"
$env:MINERU_MODEL_SOURCE = "modelscope"
$env:CUDA_PATH = "$Mineru340Root\cuda"
$env:PYTHONUTF8 = "1"

Write-Output "Fallback: MinerU 3.4.0 hybrid-engine --effort high -> $fallbackOut"
& "$Mineru340Root\WPy64-312101\python\python.exe" -m mineru.cli.client `
    -p $Pdf -o $fallbackOut -b hybrid-engine --effort high
exit $LASTEXITCODE
