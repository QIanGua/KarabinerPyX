# KarabinerPyX 开发任务管理
# 使用 uv 作为包管理器

# 默认任务：显示帮助
default:
    @just --list

# 初始化开发环境
init:
    uv sync --all-extras

# 安装依赖
install:
    uv sync

# 安装开发依赖
install-dev:
    uv sync --extra dev

# 运行测试
test:
    uv run pytest tests/ -v

# 运行测试并显示覆盖率
test-cov:
    uv run pytest tests/ -v --cov=src/karabinerpyx --cov-report=term-missing

# 运行示例
example:
    uv run python examples/demo.py

# 构建包
build:
    uv build

# 清理
clean:
    rm -rf dist/ build/ *.egg-info src/*.egg-info .pytest_cache .coverage
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# 格式化代码（如果安装了 ruff）
fmt:
    uv run ruff format src/ tests/ || echo "ruff not installed"

# 检查代码（如果安装了 ruff）
lint:
    uv run ruff check src/ tests/ || echo "ruff not installed"
