param(
  [Parameter(Position=0)] [string]$Command = "help",
  [Parameter(ValueFromRemainingArguments=$true)] [string[]]$Rest
)
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Scripts = Join-Path $Root "shared/scripts"
$StateCommands = @("init","sync-clips","begin-transcription","await-transcript","approve-transcript","record-guide","require-story-cut","approve-story-cut","await-preview","approve-preview","mark-final","advance-clip","approve-merge","mark-merged","status")
if ($StateCommands -contains $Command) { & python (Join-Path $Scripts "state.py") $Command @Rest; exit $LASTEXITCODE }
switch ($Command) {
  "scan-clips" { & python (Join-Path $Scripts "scan_clips.py") @Rest }
  "scan-instructions" { & python (Join-Path $Scripts "scan_instructions.py") @Rest }
  "guard" { & python (Join-Path $Scripts "guard.py") @Rest }
  "recipe" { & python (Join-Path $Scripts "recipe.py") @Rest }
  "transcribe" { & python (Join-Path $Scripts "transcribe.py") @Rest }
  "captions" { & python (Join-Path $Scripts "captions.py") @Rest }
  "verify" { & python (Join-Path $Scripts "verify_media.py") @Rest }
  "doctor" { & python (Join-Path $Scripts "doctor.py") @Rest }
  "validate-config" { & python (Join-Path $Scripts "validate_config.py") @Rest }
  "release-audit" { & python (Join-Path $Scripts "release_audit.py") @Rest }
  "version" { Get-Content (Join-Path $Root "VERSION") }
  default {
    Write-Host "m-edit command line"
    Write-Host "Use: m-edit.ps1 doctor --project DIR, status --project DIR, or help"
  }
}
exit $LASTEXITCODE
