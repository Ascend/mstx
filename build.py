#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This file is part of the MindStudio project.
# Copyright (c) 2025 Huawei Technologies Co.,Ltd.
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
import argparse
import logging
import multiprocessing
import os
import shutil
import subprocess
import sys
import sysconfig
import traceback
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class BuildManager:
    """
    统一构建管理：依赖拉取 → CMake 配置 → 并行编译 → 安装 / 测试。

    用法:
        python build.py                  完整构建（拉取依赖 + Release 编译）
        python build.py local            本地构建（跳过依赖拉取, Release 编译）
        python build.py test             单元测试（拉取依赖 + Debug 编译 + 执行测试）
        python build.py test local       单元测试（跳过依赖拉取, Debug 编译 + 执行测试）
        python build.py -r <revision>    指定依赖的内部源码仓(例如msopcom)的 Git 分支/标签/commit
        python build.py -v <version>     指定构建版本号，同时覆盖 --build-version 和 --whl-version
        python build.py -e KEY=VALUE     指定额外构建选项，可多次使用

    参数说明:
        - 参数: command : 构建动作: 为空时为全构建, local 为跳过依赖下载, test 为运行单元测试。
        - 参数: -r, --revision : 指定 Git 修订版本或标签用于依赖检出。
        - 参数: -v, --version : 指定构建版本号；若设置，则同时覆盖 --build-version 和 --whl-version 的值。
        - 参数: --build-version, --whl-version : 历史参数，保留用于兼容；设置了 --version 时以 --version 为准。
        - 参数: -e, --extra : 额外构建选项，格式为 KEY=VALUE，可多次指定。

    产物归档:
        产品构建完成后，归档到 artifacts/ 目录中。
    """

    def __init__(self):
        self.project_root = Path(__file__).resolve().parent
        self.build_jobs = multiprocessing.cpu_count()
        argument_parser = argparse.ArgumentParser(description='Build the project and optionally run tests.')
        argument_parser.add_argument('command', nargs='*', default=[],
                                     choices=[[], 'local', 'test'],
                                     help='Build action: omit for full build, "local" to skip dependency download, "test" to run unit tests')
        argument_parser.add_argument('-r', '--revision',
                                     help='Specify Git revision for internal dependent repo (e.g., msopcom).')
        argument_parser.add_argument('--build-version', type=str, default=None, help='Build version for run/exe/dmg packages')
        argument_parser.add_argument('--whl-version', type=str, default=None, help='WHL version for Python wheel packages')
        argument_parser.add_argument('-v', '--version', type=str, default=None,
                                     help='Build version, overrides --build-version and --whl-version if set')
        argument_parser.add_argument('-e', '--extra', metavar='KEY=VALUE', action='append', default=[],
                                     help='Extra build options in KEY=VALUE format, can be specified multiple times')
        self.parsed_arguments = argument_parser.parse_args()

        if self.parsed_arguments.version is not None:
            self.parsed_arguments.build_version = self.parsed_arguments.version
            self.parsed_arguments.whl_version = self.parsed_arguments.version

    def _execute_command(self, command_sequence, timeout_seconds=36000, cwd=None, env=None):
        logging.info("Running: %s", " ".join(command_sequence))
        subprocess.run(command_sequence, timeout=timeout_seconds, check=True, cwd=cwd, env=env)

    def _build_test_target(self, lang, unit_test_build_dir):
        """构建指定语言变体（C 或 CPP）的测试目标。"""
        test_build_path = Path(f"{unit_test_build_dir}_{lang.lower()}")
        test_build_path.mkdir(exist_ok=True)

        self._execute_command(["cmake", "..", "-DBUILD_TESTS=ON", f"-DLANG={lang}", "-DCMAKE_BUILD_TYPE=Debug", "-DPython_ROOT_DIR=" + sysconfig.get_config_var("prefix"), "-DPython_EXECUTABLE=" + sys.executable],
                              cwd=str(test_build_path))
        self._execute_command(["make", "-j", str(self.build_jobs)],
                              cwd=str(test_build_path))

    def _run_c_tests(self, build_dir, lang):
        """运行 C/CPP 单元测试，覆盖无初始化 / preload / 正常环境 / 异常环境等场景。"""
        cwd = str(build_dir)
        test_binary = f"./test/c/mstx_test_{lang}"
        test_lib_binary = f"./test/c/mstx_test_lib_{lang}"
        lib_path = str(build_dir / "c") + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')

        logging.info("Testing %s without init", lang)
        self._execute_command([test_binary], cwd=cwd)
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = lib_path
        self._execute_command([test_lib_binary], cwd=cwd, env=env)

        logging.info("Testing %s init with preload", lang)
        env = os.environ.copy()
        env["LD_PRELOAD"] = "./test/c/libinjection_test.so"
        self._execute_command([test_binary], cwd=cwd, env=env)
        env["LD_LIBRARY_PATH"] = lib_path
        self._execute_command([test_binary], cwd=cwd, env=env)

        logging.info("Testing %s init with normal env", lang)
        env = os.environ.copy()
        env["MSTX_INJECTION_PATH"] = cwd + "/test/c/libinjection_test.so"
        self._execute_command([test_binary], cwd=cwd, env=env)
        env["LD_LIBRARY_PATH"] = lib_path
        self._execute_command([test_binary], cwd=cwd, env=env)

        logging.info("Testing %s init with abnormal env", lang)
        env = os.environ.copy()
        env["MSTX_INJECTION_PATH"] = "1234"
        self._execute_command([test_binary], cwd=cwd, env=env)
        env["LD_LIBRARY_PATH"] = lib_path
        self._execute_command([test_binary], cwd=cwd, env=env)

    def _run_python_tests(self, build_dir):
        """运行 Python 单元测试，覆盖无初始化 / preload / 正常环境 / 异常环境等场景。"""
        cwd = str(build_dir)
        test_dir = str(build_dir / "test" / "python")
        mstx_so_dir = str(build_dir / "python")
        lib_path = str(build_dir / "c") + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')
        base_pythonpath = mstx_so_dir + os.pathsep + os.environ.get('PYTHONPATH', '')

        os.makedirs(test_dir, exist_ok=True)
        shutil.copytree(str(self.project_root / "test" / "python"), test_dir, dirs_exist_ok=True)

        logging.info("Testing Python without init")
        env = os.environ.copy()
        env["PYTHONPATH"] = base_pythonpath
        self._execute_command([sys.executable, "-m", "pytest", "./test/python/test_mstx_without_init.py"], cwd=cwd, env=env)
        env["LD_LIBRARY_PATH"] = lib_path + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')
        self._execute_command([sys.executable, "-m", "pytest", "./test/python/test_mstx_without_init.py"], cwd=cwd, env=env)

        logging.info("Testing Python init with preload")
        env = os.environ.copy()
        env["LD_PRELOAD"] = "./test/c/libinjection_test.so"
        env["PYTHONPATH"] = base_pythonpath
        self._execute_command([sys.executable, "-m", "pytest", "./test/python/test_mstx_with_init.py"], cwd=cwd, env=env)
        env["LD_LIBRARY_PATH"] = lib_path + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')
        self._execute_command([sys.executable, "-m", "pytest", "./test/python/test_mstx_with_init.py"], cwd=cwd, env=env)

        logging.info("Testing Python init with normal env")
        env = os.environ.copy()
        env["MSTX_INJECTION_PATH"] = cwd + "/test/c/libinjection_test.so"
        env["PYTHONPATH"] = base_pythonpath
        self._execute_command([sys.executable, "-m", "pytest", "./test/python/test_mstx_with_init.py"], cwd=cwd, env=env)
        env["LD_LIBRARY_PATH"] = lib_path + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')
        self._execute_command([sys.executable, "-m", "pytest", "./test/python/test_mstx_with_init.py"], cwd=cwd, env=env)

        logging.info("Testing Python init with abnormal env")
        env = os.environ.copy()
        env["MSTX_INJECTION_PATH"] = "1234"
        env["PYTHONPATH"] = base_pythonpath
        self._execute_command([sys.executable, "-m", "pytest", "./test/python/test_mstx_without_init.py"], cwd=cwd, env=env)
        env["LD_LIBRARY_PATH"] = lib_path + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')
        self._execute_command([sys.executable, "-m", "pytest", "./test/python/test_mstx_without_init.py"], cwd=cwd, env=env)

    def _archive_artifacts(self):
        """将产品构建产物归档到工程根目录的 artifacts 目录。"""
        artifact_patterns = ("*.whl",)
        artifacts_dir = self.project_root / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        search_dirs = (self.project_root / "output",)
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for pattern in artifact_patterns:
                for artifact in search_dir.rglob(pattern):
                    destination = artifacts_dir / artifact.name
                    logging.info("Archiving artifact: %s -> %s", artifact, destination)
                    shutil.copy2(artifact, destination)

    def _repair_wheels(self):
        """使用 auditwheel 修复 artifacts 中的 manylinux wheel，并用修复后的包替换原始包。"""
        if shutil.which("auditwheel") is None:
            logging.info("auditwheel not found in environment, skipping wheel repair.")
            return

        artifacts_dir = self.project_root / "artifacts"
        tmp_dir = artifacts_dir / ".repair_tmp"
        tmp_dir.mkdir(exist_ok=True)

        whl_files = list(artifacts_dir.glob("*.whl"))
        if not whl_files:
            logging.info("No wheel files found in artifacts, skipping auditwheel repair.")
            shutil.rmtree(tmp_dir)
            return

        logging.info("============ start to repair wheels with auditwheel ============")
        for whl in whl_files:
            logging.info("Repairing: %s", whl.name)
            self._execute_command(
                ["auditwheel", "repair", str(whl), "-w", str(tmp_dir)]
            )
            # 删除原始 wheel，将修复后的 wheel 移入替换
            whl.unlink()
            repaired_whls = list(tmp_dir.glob("*.whl"))
            for repaired_whl in repaired_whls:
                destination = artifacts_dir / repaired_whl.name
                shutil.move(str(repaired_whl), str(destination))
                logging.info("Replaced: %s -> %s", whl.name, destination.name)

        shutil.rmtree(tmp_dir)
        logging.info("============ auditwheel repair completed ============")

    def run(self):
        os.chdir(self.project_root)

        # 将 --whl-version 传入环境变量，供 setup.py 通过 os.environ.get('WHL_VERSION') 读取
        whl_version = self.parsed_arguments.whl_version
        if whl_version:
            os.environ['WHL_VERSION'] = whl_version
            logging.info("WHL_VERSION set to: %s", whl_version)

        build_version = self.parsed_arguments.build_version
        if build_version:
            logging.info("--build-version: %s", build_version)

        for option in self.parsed_arguments.extra:
            key, _, value = option.partition('=')
            logging.info("--extra: %s = %s", key, value)

        # 在非 local 场景下按需更新依赖；在 local 场景下仅使用本地已有代码，不更新依赖。
        if 'local' not in self.parsed_arguments.command:
            from download_dependencies import DependencyManager
            DependencyManager(self.parsed_arguments).run()

        if 'test' in self.parsed_arguments.command:
            # -------------------- 单元测试 --------------------
            # ut 使用单独的目录构建，与 build 区分开，避免相互影响
            unit_test_build_dir = self.project_root / "build_ut"

            for lang in ("C", "CPP"):
                self._build_test_target(lang, unit_test_build_dir)

            ut_c_dir = Path(f"{unit_test_build_dir}_c")
            ut_cpp_dir = Path(f"{unit_test_build_dir}_cpp")

            self._run_c_tests(ut_c_dir, "C")
            self._run_c_tests(ut_cpp_dir, "CPP")
            self._run_python_tests(ut_cpp_dir)
        else:
            # -------------------- 产品构建 --------------------
            product_build_dir = self.project_root / "build"
            product_build_dir.mkdir(exist_ok=True)
            os.chdir(product_build_dir)

            self._execute_command(["cmake", ".."])
            self._execute_command(["make", "-j", str(self.build_jobs)])
            self._execute_command(["make", "install"])

            self._archive_artifacts()
            self._repair_wheels()


if __name__ == "__main__":
    try:
        BuildManager().run()
    except Exception:
        logging.error(f"Unexpected error: {traceback.format_exc()}")
        sys.exit(1)
