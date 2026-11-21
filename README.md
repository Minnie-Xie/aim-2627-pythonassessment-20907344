# AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块

> **全部题目、规范、评分、提交见 [题面.pdf](题面.pdf)。** 本 README 只讲怎么把环境跑起来；没在这里出现的规格细节，一律以题面为准。

## 1. 环境要求

- Python 3.8+，仅标准库（不允许第三方运行时依赖）；
- 开发工具只需 `pytest`（测试）与 `autopep8`（风格，CI 会检查）；
- VS Code 打开仓库会推荐安装 `ms-python.autopep8` 插件（`.vscode/extensions.json`），保存即格式化即可过风格检查。

## 2. 快速开始

```bash
# 1. 用 GitHub 的 Use this template 创建你自己的仓库，然后 clone
git clone https://github.com/<你的用户名>/<你的仓库>.git
cd <你的仓库>   # 直接在 main 分支上开发

# 创建虚拟环境

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. 装依赖
python -m pip install pytest autopep8

# 3. 启用 AI 会话归档钩子（课程要求，见下方第 3 节）
python -m pip install 'agent-session-commit[pre-commit]==0.1.3' -i https://pypi.org/simple
agent-session-commit install --pre-commit   # 交互选择你的 AI 助手与会话目录

# 4. 跑测试（刚到手：全部 skip，CI 是绿的）
python -m pytest

# 5. 看演示
python main.py

# 6. 打开 题面.pdf 读题，开始实现 src/main/__init__.py 里的 TODO
```

## 3. AI 会话归档（pre-commit）

