param(
  [string]$OutputDir = "third_party"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$repos = @(
  @{ Name = "wildguard"; Url = "https://github.com/allenai/wildguard.git" },
  @{ Name = "HarmBench"; Url = "https://github.com/centerforaisafety/HarmBench.git" },
  @{ Name = "BingoGuard"; Url = "https://github.com/SalesforceAIResearch/BingoGuard.git" },
  @{ Name = "calibration_guard_model"; Url = "https://github.com/Waffle-Liu/calibration_guard_model.git" },
  @{ Name = "HarmAug"; Url = "https://anonymous.4open.science/r/HarmAug/" },
  @{ Name = "OmniGuard"; Url = "https://github.com/vsahil/OmniGuard.git" },
  @{ Name = "syroup"; Url = "https://github.com/anthonysicilia/syroup.git" }
)

foreach ($repo in $repos) {
  $target = Join-Path $OutputDir $repo.Name
  if (Test-Path $target) {
    Write-Host "Skipping existing $target"
    continue
  }
  Write-Host "Cloning $($repo.Url) -> $target"
  git clone --depth 1 $repo.Url $target
}
