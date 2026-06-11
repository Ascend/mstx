<h1 align="center">MindStudio Tools Extension Library</h1>

<div align="center">
<h2>Ascend AI Operator Tool Extension Interface Library</h2>

 [![Ascend](https://img.shields.io/badge/Community-MindStudio-blue.svg)](https://www.hiascend.com/en/developer/software/mindstudio) 
 [![License](https://badgen.net/badge/License/MulanPSL-2.0/blue)](./LICENSE)

</div>

## ✨ What's New

<span style="font-size:14px;">

🔹 **[2025.12.31]**: The MindStudio Tools Extension Library project is now fully open source.

</span>

## ️ ℹ️ Introduction

MindStudio Tools Extension Library (msTX) introduces the msTX instrumentation API. It allows you to customize collection time ranges or the start and end time points of key functions, identify information such as key functions or iterations, and quickly scope performance and operator issues.

## ⚙️ Features

By default, the mstx API has no functionality. You need to call the mstx API in your user application and then enable the mstx instrumentation feature for different scenarios, such as configuring `--mstx=on` when profiling data with the msprof command line, configuring `ACL_PROF_MSPROFTX` when profiling data with the AscendCL API, and configuring `mstx=True` when profiling data with the Ascend PyTorch Profiler API.

## 📦 Installation Guide

For environment dependencies and installation methods, see the [msTX Installation Guide](docs/en/install_guide/mstx_install_guide.md).

## 💡 Typical Use Cases

For typical usage scenarios, refer to [msOpProf Extended Functions](https://gitcode.com/Ascend/msopprof/blob/master/docs/en/user_guide/extended_functions.md#mstx-extension) and [msSanitizer API Reference](https://gitcode.com/Ascend/mssanitizer/blob/master/docs/en/api_reference/mssanitizer_api_reference.md#mstx-extension).

## 📚 API Reference

For details on msTX APIs, refer to [msTX API Reference](docs/en/api_reference/README.md).

## 🛠️ Contribution Guide

Contributions are welcome. For details, see the [Contribution Guide](./docs/zh/contributing/contributing_guide.md).  

## ⚖️ Related Information

🔹 [Release Notes](./docs/en/release_notes/release_notes.md)  
🔹 [LICENSE Statement](./docs/en/legal/license_notice.md)  
🔹 [Security Statement](./docs/en/legal/security_statement.md)  
🔹 [Disclaimer](./docs/en/legal/disclaimer.md)  

## 🤝 Suggestions and Communication

We welcome contributions to the community. If you have any questions or suggestions, please submit an [Issue](https://gitcode.com/Ascend/mstx/issues), and we will respond as soon as possible. Thank you for your support.

|                                      📱 Follow the MindStudio Official Account                                       | 💬 More Communication and Support                                                                                                                                                                                                                                                                                                                                                                                                                     |
|:-------------------------------------------------------------------------------------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| <img src="https://gitcode.com/Ascend/msot/blob/master/docs/zh/figures/readme/officialAccount.png" width="120"><br><sub>*Scan the QR code to get the latest updates*</sub> | 💡 **Join the WeChat Group**:<br>Follow the official account and reply "communication group" to get the group QR code.<br><br>🛠️ **Other Channels**:<br>👉 Ascend Assistant: [![WeChat](https://img.shields.io/badge/WeChat-07C160?style=flat-square&logo=wechat&logoColor=white)](https://gitcode.com/Ascend/msot/blob/master/docs/zh/figures/readme/xiaozhushou.png)<br>👉 Ascend Forum: [![Website](https://img.shields.io/badge/Website-%231e37ff?style=flat-square&logo=RSS&logoColor=white)](https://www.hiascend.com/forum/) |

## 🙏 Acknowledgments

This tool is jointly contributed by the following departments of Huawei:    
🔹 Ascend Computing MindStudio Development Dept  
🔹 Ascend Computing Ecosystem Enablement Dept 
🔹 Ascend AI Cloud Service  
🔹 2012 Compiler Lab  
🔹 2012 Markov Lab  
Thank you for every PR from the community. Contributions are welcome.
