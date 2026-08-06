#!/bin/bash
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This file is part of the MindStudio project.
# Copyright (c) 2026 Huawei Technologies Co.,Ltd.
#
# MindStudio is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#
#          http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# 容器首次创建后的幂等初始化脚本
# 所有动作必须幂等，失败不阻塞容器创建
# -------------------------------------------------------------------------
set -e

log() { echo "[post-create] $*"; }
warn() { echo "[post-create] WARN: $*"; }

# ──────────────────────────────────────────────────────────────────────────────
# 1. 用户级命令目录
# ──────────────────────────────────────────────────────────────────────────────
configure_user_bin() {
    log "Configuring user bin directory..."
    mkdir -p "$HOME/.local/bin"
    npm config set prefix "$HOME/.local" 2>/dev/null || warn "npm config set prefix failed"

    # 写入 shell 启动文件 (只写入一次)
    local marker="# mstx-devcontainer-user-bin"
    for rcfile in "$HOME/.bashrc" "$HOME/.bash_profile"; do
        if [ -f "$rcfile" ] && ! grep -qF "$marker" "$rcfile"; then
            cat >> "$rcfile" <<EOF
$marker
export PATH="\$HOME/.local/bin:\$PATH"
EOF
            log "Appended PATH to $rcfile"
        fi
    done
}

# ──────────────────────────────────────────────────────────────────────────────
# 2. Python 3 (最低要求 3.8)
# ──────────────────────────────────────────────────────────────────────────────
configure_python3() {
    log "Configuring Python 3..."
    # MindStudio 构建镜像使用 pyenv / aswitch 切换 Python 版本
    # 尝试加载镜像自带的 Python 切换脚本
    if [ -f "/etc/profile.d/pyenv.sh" ]; then
        source /etc/profile.d/pyenv.sh 2>/dev/null || warn "Failed to source pyenv.sh"
        log "Loaded pyenv profile"
    fi

    if command -v python3 &>/dev/null; then
        log "Python 3 found: $(python3 --version 2>&1)"
    else
        warn "python3 not found in PATH"
    fi
}

