# -*- coding: utf-8 -*-
"""AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块（学生骨架）。

你的全部作业都在本文件里：按题面（题面.pdf）各题的规范补全每个标有 TODO 的函数。
- 骨架已提供：Facing / SentryState 枚举、SentryGrid 的构造与只读属性、
  渲染函数 render_frame（demo 用，不进测试）。
- 你要实现：Q1-Q6 与 Bonus 的全部 TODO，以及 SentryGrid 的
  四个方法（current_pos 的 setter、move_forward、turn_left、turn_right）。
- 未实现的函数 raise NotImplementedError：可见测试会自动 skip，
  CI 一开始就是绿的；实现一个，对应测试亮一个。
- `python main.py`（或 PYTHONPATH=src python -m main）可看 ASCII 演示。
"""
import json
from enum import Enum


# ---------------------------------------------------------------------------
# 仿真世界基础（已提供，勿改）
# ---------------------------------------------------------------------------
class Facing(Enum):
    """朝向枚举。世界坐标 (x, y)：x 向右增长，y 向上增长（数学系）。"""

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        """该朝向的单位位移向量 (dx, dy)。"""
        return self.value[0], self.value[1]


# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def hp_ratio(hp, max_hp):
    if type(hp) is int and type(max_hp) is int:
        percent_hp = (hp / max_hp) * 100
        return int(percent_hp)
    else:
        raise TypeError("hp 和 max_hp 必须是 int 类型")


def status_report(name, robot_type, hp, max_hp, battery):
    percent_hp = hp_ratio(hp, max_hp)
    battery_count = battery
    if battery_count < 0:
        raise ValueError("battery 不能小于 0")
    elif battery_count < 20:
        status_robot = "LOW"
    elif battery_count < 60:
        status_robot = "WARNING"
    elif battery_count <= 100:
        status_robot = "OK"
    else:
        raise ValueError("battery_count 不能大于 100")
    return f"{name:<10}|{robot_type:^10}|HP {percent_hp:>3}%|BAT {battery_count:>3}%|{status_robot}"
    """TODO(Q1)：一行自检报告字符串；档位判定与逐字符格式见题面 Q1 规范。"""


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
# ---------------------------------------------------------------------------
def analyze_damage_log(lines):
    """解析混合格式伤害日志，返回固定契约的统计 dict。"""
    total = 0
    by_armor = {"front": 0, "left": 0, "right": 0}
    seen_ids = set()
    event_count = 0

    for line in lines:
        try:
            stripped = line.strip()

            # 空行 / # 注释 → 脏行跳过
            if stripped == "" or stripped.startswith("#"):
                continue

            # 以 { 开头 → JSON 行
            if stripped.startswith("{"):
                loaded = json.loads(stripped)
                if not isinstance(loaded, dict):
                    continue

                # 必需字段
                if "armor" not in loaded or "damage" not in loaded:
                    continue

                armor = loaded["armor"]
                damage = loaded["damage"]

                # armor 值域：三者之一
                if armor not in ("front", "left", "right"):
                    continue
                # damage 必须是严格正整数（排除 bool / 浮点 / 负数 / 零）
                if type(damage) is not int or damage <= 0:
                    continue

                # 带 id 的去重
                rid = loaded.get("id")
                if rid is not None:
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)

                # 累加
                total += damage
                by_armor[armor] += damage
                event_count += 1

            else:
                # 否则按传感器行处理：字母:正整数，逗号分隔
                events = []
                for seg in stripped.split(","):
                    seg = seg.strip()
                    if ":" not in seg:
                        raise ValueError("段格式非法")
                    key, _, val = seg.partition(":")
                    key = key.strip()
                    val = val.strip()
                    if key not in ("F", "L", "R"):
                        raise ValueError("部位字母非法")
                    if not val.isdigit():
                        raise ValueError("数值非正整数")
                    num = int(val)
                    if num <= 0:
                        raise ValueError("数值非正整数")
                    events.append((key, num))

                if not events:
                    continue

                mapping = {"F": "front", "L": "left", "R": "right"}
                for key, dmg in events:
                    armor = mapping[key]
                    total += dmg
                    by_armor[armor] += dmg
                    event_count += 1

        except Exception:
            # 任何异常 → 脏行跳过，绝不向外抛
            continue

    # 派生统计
    most_hit = None
    if event_count > 0:
        most_hit = max(("front", "left", "right"), key=lambda k: by_armor[k])
    avg = total / event_count if event_count > 0 else 0.0

    return {
        "total": total,
        "by_armor": by_armor,
        "most_hit": most_hit,
        "avg": avg,
    }


# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------
class SentryGrid:
    """哨兵仿真载体（构造与只读属性已提供；四个 TODO 方法由你实现）。"""

    def __init__(self, width, height, obstacles, enemy_pos,
                 start_pos=(0, 0), facing=Facing.UP, fuel=100):
        self._width = int(width)
        self._height = int(height)
        if self._width <= 0 or self._height <= 0:
            raise ValueError("地图尺寸必须为正")
        # 障碍坐标存入 set，查询 O(1)——已有实现，勿改。
        self._obstacles = set()
        for ob in obstacles:
            x, y = ob
            self._obstacles.add((int(x), int(y)))
        if not isinstance(enemy_pos, (tuple, list)) or len(enemy_pos) != 2:
            raise TypeError("enemy_pos 需要长度为 2 的 tuple/list")
        self._enemy_pos = self._clamp_cell(enemy_pos)
        if self._enemy_pos in self._obstacles:
            raise ValueError("enemy_pos 不能位于障碍物上")
        if not isinstance(facing, Facing):
            facing = Facing.UP
        self._facing = facing
        self._fuel = int(fuel)
        self._collision_count = 0
        self.current_pos = start_pos

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    # -- 只读属性（已提供，勿改） ------------------------------------------
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def enemy_pos(self):
        return self._enemy_pos

    @property
    def facing(self):
        return self._facing

    @property
    def fuel(self):
        return self._fuel

    @property
    def collision_count(self):
        return self._collision_count

    @property
    def obstacles(self):
        """障碍集合的只读视图（内部 set 引用，不要修改它）。"""
        return self._obstacles

    @property
    def found_enemy(self):
        return self._pos == self._enemy_pos

    def is_blocked(self, x, y):
        """已提供：坐标是否为障碍或越界（O(1)）。"""
        return ((x, y) in self._obstacles
                or not (0 <= x < self._width and 0 <= y < self._height))

    # -- 你要实现的部分 ------------------------------------------------------
    @property
    def current_pos(self):
        """当前位置 (x, y) 的 tuple。"""
        return self._pos

    @current_pos.setter
    def current_pos(self, value):
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise TypeError("current_pos 需要长度为 2 的 tuple/list")
        try:
            new_pos = self._clamp_cell(value)
        except (TypeError, ValueError) as e:
            raise TypeError("current_pos 元素必须可转为 int") from e
        if new_pos in self._obstacles:
            raise ValueError("current_pos 不能位于障碍物上")
        self._pos = new_pos

    def move_forward(self):
        if self._fuel <= 0:
            return self._pos
        self._fuel -= 1
        dx, dy = self._facing.delta
        nx = self._pos[0] + dx
        ny = self._pos[1] + dy
        if self.is_blocked(nx, ny):
            self._collision_count += 1
            return self._pos
        try:
            self.current_pos = (nx, ny)
        except (TypeError, ValueError):
            pass
        return self._pos

    def turn_left(self):
        LEFT_ROT = {Facing.UP: Facing.LEFT, Facing.LEFT: Facing.DOWN,
                    Facing.DOWN: Facing.RIGHT, Facing.RIGHT: Facing.UP}
        self._facing = LEFT_ROT[self._facing]
        return self._facing

    def turn_right(self):
        RIGHT_ROT = {Facing.UP: Facing.RIGHT, Facing.RIGHT: Facing.DOWN,
                     Facing.DOWN: Facing.LEFT, Facing.LEFT: Facing.UP}
        self._facing = RIGHT_ROT[self._facing]
        return self._facing


# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
DELTA = {
    Facing.UP: (0, 1),
    Facing.DOWN: (0, -1),
    Facing.LEFT: (-1, 0),
    Facing.RIGHT: (1, 0),
}

