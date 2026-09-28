$ErrorActionPreference = 'Stop'
$Root = (Get-Location).Path
$SkillDir = Join-Path $Root '.opencode/skills'
$CommandDir = Join-Path $Root '.opencode/commands'
$MotionDir = Join-Path $Root '.motion'
$ToolsDir = Join-Path $MotionDir 'tools'
$RefDir = Join-Path $MotionDir 'references'

function Need($n) { if (-not (Get-Command $n -ErrorAction SilentlyContinue)) { throw "Missing required command: $n" } }
Need 'git'; Need 'node'; Need 'npm'
$major = [int](node -p "process.versions.node.split('.')[0]")
if ($major -lt 20) { throw "Node 20+ required; detected $major" }

New-Item -ItemType Directory -Force -Path $SkillDir,$CommandDir,$ToolsDir,$RefDir | Out-Null
function Clone($url,$dest) {
  if (Test-Path (Join-Path $dest '.git')) { git -C $dest fetch --depth 1 origin; git -C $dest reset --hard origin/HEAD }
  else { if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }; git clone --depth 1 $url $dest }
}

# 1) MotionLens / MotionVault — local reference extraction.
$mv = Join-Path $ToolsDir 'MotionVault'
Clone 'https://github.com/xiyu519/MotionVault.git' $mv
Push-Location $mv
try { npm ci; node capture/scripts/build-bookmarklet.mjs; node capture/scripts/build-extension.mjs } finally { Pop-Location }

# 2) Agent knowledge. Copy only selected skills; no runtime animation package is installed.
$src = Join-Path $ToolsDir 'skill-sources'; New-Item -ItemType Directory -Force -Path $src | Out-Null
$emil = Join-Path $src 'emil-skills'; $gsap = Join-Path $src 'gsap-skills'; $mref = Join-Path $src 'motion-ref-skill'
Clone 'https://github.com/emilkowalski/skills.git' $emil
Clone 'https://github.com/greensock/gsap-skills.git' $gsap
Clone 'https://github.com/joepUI/motion-ref-skill.git' $mref

foreach ($n in @('animate','review-animations','improve-animations','find-animation-opportunities','emil-design-eng')) {
  $s = Join-Path $emil "skills/$n"; if (Test-Path "$s/SKILL.md") { Copy-Item -Recurse -Force $s (Join-Path $SkillDir $n) }
}
foreach ($n in @('gsap-core','gsap-timeline','gsap-scrolltrigger','gsap-react')) {
  $s = Join-Path $gsap "skills/$n"; if (Test-Path "$s/SKILL.md") { Copy-Item -Recurse -Force $s (Join-Path $SkillDir $n) }
}
$mrt = Join-Path $SkillDir 'motion-ref-skill'; if (Test-Path $mrt) { Remove-Item -Recurse -Force $mrt }
New-Item -ItemType Directory -Force -Path $mrt | Out-Null
Copy-Item "$mref/SKILL.md" $mrt
foreach ($d in @('references','ref','docs')) { if (Test-Path (Join-Path $mref $d)) { Copy-Item -Recurse -Force (Join-Path $mref $d) $mrt } }

# 3) Local government-specific skill, templates and prompts.
$gov = Join-Path $SkillDir 'gov-motion-reference'; New-Item -ItemType Directory -Force -Path $gov | Out-Null
Copy-Item "$PSScriptRoot/GOV-MOTION-SYSTEM.md" "$gov/SKILL.md" -Force
if (-not (Test-Path (Join-Path $MotionDir 'MOTION.md'))) { Copy-Item "$PSScriptRoot/MOTION.md" (Join-Path $MotionDir 'MOTION.md') }
Copy-Item "$PSScriptRoot/SIH-GOV-MOTION-PROMPTS.md" (Join-Path $Root 'SIH-GOV-MOTION-PROMPTS.md') -Force
Copy-Item "$PSScriptRoot/MOTION.md" (Join-Path $RefDir 'MOTION.md') -Force

@'
---
description: Analyze or implement motion from a LOCAL reference for the government-service UI
agent: build
---
Use the `gov-motion-reference` skill.

Arguments:
$ARGUMENTS

NO web search or URL fetching. A URL alone is not evidence. Require a local MotionLens CaptureReport, screenshots, recording, existing code, or MOTION.md.

Read `.motion/MOTION.md`, local reference evidence, relevant target components, and `package.json`.

Reference analysis: create/update `MOTION_SPEC.md`; classify facts as EXACT / OBSERVED / INFERRED / DEFAULT; do not code until the spec is coherent.

Implementation: change only the requested motion; reuse the current stack/tokens; use CSS/WAAPI before adding libraries; add GSAP only when its capabilities are justified; implement reduced-motion and keyboard/touch-safe behavior; do not refactor unrelated code.

Audit: report BLOCKER / IMPORTANT / MINOR / PASS for motion purpose, timing, easing, origin, interruptibility, performance, reduced motion, hover/touch, accessibility, government context, reference fidelity and scope.

Never claim exact reproduction without local evidence.
'@ | Set-Content -Encoding UTF8 (Join-Path $CommandDir 'gov-motion.md')

# Ignore only local tool checkouts/builds; keep prompts and MOTION.md tracked.
$gi = Join-Path $Root '.gitignore'
$line = ".motion/tools/"
if (-not (Test-Path $gi)) { Set-Content -Encoding UTF8 $gi $line } elseif (-not ((Get-Content $gi -Raw) -match [regex]::Escape($line))) { Add-Content -Encoding UTF8 $gi "`r`n$line" }

Write-Host "Installed. Restart OpenCode."
Write-Host "Command: /gov-motion <local-reference-path> <target>"
Write-Host "MotionLens bookmarklet: $mv/capture/dist/bookmarklet-url.txt"
Write-Host "MotionLens extension:   $mv/capture/dist/extension"
Write-Host "Motion source of truth:  $MotionDir/MOTION.md"