# ──────────────────────────────────────────────────────────────────────────────
# 2.5 安装编译和测试依赖 (幂等)
# ──────────────────────────────────────────────────────────────────────────────
install_build_deps() {
    log "Installing system build dependencies..."

    # --- 系统包 (dnf) ---
    if command -v dnf &>/dev/null; then
        local sys_pkgs=(
            python3-devel
        )
        local missing_sys=()
        for pkg in "${sys_pkgs[@]}"; do
            if ! rpm -q "$pkg" &>/dev/null; then
                missing_sys+=("$pkg")
            else
                log "  System pkg OK: $pkg"
            fi
        done
        if [ ${#missing_sys[@]} -gt 0 ]; then
            log "  Installing: ${missing_sys[*]}"
            sudo dnf install -y "${missing_sys[@]}" 2>/dev/null || warn "dnf install failed: ${missing_sys[*]}"
        fi
        # gitleaks 用于 pre-commit 密钥扫描
        if ! command -v gitleaks &>/dev/null; then
            log "  Installing gitleaks..."
            sudo dnf install -y gitleaks 2>/dev/null || warn "gitleaks install failed"
        else
            log "  System pkg OK: gitleaks"
        fi
    elif command -v apt-get &>/dev/null; then
        local sys_pkgs=(
            python3-dev
        )
        local missing_sys=()
        for pkg in "${sys_pkgs[@]}"; do
            if ! dpkg -s "$pkg" &>/dev/null; then
                missing_sys+=("$pkg")
            else
                log "  System pkg OK: $pkg"
            fi
        done
        if [ ${#missing_sys[@]} -gt 0 ]; then
            log "  Installing: ${missing_sys[*]}"
            sudo apt-get update -qq && sudo apt-get install -y "${missing_sys[@]}" 2>/dev/null || warn "apt-get install failed: ${missing_sys[*]}"
        fi
    fi

    # --- pip 包 ---
    # 容器内可能存在多套 Python（pyenv python3.11 + 系统 python3），
    # 两套都需要装，避免构建脚本调不同 Python 时报 ModuleNotFoundError
    local pip_pkgs=(
        packaging
        wheel
        pytest
        coverage
        pre-commit
    )

    for PY in $(command -v python3 2>/dev/null) $(command -v python 2>/dev/null); do
        log "Installing pip packages for: $($PY --version 2>&1)"
        "$PY" -m pip install --quiet --upgrade pip setuptools >/dev/null 2>&1 || warn "pip/setuptools upgrade failed for $PY"

        local missing_pip=()
        for pkg in "${pip_pkgs[@]}"; do
            if ! "$PY" -m pip show "$pkg" &>/dev/null; then
                missing_pip+=("$pkg")
            else
                log "  Pip pkg OK ($PY): $pkg"
            fi
        done
        if [ ${#missing_pip[@]} -gt 0 ]; then
            log "  Installing for $PY: ${missing_pip[*]}"
            "$PY" -m pip install "${missing_pip[@]}" || warn "pip install failed for $PY: ${missing_pip[*]}"
        fi

        # auditwheel 可选，缺失时 build.py 会跳过 wheel repair
        if ! "$PY" -m pip show auditwheel &>/dev/null; then
            log "  Installing optional auditwheel for $PY"
            "$PY" -m pip install --quiet auditwheel 2>/dev/null || warn "auditwheel install failed for $PY (optional)"
        else
            log "  Pip pkg OK ($PY): auditwheel"
        fi
    done

    # 确保 googletest 目录存在 (build.py test 会下载，这里只是提前检查)
    if [ ! -d "thirdparty/googletest" ]; then
        warn "thirdparty/googletest not yet present (will be downloaded by 'python3 build.py test')"
    fi

    log "Build dependencies check complete"
}

# ──────────────────────────────────────────────────────────────────────────────
# 3. Git 身份同步
# ──────────────────────────────────────────────────────────────────────────────
sync_git_identity() {
    log "Syncing Git identity..."
    local gitconfig="/home/mindstudio/.devcontainer-host-gitconfig"
    if [ -f "$gitconfig" ] && [ -s "$gitconfig" ]; then
        grep '^user\.name' "$gitconfig" | sed 's/^user\.name=//' | xargs git config --global user.name 2>/dev/null || true
        grep '^user\.email' "$gitconfig" | sed 's/^user\.email=//' | xargs git config --global user.email 2>/dev/null || true
        log "Git identity synced from host"
    else
        warn "No host Git config found, skipping identity sync"
    fi
}

# ──────────────────────────────────────────────────────────────────────────────
# 4. 开发命令提示
# ──────────────────────────────────────────────────────────────────────────────
append_dev_hint_once() {
    local marker="# mstx-dev-hint"
    local rcfile="$HOME/.bashrc"

    if grep -qF "$marker" "$rcfile" 2>/dev/null; then
        return
    fi

    cat >> "$rcfile" <<EOF
$marker
# mstx development commands:
#   python3 build.py              Build Release (full)
#   python3 build.py local        Build Release (skip deps)
#   python3 build.py test         Build and run unit tests
#   python3 build.py test local   Run unit tests (skip deps)
EOF
    log "Appended dev hints to $rcfile"
}

# ──────────────────────────────────────────────────────────────────────────────
# 5. pre-commit 自动安装
# ──────────────────────────────────────────────────────────────────────────────
install_pre_commit_hook() {
    log "Installing pre-commit hook..."

    # 确保 ~/.local/bin 在当前 shell 的 PATH 中 (pip 安装的 pre-commit 可能在这里)
    export PATH="$HOME/.local/bin:$PATH"

    # 多种方式定位 pre-commit: 直接命令 > python3 -m > python -m
    local pre_commit_cmd=""
    if command -v pre-commit &>/dev/null; then
        pre_commit_cmd="pre-commit"
    elif python3 -m pre_commit --version &>/dev/null 2>&1; then
        pre_commit_cmd="python3 -m pre_commit"
    elif python -m pre_commit --version &>/dev/null 2>&1; then
        pre_commit_cmd="python -m pre_commit"
    else
        warn "pre-commit not found, skipping hook installation"
        return
    fi

    if [ ! -d ".git" ]; then
        warn "Not a Git repository, skipping pre-commit hook"
        return
    fi

    $pre_commit_cmd install || warn "pre-commit install failed"
    log "pre-commit hook installed via: $pre_commit_cmd"
}

# ──────────────────────────────────────────────────────────────────────────────
# 6. clangd
# ──────────────────────────────────────────────────────────────────────────────
setup_clangd() {
    log "Setting up clangd..."
    if command -v clangd &>/dev/null; then
        log "clangd found: $(clangd --version 2>&1 | head -1)"
        return
    fi

    warn "clangd not found, attempting to install..."
    if command -v dnf &>/dev/null; then
        sudo dnf install -y clangd 2>/dev/null || warn "Failed to install clangd via dnf"
    elif command -v apt-get &>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y clangd 2>/dev/null || warn "Failed to install clangd via apt-get"
    else
        warn "Cannot install clangd automatically"
    fi

    if command -v clangd &>/dev/null; then
        log "clangd installed successfully"
    else
        warn "clangd is not available, C++ IDE features will be limited"
    fi
}

# ──────────────────────────────────────────────────────────────────────────────
# 7. 忽略 .vscode/settings.json 本地修改
# ──────────────────────────────────────────────────────────────────────────────
ignore_vscode_settings() {
    log "Setting up skip-worktree for .vscode/settings.json..."
    if [ -f ".vscode/settings.json" ]; then
        git update-index --skip-worktree .vscode/settings.json 2>/dev/null || true
        log ".vscode/settings.json set to skip-worktree"
    fi
}

# ──────────────────────────────────────────────────────────────────────────────
# 8. compile_commands.json 提示
# ──────────────────────────────────────────────────────────────────────────────
check_compile_commands() {
    if [ ! -f "build/compile_commands.json" ]; then
        warn "build/compile_commands.json not found (expected on cold start)"
        warn "Run 'python3 build.py' to generate it for clangd support"
    else
        log "compile_commands.json found, clangd ready"
    fi
}

# ──────────────────────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────────────────────
log "Starting container initialization..."

configure_user_bin
configure_python3
install_build_deps
sync_git_identity
append_dev_hint_once
install_pre_commit_hook
setup_clangd
ignore_vscode_settings
check_compile_commands

log "Container initialization complete!"
