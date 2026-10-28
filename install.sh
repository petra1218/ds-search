#!/usr/bin/env bash
# ds-search 安装器：把 skills/ds-search/ 复制到各 Agent 技能目录。
# 幂等：重复安装覆盖旧版并提示。仅分发 skills/ds-search/ 一个自包含目录。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/skills/ds-search"
SKILL_NAME="ds-search"

usage() {
  cat <<'EOF'
用法: install.sh --agent=<target>
  <target> ∈ zcode|claude|codex|cursor|codebuddy|workbuddy|reasonx|all
示例:
  ./install.sh --agent=zcode
  ./install.sh --agent=all
EOF
}

target_dir() {
  case "$1" in
    zcode)     echo "$HOME/.agents/skills/$SKILL_NAME" ;;
    claude)    echo "$HOME/.claude/skills/$SKILL_NAME" ;;
    codex)     echo "$HOME/.codex/skills/$SKILL_NAME" ;;
    cursor)    echo "$HOME/.claude/skills/$SKILL_NAME" ;;  # Cursor 兼容读取 .claude 技能目录
    codebuddy) echo "$HOME/.codebuddy/skills/$SKILL_NAME" ;; # 未亲测路径，默认约定
    workbuddy) echo "$HOME/.workbuddy/skills/$SKILL_NAME" ;; # 未亲测路径，默认约定
    reasonx)   echo "$HOME/.reasonx/skills/$SKILL_NAME" ;;   # 未亲测路径，默认约定
    *) return 1 ;;
  esac
}

install_to() {
  local agent="$1" dest="$2"
  if [ -d "$dest" ]; then
    echo "[$agent] 检测到旧版本，覆盖安装: $dest"
    rm -rf "$dest"
  else
    echo "[$agent] 全新安装: $dest"
  fi
  mkdir -p "$(dirname "$dest")"
  cp -r "$SRC" "$dest"
  # runtime.conf 记录本机可执行命令，落位后改写为安装路径
  printf 'Runtime: Python\nCommand: python %s/scripts/ds_cli.py\n' "$dest" > "$dest/runtime.conf"
  if [ ! -f "$dest/SKILL.md" ] || [ ! -f "$dest/scripts/ds_cli.py" ]; then
    echo "[$agent] 错误: 安装不完整（缺 SKILL.md 或 scripts/ds_cli.py）" >&2
    exit 1
  fi
  echo "[$agent] 完成（SKILL.md + scripts/ + references/ + runtime.conf）"
}

[ -f "$SRC/SKILL.md" ] || { echo "错误: 未找到 $SRC（请在仓库根目录运行）" >&2; exit 1; }

case "${1:-}" in
  --agent=zcode)     install_to zcode     "$(target_dir zcode)" ;;
  --agent=claude)    install_to claude    "$(target_dir claude)" ;;
  --agent=codex)     install_to codex     "$(target_dir codex)" ;;
  --agent=cursor)    install_to cursor    "$(target_dir cursor)" ;;
  --agent=codebuddy) install_to codebuddy "$(target_dir codebuddy)" ;;
  --agent=workbuddy) install_to workbuddy "$(target_dir workbuddy)" ;;
  --agent=reasonx)   install_to reasonx   "$(target_dir reasonx)" ;;
  --agent=all)
    for a in zcode claude codex cursor codebuddy workbuddy reasonx; do
      install_to "$a" "$(target_dir "$a")"
    done
    ;;
  *) usage; exit 1 ;;
esac
