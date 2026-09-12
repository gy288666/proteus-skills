# 库的分发与版本

Proteus Skills 是独立技能仓库，代码库单独维护在 `proteus-automatic-api`。运行依赖为 Windows、Python 3.10+、单独安装的 Proteus 及所需模型、已安装的 `proteus-automatic-api`。技能仓库不复制 Python 库、wheel、Proteus 软件或演示固件。

## 依赖版本与来源

| 项目 | 当前声明 |
|---|---|
| 技能名称 / 调用名 | `Proteus Skills` / `$proteus-skills` |
| 独立代码仓库名称 | `proteus-automatic-api` |
| Python 分发名 | `proteus-automatic-api` |
| Python 导入名 | `proteus_automatic_api` |
| 本技能已验证的库版本 | `0.2.0` |
| 代码仓库完整地址 | 已确定仓库名；托管平台和所有者地址尚未提供 |
| 0.2.0 Release / wheel 地址 | 尚未配置正式地址 |
| PyPI 发布状态 | 未确认；不能据包名假定已发布 |

此处缺少发布地址不影响已经安装匹配库的使用者。缺少库时，先使用用户提供且来源明确的 0.2.0 wheel；如果既没有发行包也没有确定的下载地址，只询问安装所缺的来源，不猜仓库所有者、下载 URL 或替代同名包。

代码仓库和 Python 分发包统一命名为 `proteus-automatic-api`，0.2.0 wheel 为 `proteus_automatic_api-0.2.0-py3-none-any.whl`。Python 模块名称使用下划线：`proteus_automatic_api`。

## 独立安装

先选定符合要求的解释器，后续 pip、导入检查和任务脚本使用同一个解释器。以下以本机验证的 `py -3.12` 为例：

```powershell
py -3.12 -I -c "import proteus_automatic_api; print(proteus_automatic_api.__version__); print(proteus_automatic_api.__file__)"
```

匹配版本已安装就继续任务，不必下载库源码。若需要安装，将 PowerShell 变量 `$ProteusWheel` 赋为已取得、来源明确的 `proteus_automatic_api-0.2.0-py3-none-any.whl` 的绝对路径，再运行：

```powershell
py -3.12 -m pip install --no-index --no-deps "$ProteusWheel"
py -3.12 -I -c "import proteus_automatic_api; assert proteus_automatic_api.__version__ == '0.2.0'; print(proteus_automatic_api.__file__)"
```

这两个命令可在任意工作目录运行。如果当前环境装有旧名 `proteus-native`，迁移时先取得新 wheel，再用同一解释器卸载旧包（`py -3.12 -m pip uninstall proteus-native`），随后安装新 wheel，并将任务脚本的旧 `proteus_api` 导入改为 `proteus_automatic_api`。两个分发包共享内部模块，不能并装后再卸载旧包，否则可能删除新包所需文件；不准备迁移现有环境时使用新的虚拟环境。

安装器不属于技能的一部分；不要在技能目录执行 `pip install .`，不要通过修改 `PYTHONPATH` 或 `sys.path` 引用旁边的 `api/` 来代替安装验证。遇到其他版本，核对对应文档和接口后决定是否使用，不擅自替换正在被用户使用的环境。

## 发布者维护

将本技能文件夹的内容直接作为技能仓库根目录：`SKILL.md`、`agents/`、`references/`、`LICENSE`。所有相对文档链接都在此目录内；用户工作产物和库的源码测试不进入该仓库。`proteus-automatic-api` 仓库单独发布 wheel，演示工程或自有固件若需要分发，则另列资源及许可证。

正式公开前在本文件填写真实库仓库地址及经过核验的 0.2.0 Release/wheel 地址，并更新发布状态；不要提交示例 URL 冒充真实地址。日后若改为 PyPI 分发，先确认项目归属和该版本确实可用，再将安装命令改为明确的版本要求。

技能与库可以独立发布版本；技能只声明实际验证过的库版本。库 API 或限制改变时，核对参考示例和能力边界，在仅安装发行包的独立工作目录验证受影响的流程后再更新声明。不默认追踪 latest，不把完整库回归变成每次调用技能的前置步骤。