AXIS_OF = {
    Facing.UP: "y", Facing.DOWN: "y",
    Facing.LEFT: "x", Facing.RIGHT: "x",
}


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    obs = {tuple(p) for p in obstacles}
    d0 = _manhattan(pos, target)
    candidates = []
    for f in (Facing.UP, Facing.RIGHT, Facing.DOWN, Facing.LEFT):
        dx, dy = DELTA[f]
        nxt = (pos[0] + dx, pos[1] + dy)
        if nxt not in obs and _manhattan(nxt, target) < d0:
            candidates.append(f)
    if not candidates:
        return current_facing
    if len(candidates) == 1:
        return candidates[0]
    dx = abs(target[0] - pos[0])
    dy = abs(target[1] - pos[1])
    primary_axis = "x" if dx > dy else "y"
    filtered = [f for f in candidates if AXIS_OF[f] == primary_axis]
    if filtered:
        return filtered[0]
    return candidates[0]


# ---------------------------------------------------------------------------
# Q5 哨兵决策机（题面 Q5·裁判系统决策规则表）
# ---------------------------------------------------------------------------
class SentryState(Enum):
    """哨兵状态机（已提供，勿改）。"""

    PATROL = "PATROL"
    SUSPECT = "SUSPECT"
    ENGAGE = "ENGAGE"
    RETREAT = "RETREAT"
    RETURN = "RETURN"


def decide(sensor, state, hp, heat):
    if not isinstance(sensor, dict):
        raise ValueError("sensor 必须是 dict")
    required = ("enemy_frames", "enemy_dist", "robot_type", "max_hp")
    for k in required:
        if k not in sensor:
            raise ValueError(f"sensor 缺字段 {k}")

    frames = sensor["enemy_frames"]
    if not isinstance(frames, (tuple, list)):
        raise ValueError("enemy_frames 必须是 tuple 或 list")
    if not (1 <= len(frames) <= 6):
        raise ValueError("enemy_frames 长度必须在 1~6 之间")

    if not isinstance(state, SentryState):
        raise ValueError("state 必须是 SentryState 成员")

    def _is_real_num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    if not _is_real_num(hp):
        raise ValueError("hp 必须是数值（非 bool）")
    if not _is_real_num(heat):
        raise ValueError("heat 必须是数值（非 bool）")

    frames = tuple(bool(x) for x in frames)

    enemy_dist = sensor["enemy_dist"]
    if enemy_dist is None:
        pass
    elif isinstance(enemy_dist, int) and not isinstance(enemy_dist, bool):
        pass
    else:
        enemy_dist = None

    robot_type = sensor["robot_type"]
    if isinstance(robot_type, str):
        rtype_upper = robot_type.strip().upper()
        if rtype_upper == "HERO":
            robot_type = "HERO"
        else:
            robot_type = "INFANTRY"
    else:
        robot_type = "INFANTRY"

    max_hp_val = sensor["max_hp"]
    if (isinstance(max_hp_val, int)
            and not isinstance(max_hp_val, bool)
            and max_hp_val > 0):
        pass
    else:
        max_hp_val = 1

    hp = int(hp)
    if hp < 0:
        hp = 0
    elif hp > max_hp_val:
        hp = max_hp_val

    heat = int(heat) if _is_real_num(heat) else 0

    hp_pct = int(hp * 100 / max_hp_val)
    visible = frames[-1]
    dist = enemy_dist
    rtype = robot_type

    # R1：残血撤退（优先级最高）
    if hp_pct <= 30:
        return ("RETREAT", SentryState.RETREAT)

    # R2：撤退保持
    if state == SentryState.RETREAT:
        if hp_pct >= 60:
            return ("RETURN", SentryState.RETURN)
        return ("RETREAT", SentryState.RETREAT)

    # R3：返航单帧过渡
    if state == SentryState.RETURN:
        return ("MOVE_BASE", SentryState.PATROL)

    # R4：交火可见
    if state == SentryState.ENGAGE and visible:
        if dist is not None and dist <= 3:
            return ("SHOOT", SentryState.ENGAGE)
        if rtype == "HERO":
            return ("MOVE_RIGHT", SentryState.ENGAGE)
        return ("MOVE_LEFT", SentryState.ENGAGE)

    # R5：交火不可见
    if state == SentryState.ENGAGE and not visible:
        if len(frames) >= 2 and frames[-2]:
            return ("HOLD_FIRE", SentryState.ENGAGE)
        return ("SCAN", SentryState.SUSPECT)

    # R6：敌情确认
    if state in (SentryState.PATROL, SentryState.SUSPECT) and visible:
        if len(frames) >= 2 and frames[-1] and frames[-2]:
            if dist is not None and dist <= 3:
                return ("SHOOT", SentryState.ENGAGE)
            if rtype == "HERO":
                return ("MOVE_RIGHT", SentryState.ENGAGE)
            return ("MOVE_LEFT", SentryState.ENGAGE)
        return ("SCAN", SentryState.SUSPECT)

    # R7：默认
    if state == SentryState.PATROL:
        return ("PATROL_MOVE", SentryState.PATROL)
    if state == SentryState.SUSPECT:
        return ("SCAN", SentryState.SUSPECT)


# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------
def _align_facing(grid, target):
    """原地旋转直到 facing == target（不耗 fuel）。"""
    while grid.facing != target:
        grid.turn_right()


def _escape_direction(grid):
    """脱困策略：优先左转 → 直行 → 右转 → 掉头。"""
    LEFT_FIRST_ORDER = (Facing.LEFT, Facing.UP, Facing.RIGHT, Facing.DOWN)
    obstacles = grid.obstacles
    for f in LEFT_FIRST_ORDER:
        dx, dy = DELTA[f]
        nxt = (grid.current_pos[0] + dx, grid.current_pos[1] + dy)
        if nxt not in obstacles:
            return f
    return grid.facing


def run_patrol(grid, max_steps=500):
    steps = 0
    collisions = 0
    visited = {grid.current_pos}
    last_dist = _manhattan(grid.current_pos, grid.enemy_pos)
    stall_count = 0
    recent_trajectory = [grid.current_pos]

    while True:
        if grid.current_pos == grid.enemy_pos:
            break
        if steps >= max_steps:
            break
        if grid.fuel <= 0:
            break

        cur_dist = _manhattan(grid.current_pos, grid.enemy_pos)

        if cur_dist >= last_dist and stall_count < 100:
            stall_count += 1
        else:
            stall_count = max(0, stall_count - 1)
        last_dist = cur_dist

        if stall_count > 4:
            next_dir = _escape_direction(grid)
        else:
            next_dir = next_step_toward(
                grid.current_pos, grid.enemy_pos,
                grid.obstacles, grid.facing,
            )

        _align_facing(grid, next_dir)

        old_pos = grid.current_pos
        grid.move_forward()
        new_pos = grid.current_pos

        if new_pos == old_pos:
            collisions += 1

        steps += 1
        visited.add(new_pos)
        recent_trajectory.append(new_pos)
        if len(recent_trajectory) > 10:
            recent_trajectory.pop(0)

    success = grid.current_pos == grid.enemy_pos
    return {
        "steps": steps,
        "collisions": collisions,
        "visited_count": len(visited),
        "found_enemy": success,
        "success": success,
    }


def report_to_json(stats):
    return json.dumps(stats, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------
def bfs_path_length(start, target, obstacles):
    if start == target:
        return 0
    obs = {tuple(p) for p in obstacles}
    from collections import deque
    q = deque()
    q.append((tuple(start), 0))
    visited = {tuple(start)}
    NEIGHBORS = [(0, 1), (0, -1), (-1, 0), (1, 0)]
    while q:
        cur, dist = q.popleft()
        for dx, dy in NEIGHBORS:
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in visited or nxt in obs:
                continue
            if nxt == tuple(target):
                return dist + 1
            visited.add(nxt)
            q.append((nxt, dist + 1))
    return -1


# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    for y in range(grid.height - 1, -1, -1):
        row = []
        for x in range(grid.width):
            if (x, y) == grid.current_pos:
                row.append("◉")
            elif (x, y) == grid.enemy_pos:
                row.append("▲")
            elif (x, y) in grid.obstacles:
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        rows.append("".join(row))
    return rows
