from setuptools import setup
from setuptools.command.install import install
import os

try:
    from packaging.tags import sys_tags
    _has_packaging = True
except ImportError:
    _has_packaging = False

def _get_plat_name(name):
    if not _has_packaging:
        return name
    try:
        return next(sys_tags()).platform
    except Exception:
        return name


class CustomInstall(install):
    def run(self):
        install.run(self)
        # 安装路径 = site-packages
        install_dir = os.path.abspath(self.install_lib)
        src = os.path.join("lib64", "mstx.so")
        dst = os.path.join(install_dir, "mstx.so")
        src_abs = os.path.join(install_dir, src)
        if os.path.exists(dst) or os.path.islink(dst):
            os.unlink(dst)
        rel_src = os.path.relpath(src_abs, install_dir)
        os.symlink(rel_src, dst)

setup(
    name = 'mstx',
    version = os.environ.get('WHL_VERSION', '26.0.0'),
    author =' mstx',
    author_email = 'mstx',
    description = 'mstx',
    long_description = open('README.md', encoding='utf-8').read(),
    long_description_content_type = 'text/markdown',
    url = 'https://gitcode.com/Ascend/mstx',
    options={
        'bdist_wheel':{
            'plat_name': _get_plat_name('')}},
    packages = ['lib64', 'include'],
    cmdclass={"install": CustomInstall},
    include_package_data = True,
    license= 'Mulan PSL v2',
    classifiers = [
        'Programming Language :: Python :: 3',
        'Operating System :: Linux',
    ],
    python_requires = '>=3.7'
)
