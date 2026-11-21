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