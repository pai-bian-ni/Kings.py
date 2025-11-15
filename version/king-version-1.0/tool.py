import pygame
import math
from collections import deque

# 颜色
GREEN = (0, 255, 0)
RED   = (255, 0, 0)
BLUE  = (0, 120, 255)
WHITE = (255, 255, 255)
GRAY  = (100, 100, 100)
DARK  = (20, 20, 20)
CYAN  = (70, 220, 220)
YELLOW = (255, 255, 0)
OVERLAY_ALPHA = 80

# 国王城坐标（行,列）
green_king_pos = [0, 10]
red_king_pos   = [19, 10]

player_upgrades = {
    0: {"hp": 0, "hurt": 0, "speed": 0},  # 绿色
    1: {"hp": 0, "hurt": 0, "speed": 0},  # 红色
}
import json, os

# 加载 DLC 配置
UNIT_CONFIG = {
    "soldier":   {"speed": 1, "damage": 10, "hp": 20, "cost": 300, "color":{"r":255, "g":30, "b":30}},
    "knight":    {"speed": 2, "damage": 5,  "hp": 40, "cost": 200},
    "paratrooper": {"speed": 1, "damage": 15, "hp": 15, "cost": 200},
    "cannon":    {"speed": 0, "damage": 5,  "hp": 100, "cost": 700},  # cost要写上
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Kings.py 所在目录
dlc_file = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "DLC", "new_units.json"))

print("加载 DLC 文件:", dlc_file)

