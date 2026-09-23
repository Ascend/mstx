#!/bin/bash
# -------------------------------------------------------------------------
# 生成 C / CPP 单元测试的代码行覆盖率报告。
# 前置条件：已执行 `python build.py test local` 完成构建并运行用例，
#           构建目录为仓库根目录下的 build_ut_c / build_ut_cpp。
# 产物：仓库根目录 coverage/ 下的 lcov info、HTML 报告及 report.tar.gz。
# -------------------------------------------------------------------------
set -e
echo "***************Generate Coverage*****************"

CUR_DIR=$(dirname $(readlink -f "$0"))
TOP_DIR=$(readlink -f "${CUR_DIR}/../..")
OUT_DIR="${TOP_DIR}/coverage"

if [ -d "${OUT_DIR}" ]; then
    rm -rf "${OUT_DIR}"
fi
mkdir -p "${OUT_DIR}"

cd "${TOP_DIR}"

for build_dir in build_ut_c build_ut_cpp; do
    if [ ! -d "${build_dir}" ]; then
        echo "ERROR: build directory ${build_dir} not found, please run 'python build.py test local' first." >&2
        exit 1
    fi
done

lcov -c -d ./build_ut_c   -o "${OUT_DIR}/mstx_C.info"   --rc lcov_branch_coverage=1
lcov -c -d ./build_ut_cpp -o "${OUT_DIR}/mstx_CPP.info" --rc lcov_branch_coverage=1

# 仅保留产品代码（c/、python/），剔除第三方库、系统头文件与测试代码
for info in mstx_C.info mstx_CPP.info; do
    lcov -e "${OUT_DIR}/${info}" "${TOP_DIR}/c/*" "${TOP_DIR}/python/*" \
         -o "${OUT_DIR}/${info}" --rc lcov_branch_coverage=1
done

lcov -a "${OUT_DIR}/mstx_C.info" -a "${OUT_DIR}/mstx_CPP.info" \
     -o "${OUT_DIR}/mstx.info" --rc lcov_branch_coverage=1

genhtml "${OUT_DIR}/mstx.info" -o "${OUT_DIR}/report" --branch-coverage

lcov --summary "${OUT_DIR}/mstx.info" --rc lcov_branch_coverage=1

cd "${OUT_DIR}"
tar -zcvf report.tar.gz ./report
