<#
.SYNOPSIS
    Create Windows directory junctions for Cursor skills pointing to D:\baseSoftware repos.
.DESCRIPTION
    WSL's ln -s creates symlinks with Linux-path targets (/mnt/d/...) that Windows apps
    like Cursor CANNOT resolve. This script replaces them with native Windows directory
    junctions (mklink /J) that work correctly.
.PARAMETER Action
    "create" (default) — create junctions. "remove" — only remove existing broken links.
.PARAMETER SourceBase
    Base directory containing plugin skills (default: D:\baseSoftware)
.PARAMETER PluginName
    Plugin subdirectory name under which skills/ lives (e.g. "understand-anything-plugin")
.PARAMETER SkillNames
    Comma-separated list of skill directory names.
.PARAMETER Force
    Remove existing symlinks/dirs before creating junctions.
.EXAMPLE
    # Understand-Anything
    .\create-cursor-skills-junctions.ps1 -PluginName "Understand-Anything/understand-anything-plugin" `
        -SkillNames "understand","understand-chat","understand-dashboard","understand-diff","understand-domain","understand-explain","understand-knowledge","understand-onboard"
#>

param(
    [ValidateSet("create","remove")]
    [string]$Action = "create",
    [string]$SourceBase = "D:\baseSoftware",
    [string]$PluginName = "",
    [string[]]$SkillNames = @(),
    [switch]$Force
)

$cursorSkills = "$env:USERPROFILE\.cursor\skills"

if (-not $PluginName) {
    Write-Host "Error: -PluginName is required (e.g. 'Understand-Anything/understand-anything-plugin')" -ForegroundColor Red
    exit 1
}

if ($SkillNames.Count -eq 0) {
    Write-Host "Error: -SkillNames is required" -ForegroundColor Red
    exit 1
}

if ($Action -eq "remove") {
    Write-Host "Removing existing links..." -ForegroundColor Yellow
    foreach ($skill in $SkillNames) {
        $link = "$cursorSkills\$skill"
        if (Test-Path $link) {
            Remove-Item $link -Force -Recurse
            Write-Host "  Removed: $skill" -ForegroundColor Yellow
        }
    }
    exit 0
}

# Create phase
$hadErrors = $false
foreach ($skill in $SkillNames) {
    $target = "$SourceBase\$PluginName\skills\$skill"
    $link = "$cursorSkills\$skill"

    if (-not (Test-Path $target)) {
        Write-Host "  ✗ Source not found: $target" -ForegroundColor Red
        $hadErrors = $true
        continue
    }

    if (Test-Path $link) {
        if ($Force) {
            Remove-Item $link -Force -Recurse
        } else {
            Write-Host "  - Already exists: $skill (use -Force to replace)" -ForegroundColor DarkYellow
            continue
        }
    }

    try {
        $null = New-Item -ItemType Junction -Path $link -Target $target -Force
        Write-Host "  ✓ $skill" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to create junction for $skill : $_" -ForegroundColor Red
        $hadErrors = $true
    }
}

if (-not $hadErrors) {
    Write-Host "`nAll skills linked. Restart Cursor to pick up changes." -ForegroundColor Cyan
} else {
    Write-Host "`nSome operations failed. Check errors above." -ForegroundColor Red
}