if os.path.exists(dlc_file):
    print("发现 DLC")
    with open(dlc_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        UNIT_CONFIG.update(data)
else:
    print("DLC 文件未找到")





if os.path.exists(dlc_file):
    print("discover")
    with open(dlc_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        UNIT_CONFIG.update(data)

def unit_stats(ut, owner=None, player_upgrades=None):
    base = UNIT_CONFIG.get(ut, {"speed":1,"damage":5,"hp":20})
    speed, damage, hp = base["speed"], base["damage"], base["hp"]

    if owner is not None and player_upgrades is not None:
        if ut != "cannon":
            speed += player_upgrades[owner]["speed"]
        damage += player_upgrades[owner]["hurt"]
        hp += player_upgrades[owner]["hp"]

    return speed, damage, hp

def get_cell_from_mouse(pos, screen):
    """根据鼠标坐标返回棋盘格子 (row, col)，超出棋盘返回 None"""
    sw, sh = screen.get_size()
    board_x, board_y, cell_size, board_size = get_board_geometry(screen)
    mx, my = pos
    if board_x <= mx < board_x + board_size and board_y <= my < board_y + board_size:
        col = int((mx - board_x) // cell_size)
        row = int((my - board_y) // cell_size)
        return (row, col)
    return None


def log_event(message):
    with open("game.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")



# === 几何与UI工具 ===
def get_board_geometry(screen):
    sw, sh = screen.get_size()
    board_size = min(sw, sh) * 0.8
    cell_size = board_size / 20
    board_x = (sw - board_size) / 2
    board_y = (sh - board_size) / 2
    return board_x, board_y, cell_size, board_size

def pos_to_cell(screen, pos):
    board_x, board_y, cell_size, board_size = get_board_geometry(screen)
    x, y = pos
    if x < board_x or y < board_y or x >= board_x + board_size or y >= board_y + board_size:
        return None
    col = int((x - board_x) // cell_size)
    row = int((y - board_y) // cell_size)
    if 0 <= row < 20 and 0 <= col < 20:
        return (row, col)
    return None

def get_city_menu_buttons(screen, city):
    board_x, board_y, cell_size, board_size = get_board_geometry(screen)
    city_row, city_col, _, _, _ = city

    # 菜单基础位置（默认显示在城市下方）
    menu_x = board_x + city_col * cell_size - 160
    menu_y = board_y + city_row * cell_size

    # 菜单高度
    menu_height = 40 * len(UNIT_CONFIG)
    menu_width = 150

    # 检查是否超出棋盘底部
    if menu_y + menu_height > board_y + board_size:
        # 如果超出，往上移动
        menu_y = menu_y - menu_height

    rect_bg = pygame.Rect(menu_x, menu_y, menu_width, menu_height)

    # 生成按钮
    buttons = {}
    for i, unit_type in enumerate(UNIT_CONFIG.keys()):
        buttons[unit_type] = pygame.Rect(menu_x + 10, menu_y + 10 + 40 * i, 140, 30)

    return rect_bg, buttons







# === 绘制 ===
def draw_map(screen, soldiers, cities, current_player, turn_count, selected_city, floating_texts):
    sw, sh = screen.get_size()
    board_x, board_y, cell_size, board_size = get_board_geometry(screen)
    overlay = pygame.Surface((int(cell_size), int(cell_size)), pygame.SRCALPHA)
    screen.fill((25, 25, 30))

    # 棋盘+河流+城市
    for row in range(20):
        for col in range(20):
            x = board_x + col * cell_size
            y = board_y + row * cell_size
            color = None
            if [row, col] == green_king_pos:
                color = GREEN
            elif [row, col] == red_king_pos:
                color = RED
            else:
                # 城市
                found_city = None
                for c in cities:
                    if c[0] == row and c[1] == col:
                        found_city = c
                        break
                if found_city:
                    city_owner = found_city[2]
                    pygame.draw.rect(screen, YELLOW, (x, y, cell_size, cell_size))
                    border_color = GREEN if city_owner == 0 else RED
                    pygame.draw.rect(screen, border_color, (x, y, cell_size, cell_size), max(1, int(cell_size*0.08)))
                else:
                    # 河流
                    if row in (9, 10):
                        if col not in (4, 14):
                            color = CYAN
                        else:
                            color = DARK if (row + col) % 2 == 0 else GRAY
                    else:
                        color = DARK if (row + col) % 2 == 0 else GRAY
            if color:
                pygame.draw.rect(screen, color, (x, y, cell_size, cell_size))

    # 城市影响范围（半透明覆盖：普通半径3，王城半径5）
    for city in cities:
        city_row = city[0]
        city_col = city[1]
        city_owner = city[2]
        city_hp = city[3]
        radius = 5 if [city_row, city_col] in (green_king_pos, red_king_pos) else 3
        color = GREEN if city_owner == 0 else RED
        for r in range(max(0, city_row - radius), min(20, city_row + radius + 1)):
            for c in range(max(0, city_col - radius), min(20, city_col + radius + 1)):
                dist = math.sqrt((r - city_row) ** 2 + (c - city_col) ** 2)
                if dist <= radius:
                    x = board_x + c * cell_size
                    y = board_y + r * cell_size
                    overlay.fill(color + (OVERLAY_ALPHA,))
                    screen.blit(overlay, (x, y))

    # 绘制城市HP
    for city in cities:
        city_row = city[0]
        city_col = city[1]
        city_owner = city[2]
        city_hp = city[3]
        x = board_x + city_col * cell_size
        y = board_y + city_row * cell_size
        # HP文本
        font = pygame.font.SysFont(None, int(cell_size/3))
        max_hp = 300 if [city_row, city_col] in (green_king_pos, red_king_pos) else 100
        txt = font.render(str(city_hp), True, WHITE)
        screen.blit(txt, (x + cell_size/2 - txt.get_width()/2, y + cell_size/2 - txt.get_height()/2))
        # 统一长度血条（固定40像素）
        BAR_WIDTH = 40
        BAR_HEIGHT = 6
        max_hp = 300 if [city_row, city_col] in (green_king_pos, red_king_pos) else 100
        bar_x = x + cell_size/2 - BAR_WIDTH/2
        bar_y = y - 8
        if city_owner == 0:  # Green
            bar_y = y - 8  # 上方
        else:  # Red
            bar_y = y + cell_size + 2  # 下方

        pygame.draw.rect(screen, RED, (x, bar_y, cell_size, 5))
        pygame.draw.rect(screen, GREEN, (x, bar_y, int(cell_size * (city_hp / max_hp)), 5))

    # HUD：回合玩家
    font_big = pygame.font.SysFont(None, 36)
    player_text = "Green" if current_player == 0 else "Red"
    hud = font_big.render(f"Turn {turn_count}  |  {player_text} Player", True, WHITE)
    screen.blit(hud, (10, 10))

    # 士兵
    draw_soldiers(screen, soldiers)

    # 选中城市信息 + 菜单
    if selected_city:
        draw_city_panel_and_menu(screen, selected_city, cities)
        owner = selected_city[2]
        hp = selected_city[3]
        level = selected_city[4]
        btn_rect = pygame.Rect(screen.get_width() - 150, 150, 120, 40)
        pygame.draw.rect(screen, (100, 100, 180), btn_rect)
        font_small = pygame.font.SysFont(None, 24)
        font_mid = pygame.font.SysFont(None, 28)
        txt = font_small.render(f"Level: {level}", True, (255, 255, 255))
        screen.blit(txt, (btn_rect.x + 10, btn_rect.y + 10))

    # 飘字（本回合）
    draw_floating_texts(screen, floating_texts)


def draw_city_panel_and_menu(screen, selected_city, cities):
    """绘制城市信息面板 + 动态兵种菜单"""
    font = pygame.font.SysFont(None, 24)
    rect_bg, buttons = get_city_menu_buttons(screen, selected_city)

    pygame.draw.rect(screen, (50, 50, 60), rect_bg)  # 底框

    for unit_type, rect in buttons.items():
        # 默认颜色
        btn_color = (80, 140, 220)
        uconf = UNIT_CONFIG.get(unit_type, {})
        if "color" in uconf:
            col = uconf["color"]
            btn_color = (col.get("r", 80), col.get("g", 140), col.get("b", 220))

        pygame.draw.rect(screen, btn_color, rect)
        cost = uconf.get("cost", 100)
        txt = font.render(f"{unit_type} ({cost})", True, WHITE)
        screen.blit(txt, (rect.x + 5, rect.y + 5))

    return rect_bg, buttons






def draw_soldiers(screen, soldiers):
    board_x, board_y, cell_size, _ = get_board_geometry(screen)

    for s in soldiers:
        row, col, owner, hp, tr, tc, unit_type = s
        x = board_x + col * cell_size
        y = board_y + row * cell_size
        cx, cy = x + cell_size/2, y + cell_size/2
        size = cell_size * 0.32
        border = GREEN if owner == 0 else RED

        # 形状：soldier=三角形，knight=方形，paratrooper=圆
        if unit_type == "soldier":
            pts = [(cx, cy - size), (cx - size, cy + size), (cx + size, cy + size)]
            pygame.draw.polygon(screen, BLUE, pts)
            pygame.draw.polygon(screen, border, pts, 2)
            max_hp = 20
        elif unit_type == "knight":
            rect = pygame.Rect(cx - size, cy - size, size*2, size*2)
            pygame.draw.rect(screen, (60, 60, 255), rect)
            pygame.draw.rect(screen, border, rect, 2)
            max_hp = 40
        else:  # paratrooper
            pygame.draw.circle(screen, (100, 200, 255), (int(cx), int(cy)), int(size))
            pygame.draw.circle(screen, border, (int(cx), int(cy)), int(size), 2)
            max_hp = 15

        # 血条（上方）
        # 固定血条宽度，比如 40px
        BAR_WIDTH = 40
        BAR_HEIGHT = 5

        # 背景


        # 前景（根据比例填充）
        if owner == 0:  # Green
            bar_y = y - 8  # 上方
        else:  # Red
            bar_y = y + cell_size + 2  # 下方

        pygame.draw.rect(screen, RED, (x, bar_y, cell_size, 5))
        pygame.draw.rect(screen, GREEN, (x, bar_y, int(cell_size * (hp / max_hp)), 5))


def draw_floating_texts(screen, floating_texts):
    if not floating_texts:
        return
    board_x, board_y, cell_size, _ = get_board_geometry(screen)
    font = pygame.font.SysFont(None, int(cell_size/2))
    for (row, col, text, color) in floating_texts:
        x = board_x + col * cell_size + cell_size/2
        y = board_y + row * cell_size + cell_size/2 - cell_size*0.3
        img = font.render(text, True, color)
        screen.blit(img, (x - img.get_width()/2, y - img.get_height()/2))


# === 路径&逻辑 ===
def is_river_cell(row, col):
    return (row in (9, 10)) and (col not in (4, 14))

def get_valid_moves_avoiding_river(row, col):
    moves = []
    for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 20 and 0 <= nc < 20 and not is_river_cell(nr, nc):
            moves.append((nr, nc))
    return moves

def find_path(start, goal):
    if start == goal:
        return [start]
    q = deque([(start, [start])])
    visited = {start}
    while q:
        (r, c), path = q.popleft()
        for nr, nc in get_valid_moves_avoiding_river(r, c):
            if (nr, nc) in visited:
                continue
            visited.add((nr, nc))
            npath = path + [(nr, nc)]
            if (nr, nc) == goal:
                return npath
            q.append(((nr, nc), npath))
    return None

def find_nearest_target(row, col, owner, cities):
    # 最近的敌方城市
    best = None
    best_d = 10**9
    for city in cities:
        cr = city[0]
        cc = city[1]
        cown = city[2]
        if cown == owner:
            continue
        d = abs(row - cr) + abs(col - cc)
        if d < best_d:
            best_d = d
            best = (cr, cc)
    return best if best else (row, col)

def city_zone_radius(city):
    row = city[0]
    col = city[1]
    owner = city[2]
    if [row, col] == green_king_pos or [row, col] == red_king_pos:
        return 5
    return 3

# === 兵种创建 ===
def create_unit(unit_type, row, col, owner, cities):
    tr, tc = find_nearest_target(row, col, owner, cities)
    hp = UNIT_CONFIG.get(unit_type, {"hp":20})["hp"]
    return (row, col, owner, hp, tr, tc, unit_type)


# === 战斗与回合推进 ===





def step_towards(row, col, target_row, target_col):
    path = find_path((row, col), (target_row, target_col))
    if path and len(path) > 1:
        return path[1]
    return (row, col)

def retarget_if_proximity(row, col, owner, soldiers, cities, tr, tc):
    """当接近敌方单位或城市时，动态重定向"""
    # 检查敌方城市
    for city in cities:
        city_row = city[0]
        city_col = city[1]
        city_owner = city[2]
        if city_owner != owner:
            if abs(city_row - row) <= 5 and abs(city_col - col) <= 5:
                return city_row, city_col

    # 检查敌方士兵
    for s in soldiers:
        sr = s[0]
        sc = s[1]
        sown = s[2]
        if sown != owner:
            if abs(sr - row) <= 5 and abs(sc - col) <= 5:
                return sr, sc

    return tr, tc


def soldier_attack_phase(idx, soldiers, cities, floating_texts):
    """士兵攻击：每个士兵每回合一次；同格先打城市，否则打一名敌军"""
    row = soldiers[idx][0]
    col = soldiers[idx][1]
    owner = soldiers[idx][2]
    hp = soldiers[idx][3]
    ut = soldiers[idx][6]
    tr, tc = soldiers[idx][4], soldiers[idx][5]
    speed, damage, _maxhp = unit_stats(ut)

    # 打城市
    for ci, city in enumerate(cities):
        city_row = city[0]
        city_col = city[1]
        city_owner = city[2]
        city_hp = city[3]
        city_level = city[4]

        if city_owner == owner:
            continue
        if city_row == row and city_col == col:
            city_hp -= damage
            cities[ci] = (city_row, city_col, city_owner, city_hp, city_level)
            floating_texts.append((row, col, f"-{damage}", (255, 100, 100)))
            return

    # 打敌军（一名）
    for j, other in enumerate(soldiers):
        if j == idx:
            continue
        orow, ocol, oown, ohp, otr, otc, out = other
        if oown == owner:
            continue
        if orow == row and ocol == col:
            ohp -= damage
            soldiers[j] = (orow, ocol, oown, ohp, otr, otc, out)
            floating_texts.append((row, col, f"-{damage}", (255, 120, 120)))
            return

def city_attack_phase(soldiers, cities, floating_texts):
    if not soldiers or not cities:
        return soldiers
    updated = list(soldiers)
    for city in cities:
        city_row = city[0]
        city_col = city[1]
        city_owner = city[2]
        city_hp = city[3]
        city_level = city[4]

        radius = city_zone_radius((city_row, city_col, city_owner, city_hp))
        candidates = []
        for i, s in enumerate(updated):
            sr, sc, sown, shp, tr, tc, ut = s
            if sown == city_owner:
                continue
            dist = math.dist((sr, sc), (city_row, city_col))
            if dist <= radius:
                candidates.append((i, dist))
        if candidates:
            i, _ = min(candidates, key=lambda x: x[1])
            sr, sc, sown, shp, tr, tc, ut = updated[i]
            damage = 3 + (city_level - 1) * 3
            shp -= damage
            updated[i] = (sr, sc, sown, shp, tr, tc, ut)
            floating_texts.append((sr, sc, f"-{damage}", (255, 180, 180)))
    updated = [s for s in updated if s[3] > 0]
    return updated


def move_soldiers(soldiers, cities, floating_texts, player_upgrades):
    """推进一回合：移动 → 单位攻击 → 城市攻击 → 清理死亡"""
    units = list(soldiers)
    city_list = list(cities)

    # 逐个单位处理
    for i in range(len(units)):
        row, col, owner, hp, tr, tc, ut = units[i]
        speed, damage, _maxhp = unit_stats(ut, owner, player_upgrades)

        # ========== 大炮特殊逻辑 ==========
        if ut == "cannon":
            # 每回合自动掉血
            hp -= 10
            if hp <= 0:
                floating_texts.append((row, col, "-100 (Cannon destroyed)", (255, 0, 0)))
                log_event(f"Player {owner} cannon at ({row},{col}) destroyed by decay")
                units[i] = (row, col, owner, 0, tr, tc, ut)
                continue

            # 搜索攻击目标
            target_city = None
            target_unit = None

            # 1. 优先敌方城市
            for ci, city in enumerate(city_list):
                cr = city[0]
                cc = city[1]
                cown = city[2]
                chp = city[3]
                if cown != owner and chp > 0:
                    dist = math.dist((row, col), (cr, cc))
                    if dist <= 7:
                        target_city = (ci, city)
                        break

            # 2. 否则找敌方单位
            if not target_city:
                for j, other in enumerate(units):
                    if j == i:
                        continue
                    orow, ocol, oown, ohp, otr, otc, out = other
                    if oown != owner and ohp > 0:
                        if math.dist((row, col), (orow, ocol)) <= 7:
                            target_unit = (j, other)
                            break

            # 执行攻击
            if target_city:
                ci, (cr, cc, cown, chp) = target_city
                chp -= 5
                city_list[ci] = (cr, cc, cown, chp)
                floating_texts.append((cr, cc, "-5", (255, 50, 50)))
                log_event(f"Cannon at ({row},{col}) hits enemy city ({cr},{cc}) for 5 dmg")

            elif target_unit:
                j, (orow, ocol, oown, ohp, otr, otc, out) = target_unit
                ohp -= 5
                units[j] = (orow, ocol, oown, ohp, otr, otc, out)
                floating_texts.append((orow, ocol, "-5", (255, 50, 50)))
                log_event(f"Cannon at ({row},{col}) hits enemy {out} at ({orow},{ocol}) for 5 dmg")

            # 更新大炮状态
            units[i] = (row, col, owner, hp, tr, tc, ut)
            continue
        # ========== 大炮特殊逻辑结束 ==========

        # 普通士兵逻辑
        # 动态重定向
        tr, tc = retarget_if_proximity(row, col, owner, units, city_list, tr, tc)

        # 移动 speed 步
        for _ in range(speed):
            nr, nc = step_towards(row, col, tr, tc)
            row, col = nr, nc

        # 更新位置
        log_event(f"Player {owner} {ut} moved to ({row},{col}), target=({tr},{tc})")
        units[i] = (row, col, owner, hp, tr, tc, ut)

        # === 攻击阶段（每个士兵每回合一次） ===
        attacked = False

        # 1. 攻击敌方城市（优先级高）
        for ci, city in enumerate(city_list):
            city_row = city[0]
            city_col = city[1]
            city_owner = city[2]
            city_hp = city[3]
            city_level = city[4]

            if city_owner == owner:
                continue
            if city_row == row and city_col == col:
                city_hp -= damage
                city_list[ci] = (city_row, city_col, city_owner, city_hp, city_level)
                floating_texts.append((row, col, f"-{damage}", (255, 100, 100)))
                attacked = True
                if city_hp <= 0:  # 城市被攻破 → 重定向
                    tr, tc = find_nearest_target(row, col, owner, city_list)
                    units[i] = (row, col, owner, hp, tr, tc, ut)
                break

        # 2. 没打城市，则打同格敌军（一名）
        if not attacked:
            for j, other in enumerate(units):
                if j == i:
                    continue
                orow, ocol, oown, ohp, otr, otc, out = other
                if oown == owner:
                    continue
                if orow == row and ocol == col:
                    ohp -= damage
                    if ohp <= 0:  # 击杀敌军 → 重定向
                        tr, tc = find_nearest_target(row, col, owner, city_list)
                        units[i] = (row, col, owner, hp, tr, tc, ut)
                    units[j] = (orow, ocol, oown, ohp, otr, otc, out)
                    log_event(
                        f"Player {owner} {ut} attacked enemy({oown}, {out}) at ({orow},{ocol}), damage={damage}, enemy_hp={ohp}")
                    floating_texts.append((row, col, f"-{damage}", (255, 120, 120)))
                    break

    # 清理被摧毁的城市
    city_list = [c for c in city_list if c[3] > 0]

    # 城市攻击阶段（每城打一个敌兵，普通半径3，王城半径5，伤害3）
    updated_units = list(units)
    for city2 in city_list:
        cr = city2[0]
        cc = city2[1]
        cown = city2[2]
        chp = city2[3]
        level = city2[4]
        radius = city_zone_radius((cr, cc, cown, chp))
        candidates = []
        for idx, s in enumerate(updated_units):
            sr, sc, sown, shp, tr, tc, ut = s
            if sown == cown:
                continue
            dist = ((sr - cr) ** 2 + (sc - cc) ** 2) ** 0.5
            if dist <= radius:
                candidates.append((idx, dist))
        if candidates:
            idx, _ = min(candidates, key=lambda x: x[1])
            sr, sc, sown, shp, tr, tc, ut = updated_units[idx]
            damage = 3 + (level - 1) * 3
            shp -= damage
            updated_units[idx] = (sr, sc, sown, shp, tr, tc, ut)
            floating_texts.append((sr, sc, "-3", (255, 180, 180)))

    # 清理死亡士兵（血量 ≤0）
    updated_units = [s for s in updated_units if s[3] > 0]

    # 检查目标是否已失效（目标城市被摧毁） → 重定向
    valid_city_positions = {(c[0], c[1]) for c in city_list}
    final_units = []
    for (row, col, owner, hp, tr, tc, ut) in updated_units:
        if (tr, tc) not in valid_city_positions:
            tr, tc = find_nearest_target(row, col, owner, city_list)
        final_units.append((row, col, owner, hp, tr, tc, ut))

    return final_units, city_list



