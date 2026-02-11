# KarabinerPyX

**A Python DSL for Declarative, Safe, and Powerful Karabiner-Elements Configuration**

---

[English](README.md) | 中文

---

## 1. 项目简介

**KarabinerPyX** 是一个用于 **以 Python DSL 的方式构建 Karabiner-Elements 配置文件（karabiner.json）** 的工具。

它的目标不是“生成 JSON”，
而是将键盘映射提升为一种：

> **可组合、可复用、可维护、可自动部署的工程化配置语言**

---

## 2. 为什么需要 KarabinerPyX？

### 2.1 Karabiner 原生 JSON 的问题

* JSON 冗长、嵌套深
* 难以抽象 layer / combo / sequence
* shell_command、AppleScript 大量重复
* 修改配置有风险（容易写坏）
* 配置生效需要手动操作

---

### 2.2 设计灵感来源

KarabinerPyX 综合并扩展了以下项目的思想：

| 项目                    | 借鉴点                    |
| --------------------- | ---------------------- |
| GokuRakuJoudo         | template 抽象、EDN 风格 DSL |
| karabiner.ts          | 类型化、可组合的配置生成           |
| Configuration as Code | 把键盘当成“输入系统代码”          |

---

## 3. 设计哲学

* **Configuration as Code**
* **Declarative over Imperative**
* **Composable Layers**
* **Safe by Default**: 自动备份旧配置（保留最近10个），应用前支持 Dry-run 预览差异。
* **Automation First**: 每次 commit 自动同步文档，CLI 级一键部署。

---

## 4. 功能总览（Feature Overview）

### 4.1 基础映射能力

* 单键映射（A -> B）
* modifiers（mandatory / optional）
* tap / hold 行为（to_if_alone / to_if_held_down）

---

### 4.2 Layer 系统

#### 4.2.1 单触发层（Hold Layer）

```python
LayerStackBuilder("hyper", "right_command")
```

* 按住进入 layer
* 释放退出
* 使用 Karabiner variable 实现

---

#### 4.2.2 Layer 内映射

```python
hyper.map("j", "left_arrow")
hyper.map("k", "down_arrow")
```

---

### 4.3 Layer Stacking（层叠加）

#### 4.3.1 多触发键进入新层

```python
LayerStackBuilder("hyper_alt", ["right_command", "right_option"])
```

* 同时按住多个 layer key
* 进入新的 mode

**典型用途：**

* Hyper + Alt -> Window / Tiling Mode
* Hyper + Ctrl -> Dev Mode

---

### 4.4 Combo Mapping（同时键）

```python
hyper.map_combo(["j", "k"], "escape")
```

* 同时按下多个键
* 使用 Karabiner simultaneous 机制

---

### 4.5 Sequence / 多键序列

```python
hyper.map_sequence(["g", "g"], "home")
```

* 顺序输入一组键
* 触发目标行为
* 内部使用 variable + delayed_action

#### 4.5.1 Timing Control

```python
hyper.set_sequence_timeout(500)  # 毫秒
```

---

### 4.6 Macro 系统

#### 4.6.1 多 key_code 宏

* 一个键触发多个按键

---

#### 4.6.2 Typed Text Macro（自动输入文本）

```python
hyper.map_macro("t", template_type="typed_text", text="Hello, world!")
```

用途：

* 常用短语
* 代码模板
* Commit message

---

## 5. Template-Based Macro（核心抽象）

### 5.1 设计目标

借鉴 **GokuRakuJoudo :templates**：

* 不在 mapping 中硬编码 shell_command
* 所有命令统一从模板生成

---

### 5.2 模板定义

```python
MACRO_TEMPLATES = {
  "typed_text": 'osascript -e \'tell application "System Events" to keystroke "{text}"\'',
  "alfred": 'osascript -e \'tell application id "com.runningwithcrayons.Alfred" to run trigger "{trigger}" in workflow "{workflow}" with argument "{arg}"\'',
  "keyboard_maestro": 'osascript -e \'tell application "Keyboard Maestro Engine" to do script "{script}"\'',
  "open": 'open "{path}"'
}
```

---

### 5.3 使用方式

```python
hyper.map_macro(
  "a",
  template_type="alfred",
  trigger="search",
  workflow="MyWorkflow",
  arg="query"
)
```

---

## 6. Conditional Layers（条件层）

### 6.1 App 条件

```python
hyper.when_app([
  "com.apple.Terminal",
  "com.microsoft.VSCode"
])
```

