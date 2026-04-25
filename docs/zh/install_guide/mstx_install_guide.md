# MindStudio Tools Extension Library安装指南

<br>

## 1. 安装说明

msTX工具的安装方式包括：

- 二进制安装：msTX工具完整功能已集成在CANN包中发布，可直接安装CANN包，请参考《[CANN 官方安装指南](https://www.hiascend.com/cann/download)》，按文档逐步完成安装与配置。
- 源码安装：如需使用最新代码的功能，或对源码进行修改以增强功能，可下载本仓库代码，自行编译、打包工具并完成安装，具体请参见[源码安装](#2-源码安装)。

## 2. 源码安装

如需使用最新代码的功能，或对源码进行修改以增强功能，可下载本仓库代码，自行编译、打包工具并完成安装。

### 2.1 环境准备

请按照以下文档进行环境配置：《[算子工具开发环境安装指导](https://gitcode.com/Ascend/msot/blob/26.0.0/docs/zh/common/dev_env_setup.md)》。

### 2.2 项目依赖

由于本项目中的代码依赖python3的头文件，因此需要编译环境中安装python3-dev包，可通过如下命令执行：

```sh
apt-get install python3-dev
```

### 2.3 构建打包

```sh
python build.py
```

### 2.4 安装whl包

```sh
cd output
pip3 install mstx-xxxxx.whl
```

## 2.5 升级

如需使用whl包替换运行环境原有已安装的whl包，执行如下安装操作：

```sh
pip3 install mstx-xxxxx.whl --force-reinstall
```

安装过程中，若提示是否替换原有安装包：
输入"y"，则安装包会自动完成升级操作。

## 2.6 卸载

卸载则通过如下命令卸载：

```sh
pip3 uninstall mstx-xxxxx.whl 
```
