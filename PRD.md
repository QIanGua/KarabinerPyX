# KarabinerPyX 功能需求文档（FRD）

## 1. 项目概述

### 1.1 项目名称

**KarabinerPyX**

### 1.2 项目定位

KarabinerPyX 是一个用于 **以 Python DSL 的方式声明式生成 Karabiner-Elements 配置** 的工具，目标是：

* 将复杂、易错、难维护的 Karabiner JSON
* 提升为 **可组合、可复用、可测试、可演进的“键盘映射代码”**

### 1.3 设计哲学

* **Configuration as Code**
* 借鉴 GokuRakuJoudo（EDN）与 karabiner.ts（TS）的优点
* 强调：

  * 可读性
  * 可维护性
  * 可扩展性
  * 自动化部署安全性

---

## 2. 核心能力需求（Functional Requirements）

### 2.1 基础键映射

#### 2.1.1 单键映射

* 支持 `A → B` 的基础 key_code 映射
* 支持 modifiers（optional / mandatory）

#### 2.1.2 Tap / Hold 行为

* `to_if_alone`
* `to_if_held_down`
* 常见用例：

  * `CapsLock → Esc / Hyper`
  * SpaceFN

---

### 2.2 Layer 系统

#### 2.2.1 单触发层（Hold Layer）

* 按住某个键进入 layer
* 释放后退出 layer
* 使用 Karabiner variable 机制实现

```python
LayerStackBuilder("hyper", "right_command")
```

#### 2.2.2 Layer 内映射

* layer 激活时，普通键具有新含义
* layer 外保持原行为

---

### 2.3 Layer Stacking（层叠加）

#### 2.3.1 多触发键组合进入新层

* 同时按住多个 layer key
* 进入一个全新的 mode

```python
LayerStackBuilder("hyper_alt", ["right_command", "right_option"])
```

#### 2.3.2 典型场景

* Hyper + Alt → Window / Tiling Mode
* Hyper + Ctrl → Dev / IDE Mode

---

### 2.4 Combo Mapping（同时键）

#### 2.4.1 功能描述

* 同时按下多个键触发映射
* 使用 Karabiner simultaneous 机制

```python
layer.map_combo(["j", "k"], "escape")
```

---

### 2.5 Sequence / Macro 系统

#### 2.5.1 多键序列（Sequence）

* 按顺序输入一组键，触发映射
* 使用 variable + delayed_action 实现

```python
layer.map_sequence(["g", "g"], "home")
```

#### 2.5.2 Sequence Timing Control

* 可配置 sequence 超时时间（ms）
* 防止误触

```python
layer.set_sequence_timeout(500)
```

---

### 2.6 Macro 系统（高级）

#### 2.6.1 多 key_code 宏

* 一个键触发多个 key_code

#### 2.6.2 Typed Text Macro（自动输入文本）

* 自动输入字符串
* 用于：

  * 代码模板
  * 常用短语
  * Commit message

```python
hyper.map_macro("t", template_type="typed_text", text="Hello, world!")
```

---

### 2.7 Template-Based Macro（核心抽象）

> 借鉴 **GokuRakuJoudo :templates**

#### 2.7.1 统一 Shell Command 模板系统

* 所有 shell_command 不内联
* 使用模板 + 参数填充

```python
MACRO_TEMPLATES = {
  "typed_text": "...",
  "alfred": "...",
  "keyboard_maestro": "...",
  "open": "..."
}
```

#### 2.7.2 支持模板类型

* typed_text
* Alfred workflow trigger
* Keyboard Maestro macro
* open / shell

---

### 2.8 Conditional Layers（条件层）

#### 2.8.1 App 条件

* 仅在特定 App 激活 layer / mapping

```python
layer.when_app(["com.apple.Terminal", "com.microsoft.VSCode"])
```

---

## 3. 配置生成与部署能力

### 3.1 JSON 构建

* 自动生成合法 Karabiner JSON
* 严格遵循 Karabiner schema

---

### 3.2 自动备份机制（安全性要求）

#### 3.2.1 功能

* 每次写入新配置前：

  * 自动备份旧 `karabiner.json`
  * 时间戳命名

#### 3.2.2 位置

```text
~/.config/karabiner/karabiner_backup_YYYYMMDD_HHMMSS.json
```

---

### 3.3 JSON 校验

* 写入后进行 JSON parse 校验
* 防止写入损坏配置

---

### 3.4 自动 Reload / Apply

#### 3.4.1 功能

* 保存后自动让 Karabiner 配置生效
* 无需用户手动打开 GUI

#### 3.4.2 实现方式

* `launchctl kickstart`
* 重启：

  * `org.pqrs.karabiner.karabiner_console_user_server`

```python
config.save(apply=True)
```

---

## 4. 非功能性需求（NFR）

### 4.1 可维护性

* DSL 语义清晰
* 模块化（Layer / Macro / Template / Deploy）

### 4.2 可扩展性

* 新模板无需修改核心逻辑
* 新 layer / mapping 类型可插拔

### 4.3 可测试性（未来）

* 纯 Python 构建
* 可对生成 JSON 做 snapshot testing

---

## 5. 项目边界（Out of Scope）

* 不替代 Karabiner-Elements 本体
* 不实现 GUI
* 不直接 hook 系统输入（完全依赖 Karabiner）

---

## 6. 项目愿景

> **把键盘映射，从“手工 JSON 配置”
> 提升为“可编程的人机接口设计语言”。**

KarabinerPyX 的终极目标是成为：

* macOS 高级用户
* 工程师
* 键盘重度使用者

的 **“键盘操作系统 DSL”**。
