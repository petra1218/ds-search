# ds-search 安装器（Windows PowerShell）：把 skills/ds-search/ 复制到各 Agent 技能目录。
# 幂等：重复安装覆盖旧版并提示。仅分发 skills/ds-search/ 一个自包含目录。
# 用法: .\install.ps1 -Agent zcode   （可选值 zcode|claude|codex|cursor|codebuddy|workbuddy|reasonx|all）
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("zcode", "claude", "codex", "cursor", "codebuddy", "workbuddy", "reasonx", "all")]
  [string]$Agent
)

$ErrorActionPreference = "Stop"
$Src = Join-Path $PSScriptRoot "skills\ds-search"
$SkillName = "ds-search"

if (-not (Test-Path (Join-Path $Src "SKILL.md"))) {
  Write-Error "错误: 未找到 $Src（请在仓库根目录运行）"
}

function Get-TargetDir([string]$Name) {
  switch ($Name) {
    "zcode"     { Join-Path $HOME ".agents\skills\$SkillName" }
    "claude"    { Join-Path $HOME ".claude\skills\$SkillName" }
    "codex"     { Join-Path $HOME ".codex\skills\$SkillName" }
    "cursor"    { Join-Path $HOME ".claude\skills\$SkillName" }   # Cursor 兼容读取 .claude 技能目录
    "codebuddy" { Join-Path $HOME ".codebuddy\skills\$SkillName" } # 未亲测路径，默认约定
    "workbuddy" { Join-Path $HOME ".workbuddy\skills\$SkillName" } # 未亲测路径，默认约定
    "reasonx"   { Join-Path $HOME ".reasonx\skills\$SkillName" }   # 未亲测路径，默认约定
  }
}

function Install-To([string]$Name, [string]$Dest) {
  if (Test-Path $Dest) {
    Write-Host "[$Name] 检测到旧版本，覆盖安装: $Dest"
    Remove-Item -Recurse -Force $Dest
  } else {
    Write-Host "[$Name] 全新安装: $Dest"
  }
  New-Item -ItemType Directory -Force -Path (Split-Path $Dest) | Out-Null
  Copy-Item -Recurse -Force $Src $Dest
  # runtime.conf 记录本机可执行命令，落位后改写为安装路径（WriteAllText 默认 UTF-8 无 BOM，PS 5.1/7 行为一致）
  [System.IO.File]::WriteAllText((Join-Path $Dest "runtime.conf"), "Runtime: Python`nCommand: python $Dest\scripts\ds_cli.py")
  if (-not (Test-Path (Join-Path $Dest "SKILL.md")) -or
      -not (Test-Path (Join-Path $Dest "scripts\ds_cli.py"))) {
    Write-Error "[$Name] 错误: 安装不完整（缺 SKILL.md 或 scripts/ds_cli.py）"
  }
  Write-Host "[$Name] 完成（SKILL.md + scripts/ + references/ + runtime.conf）"
}

$Targets = if ($Agent -eq "all") {
  @("zcode", "claude", "codex", "cursor", "codebuddy", "workbuddy", "reasonx")
} else {
  @($Agent)
}

foreach ($t in $Targets) {
  Install-To $t (Get-TargetDir $t)
}