* 仅在指定 App 前台时生效

---

## 7. 配置生成与部署（Deployment）

### 7.1 自动备份（Safety First）

每次写入新配置前：

* 自动备份旧 `karabiner.json`
* 使用时间戳命名

```text
~/.config/karabiner/
  ├── karabiner.json
  ├── karabiner_backup_20251217_014233.json
```

---

### 7.2 JSON 校验

* 写入后立即进行 JSON parse 校验
* 防止损坏配置

---

### 7.3 自动 Reload / Apply

```python
config.save(apply=True)
```

内部行为：

1. 备份旧配置
2. 写入新配置
3. 校验 JSON
4. `launchctl kickstart` 重启 Karabiner

无需手动打开 GUI。

---

## 8. CLI 工具 (kpyx)

KarabinerPyX 包含一个功能强大的命令行工具，用于管理你的配置：

- `kpyx list <script.py>`：列出脚本中定义的所有 Profile 和 Rule。
- `kpyx build <script.py> -o output.json`：生成 JSON 文件。
- `kpyx dry-run <script.py>`：**强烈推荐**，在应用前预览配置差异（Diff）。
- `kpyx apply <script.py>`：直接应用配置到 Karabiner（包含自动备份和清理）。
- `kpyx restore`：从备份文件夹中交互式选择并恢复之前的配置。
- `kpyx docs <script.py> -o CHEAT_SHEET.md`：自动生成 Markdown 格式的说明文档。
- `kpyx stats <script.py> --json`：输出机器可读的静态分析报告。

### 8.1 Watch & Service

KarabinerPyX 提供自动监听与服务化能力：

```bash
# 安装可选依赖（watchfiles）
uv add "karabinerpyx[watch]"
# 或
pip install "karabinerpyx[watch]"

# 监听脚本变更并自动应用
kpyx watch path/to/config.py

# 使用默认路径或环境变量
export KPYX_CONFIG_FILE=~/.config/karabiner/config.py
kpyx watch

# 安装并启动后台服务（launchd）
kpyx service install path/to/config.py

# 查看服务状态
kpyx service status

# 卸载服务
kpyx service uninstall
```

可用环境变量：

- `KPYX_CONFIG_FILE`：默认配置脚本路径。
- `KPYX_WATCH_DEBOUNCE_MS`：监听去抖（毫秒，默认 500）。

---

## 9. 核心预设 (Presets)

KarabinerPyX 内置了一些常用的配置片段，可以直接在你的脚本中引用：

```python
from karabinerpyx.presets import hyper_key_rule, vim_navigation, common_system_shortcuts

# 1. 一键设置 Hyper Key (CapsLock -> Cmd+Ctrl+Opt+Shift)
profile.add_rule(hyper_key_rule())

# 2. 为任何 Layer 注入 Vim 导航 (HJKL -> 方向键)
hyper = LayerStackBuilder("hyper", "right_command")
vim_navigation(hyper)
```

---

## 10. 使用示例（完整）

```python
from karabinerpyx import KarabinerConfig, Profile, LayerStackBuilder

hyper = (
    LayerStackBuilder("hyper", "right_command")
    .map("j", "left_arrow")
    .map("k", "down_arrow")
    .map_macro("t", template_type="typed_text", text="Hello from KarabinerPyX!")
)

profile = Profile("KarabinerPyX Demo")
for rule in hyper.build_rules():
    profile.add_rule(rule)

KarabinerConfig().add_profile(profile).save(apply=True)
```

---

## 11. 非功能性需求（NFR）

* 高可维护性
* 高可扩展性
* DSL 语义清晰
* 支持未来 snapshot testing / diff / rollback

---

## 12. 项目边界（Out of Scope）

* 不替代 Karabiner-Elements 本体
* 不实现 GUI
* 不绕过 Karabiner 安全机制

---

## 13. 项目愿景

> **把键盘映射，从“手写 JSON”
> 提升为“可编程的人机接口设计语言”。**

KarabinerPyX 的长期目标是成为：

* macOS 高级用户
* 工程师
* 键盘重度用户

的 **键盘操作系统 DSL**。

---

## 14. License & Future

* MIT License（建议）
* 未来方向：

  * dry-run / diff
  * 自动回滚
  * preset layers
  * 文档生成

---

**KarabinerPyX — Design your keyboard like you design software.**

---

## 迁移说明

v0.2 引入了破坏性升级，详见：

- [MIGRATION.md](MIGRATION.md)