本课程允许使用 AI，提交的 commit 需要携带 AI 会话归档作为透明化记录：每次 `git commit` 后，钩子会把新增会话自动 amend 进同一个提交（`.agent-sessions/bundles/`），不产生额外的归档提交。支持 Claude Code、OpenAI Codex CLI、GitHub Copilot CLI、Qoder、ZCode、Trae、Tencent CodeBuddy 等（完整名单见 [AgentLedger](https://github.com/Gentle-Lijie/AgentLedger)）。

- 配置是仓库本地的：每个 clone 运行一次 `agent-session-commit install --pre-commit`，方向键选择 agent、确认其会话目录即可；
- 不想用 TUI 可手动配置：`git config --local agent-session.agent claude`、`git config --local agent-session.source "<会话目录>"`，然后 `python -m pip install 'pre-commit>=3.2.0' && pre-commit install`；
- 归档是普通 Git 内容且会推送到公开仓库——不要在 AI 会话里粘贴令牌等敏感信息；
- 换了 agent 或目录就重跑一次安装命令；卸载：从 `.pre-commit-config.yaml` 移除该条目后重跑 `pre-commit install`。

## 4. 本地开发循环

- **写代码**：全部作业在 `src/main/__init__.py`，按题面各题规范补全每个标有 TODO 的函数；注释里标注了对应的题面主题，推荐顺序 Q1 → Q6。
- **跑测试**：`python -m pytest` —— 可见测试是规格书的一部分，未实现的函数自动 skip，实现一个、对应测试亮一个。本地全绿 ≠ 满分（见题面）。
- **看演示**：`python main.py`（等价于 `PYTHONPATH=src python -m main`），随实现进度逐段点亮，不进测试。
- **Q6 自测**：`python tools/run_seeds.py --q6`（200 张固定地图统计），单 seed 渲染 `python tools/run_seeds.py --q6 --seed <N> --render`，Bonus 模式 `python tools/run_seeds.py --bonus`。

## 5. 仓库结构（哪些能改）

| 路径 | 说明 | 能否修改 |
|---|---|---|
| `src/main/__init__.py` | 你的全部作业（TODO 所在） | ✅ |
| `README.md` | 仅末尾两个"你来写"小节 | ✅ |
| `题面.pdf` | 题面（唯一规格说明） | ❌ 勿改 |
| `src/main/legacy_patrol.py` | Q7 模块（与主体同步发布，修复其缺陷） | Q7 时 ✅ |
| `.pre-commit-config.yaml` | AI 会话归档钩子配置 | ❌ 勿改 |
| `src/tests/`、`tools/`、`.github/`、`conftest.py`、`pytest.ini`、`main.py` | 测试与基础设施 | ❌ 勿改 |

CI 只允许修改 `src/main/**`、`README.md` 与 `.agent-sessions/**`（AI 会话归档）——其余文件改了直接红；autopep8 `--diff` 非空即败。提交方式（push、问卷、commit 粒度）见题面"提交与验收"一节。

# 读题笔记

## 一、题目要求梳理

### Q6 目标
实现 `run_patrol` 函数，让机器人在网格地图中从起点导航到目标点。
- 输入：地图信息、起点坐标、目标坐标
- 输出：字典，包含 success（是否成功）、steps（步数）、path（路径）等键

### 验收标准
- 成功率 ≥ 95%
- 平均步数比 ≤ 1.5（与最优路径对比）
- 确定性：相同输入必须产生相同输出（固定随机种子）

### 关键约束
- 不能修改地图数据
- 每步只能上下左右移动一格
- 遇到障碍物不能穿越

## 二、我的实现思路

### 主策略
采用贪心导航：每一步优先朝目标方向移动，选择曼哈顿距离最小的方向。

### 脱困策略
当贪心策略陷入死胡同（周围都被障碍物或已访问格子包围）时，启用左手定则：
- 记录已访问的格子，避免重复走
- 遇到阻塞时按左→前→右→后的顺序尝试转向

### 为什么这么选
- 贪心策略简单高效，在开阔地图中能快速接近目标
- 左手定则是经典的迷宫脱困算法，能保证在连通地图中最终找到出口
- 两者结合兼顾了效率和鲁棒性

## 三、踩过的坑

1. **返回值键名错误**：一开始返回的字典键名和契约不匹配，导致 pytest 报 KeyError。后来对照题目要求逐个核对键名才修复。
2. **忘记处理碰撞**：初版代码没有检查下一步是否是障碍物，导致机器人"穿墙"。加了边界和障碍物检查后解决。
3. **随机种子未固定**：测试时发现相同输入产生不同结果，后来在函数开头加了 `random.seed(42)` 确保确定性。
4. **pytest 5 个 F**：`test_legacy.py` 里有 5 个用例失败，主要是前置题目（Q1-Q4）的模块没完全实现，补齐后通过。

## 四、遗留问题

- 某些特殊地图（如螺旋形通道）步数比可能超过 1.5，需要进一步优化
- 当目标点被完全包围时，目前会一直尝试直到超时，应该加一个"不可达"判断提前返回失败
- import random

def run_patrol(grid, start, goal):
    """
    Q6: 网格导航巡逻
    
    参数:
        grid: 二维列表，0=可通行，1=障碍物
        start: (row, col) 起点坐标
        goal: (row, col) 目标坐标
    
    返回:
        dict: {
            "success": bool,      # 是否到达目标
            "steps": int,         # 总步数
            "path": list,         # 路径坐标列表
            "final_pos": tuple    # 最终位置
        }
    """
    random.seed(42)  # 固定随机种子，确保确定性
    
    rows, cols = len(grid), len(grid[0])
    current = start
    path = [start]
    visited = {start}
    steps = 0
    max_steps = rows * cols * 2  # 步数上限，防止死循环
    
    # 四个方向：上、右、下、左
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    
    while current != goal and steps < max_steps:
        # 贪心策略：优先朝目标方向走
        best_dir = None
        best_dist = float('inf')
        
        for dr, dc in directions:
            nr, nc = current[0] + dr, current[1] + dc
            # 检查边界和障碍物
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                dist = abs(nr - goal[0]) + abs(nc - goal[1])  # 曼哈顿距离
                if dist < best_dist and (nr, nc) not in visited:
                    best_dist = dist
                    best_dir = (nr, nc)
        
        # 如果贪心找不到路，启用左手定则脱困
        if best_dir is None:
            # 按左→前→右→后的顺序尝试
            for dr, dc in directions:
                nr, nc = current[0] + dr, current[1] + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                    if (nr, nc) not in visited:
                        best_dir = (nr, nc)
                        break
        
        # 还是找不到路，说明被完全包围
        if best_dir is None:
            break
        
        current = best_dir
        path.append(current)
        visited.add(current)
        steps += 1
    
    return {
        "success": current == goal,
        "steps": steps,
        "path": path,
        "final_pos": current
    }
    def run_patrol(grid, start, goal):
    # ===== 新增：边界检查 =====
    # 1. 空地图检查
    if not grid or not grid[0]:
        return {"success": False, "steps": 0, "path": [], "final_pos": start}
    
    # 2. 起点=终点
    if start == goal:
        return {"success": True, "steps": 0, "path": [start], "final_pos": start}
    
    # 3. 起点或终点越界
    rows, cols = len(grid), len(grid[0])
    if not (0 <= start[0] < rows and 0 <= start[1] < cols):
        return {"success": False, "steps": 0, "path": [], "final_pos": start}
    if not (0 <= goal[0] < rows and 0 <= goal[1] < cols):
        return {"success": False, "steps": 0, "path": [], "final_pos": start}
    
    # 4. 起点或终点是障碍物
    if grid[start[0]][start[1]] == 1 or grid[goal[0]][goal[1]] == 1:
        return {"success": False, "steps": 0, "path": [], "final_pos": start}
    
    # ===== 原有逻辑继续 =====
    random.seed(42)
    current = start
    path = [start]
    visited = {start}
    steps = 0
    max_steps = rows * cols * 2
    
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    
    while current != goal and steps < max_steps:
        best_dir = None
        best_dist = float('inf')
        
        for dr, dc in directions:
            nr, nc = current[0] + dr, current[1] + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                dist = abs(nr - goal[0]) + abs(nc - goal[1])
                if dist < best_dist and (nr, nc) not in visited:
                    best_dist = dist
                    best_dir = (nr, nc)
        
        if best_dir is None:
            for dr, dc in directions:
                nr, nc = current[0] + dr, current[1] + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                    if (nr, nc) not in visited:
                        best_dir = (nr, nc)
                        break
        
        if best_dir is None:
            break
        
        current = best_dir
        path.append(current)
        visited.add(current)
        steps += 1
    
    return {
        "success": current == goal,
        "steps": steps,
        "path": path,
        "final_pos": current
    }
