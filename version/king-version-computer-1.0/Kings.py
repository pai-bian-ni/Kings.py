from tool import *


pygame.init()
screen = pygame.display.set_mode((1100, 800))
clock = pygame.time.Clock()
gameTime = 0


import os, sys, pygame

def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容 PyInstaller 打包后"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # Kings.py 所在目录的上两级目录
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

# 设置窗口标题
pygame.display.set_caption("Kings")

# 设置窗口图标
icon_path = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "Assets", "icon1.ico"))

if os.path.exists(icon_path):
    try:
        icon_surface = pygame.image.load(icon_path)
        pygame.display.set_icon(icon_surface)
        print("已成功加载自定义窗口图标:", icon_path)
    except Exception as e:
        print("加载图标失败:", e)
else:
    print("图标文件不存在:", icon_path)




# 初始数据
# 城市：(row, col, owner, hp, level)
cities = [
    (0, 10, 0, 300, 1),   # Green King
    (19, 10, 1, 300, 1),  # Red King
    (4, 3, 0, 100, 1),
    (4, 16, 0, 100, 1),
    (15, 3, 1, 100, 1),
    (15, 16, 1, 100, 1),
]

# 士兵列表：(row, col, owner, hp, tr, tc, unit_type)
soldiers = []

current_player = 0   # 0=Green, 1=Red
turn_count = 1
selected_city = None
floating_texts = []  # (row, col, text, color)

# 资源
green_resources = 500
red_resources = 500

# 空降兵放置模式
placing_paratrooper = False

placing_cannon = False


font_small = pygame.font.SysFont(None, 24)
font_mid = pygame.font.SysFont(None, 28)

player_upgrades = {
    0: {"hp": 0, "hurt": 0, "speed": 0},  # 绿色
    1: {"hp": 0, "hurt": 0, "speed": 0},  # 红色
}

upgrade_buttons = {
    "hp": pygame.Rect(20, 150, 120, 40),
    "hurt": pygame.Rect(20, 200, 120, 40),
    "speed": pygame.Rect(20, 250, 120, 40),
}

print("当前兵种菜单：", list(UNIT_CONFIG.keys()))


def create_cannon(row, col, owner, cities):
    return (row, col, owner, 100, row, col, "cannon")


def log_event(message):
    with open("game.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")


def get_player_resources(player):
    return green_resources if player == 0 else red_resources

def set_player_resources(player, value):
    global green_resources, red_resources
    if player == 0:
        green_resources = value
    else:
        red_resources = value

def get_city_at(row, col):
    for c in cities:
        if c[0] == row and c[1] == col:
            return c
    return None

def end_turn():
    global current_player, turn_count, soldiers, cities, floating_texts, green_resources, red_resources

    # 回合开始给每位玩家 +100 资源（简单经济系统）
    if current_player == 0:
        green_resources += 100
    else:
        red_resources += 100

    # 推进战斗与移动
    soldiers, cities = move_soldiers(soldiers, cities, floating_texts, player_upgrades)

    # 检查国王城是否被摧毁
    alive_green_king = any((c[0] == green_king_pos[0] and c[1] == green_king_pos[1] and c[3] > 0) for c in cities)
    alive_red_king   = any((c[0] == red_king_pos[0]   and c[1] == red_king_pos[1]   and c[3] > 0) for c in cities)
    if not alive_green_king or not alive_red_king:
        draw_map(screen, soldiers, cities, current_player, turn_count, selected_city, floating_texts)
        pygame.display.flip()
        pygame.time.wait(1000)
        winner = "Red" if not alive_green_king else "Green"
        game_over_screen(winner)
        pygame.quit()
        raise SystemExit

    # 清理本回合飘字
    floating_texts.clear()

    # 轮换玩家
    current_player = 1 - current_player
    turn_count += 1

def game_over_screen(winner):
    screen.fill((10, 10, 20))
    txt = pygame.font.SysFont(None, 72).render(f"{winner} Player Wins!", True, (255, 80, 80))
    screen.blit(txt, (screen.get_width()/2 - txt.get_width()/2, screen.get_height()/2 - txt.get_height()/2))
    pygame.display.flip()
    pygame.time.wait(3000)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:  # 按下空格键切换阵营
                current_player = 1 - current_player  # 切换阵营
            elif event.key == pygame.K_p:      # P → 空降兵模式
                placing_paratrooper = True
                placing_cannon = False
            elif event.key == pygame.K_f:      # F → 大炮模式
                placing_cannon = True
                placing_paratrooper = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            cell = get_cell_from_mouse(pos, screen)

            # ==== DLC 左侧升级按钮 ====
            if pos[0] < 150:  # 左边 UI 区域
                for key, rect in upgrade_buttons.items():
                    if rect.collidepoint(pos):
                        res = get_player_resources(current_player)
                        if key == "hp" and res >= 300:
                            player_upgrades[current_player]["hp"] += 10
                            set_player_resources(current_player, res - 300)
                        elif key == "hurt" and res >= 300:
                            player_upgrades[current_player]["hurt"] += 5
                            set_player_resources(current_player, res - 300)
                        elif key == "speed" and res >= 500:
                            player_upgrades[current_player]["speed"] += 1
                            set_player_resources(current_player, res - 500)
                        break


            # ==== 空降兵模式 ====
            elif placing_paratrooper and cell:
                r, c = cell
                res = get_player_resources(current_player)
                if res >= UNIT_CONFIG["paratrooper"]["cost"]:
                    soldiers.append(create_unit("paratrooper", r, c, current_player, cities))
                    set_player_resources(current_player, res - UNIT_CONFIG["paratrooper"]["cost"])
                placing_paratrooper = False

            # ==== 大炮模式 ====
            elif placing_cannon and cell:
                r, c = cell
                res = get_player_resources(current_player)
                if res >= UNIT_CONFIG["cannon"]["cost"]:
                    soldiers.append(create_unit("cannon", r, c, current_player, cities))
                    set_player_resources(current_player, res - UNIT_CONFIG["cannon"]["cost"])
                placing_cannon = False

            # ==== 普通点击 ====
            else:
                if cell:
                    r, c = cell
                    city = get_city_at(r, c)

                    if city:  # 点击城市 → 打开菜单
                        selected_city = city

                    elif selected_city:  # 如果已经选中城市 → 检查按钮
                        rect_bg, menu_buttons = get_city_menu_buttons(screen, selected_city)
                        # 城市升级按钮区域
                        rect_bg, menu_buttons = get_city_menu_buttons(screen, selected_city)
                        upgrade_rect = pygame.Rect(rect_bg.right + 10, rect_bg.top, 100, 40)

                        if upgrade_rect.collidepoint(pos):
                            sr, sc, owner, hp, level = selected_city

                            # 只有当前阵营能升级
                            if owner == current_player:

                                # 等级上限 3
                                if level >= 3:
                                    print("城市已达到最高等级")
                                else:
                                    cost = 300
                                    res = get_player_resources(current_player)

                                    if res >= cost:
                                        # 扣资源
                                        set_player_resources(current_player, res - cost)

                                        # 升级城市
                                        # ⚠️ 因为 cities 是 tuple list，需要重建 tuple
                                        for i, c in enumerate(cities):
                                            if c[0] == sr and c[1] == sc:
                                                cities[i] = (sr, sc, owner, hp, level + 1)
                                                selected_city = cities[i]  # 同步更新选中状态
                                                break

                                        print("城市成功升级到 Level", level + 1)

                        # 点击兵种按钮
                        for unit_type, rect in menu_buttons.items():
                            if rect.collidepoint(pos):
                                sr, sc, owner, hp, level = selected_city
                                if owner == current_player:
                                    cost = UNIT_CONFIG[unit_type].get("cost", 100)
                                    res = get_player_resources(current_player)
                                    if res >= cost:
                                        soldiers.append(create_unit(unit_type, sr, sc, owner, cities))
                                        set_player_resources(current_player, res - cost)
                                break
                        else:
                            # 如果点在菜单框外 → 关闭菜单
                            if not rect_bg.collidepoint(pos):
                                selected_city = None
                    else:
                        selected_city = None

                else:  # 点击棋盘外
                    if selected_city:
                        rect_bg, menu_buttons = get_city_menu_buttons(screen, selected_city)
                        # 如果点到菜单按钮 → 正常处理
                        for unit_type, rect in menu_buttons.items():
                            if rect.collidepoint(pos):
                                sr, sc, owner, hp, level = selected_city
                                if owner == current_player:
                                    cost = UNIT_CONFIG[unit_type].get("cost", 100)
                                    res = get_player_resources(current_player)
                                    if res >= cost:
                                        soldiers.append(create_unit(unit_type, sr, sc, owner, cities))
                                        set_player_resources(current_player, res - cost)
                                break
                        # ⚠️ 不再写 selected_city = None，这样菜单会保持

    # 获取当前时间
    current_time = pygame.time.get_ticks()

    # 每过1秒（1000毫秒），更新资源和移动士兵
    if current_time - gameTime >= 1000:
        gameTime = current_time  # 更新游戏时间
        # 增加资源
        green_resources += 50
        red_resources += 50

        # 移动所有士兵
        soldiers, cities = move_soldiers(soldiers, cities, floating_texts, player_upgrades)
        # === 检查国王城是否被摧毁 ===
        alive_green_king = any((c[0] == green_king_pos[0] and c[1] == green_king_pos[1] and c[3] > 0) for c in cities)
        alive_red_king = any((c[0] == red_king_pos[0] and c[1] == red_king_pos[1] and c[3] > 0) for c in cities)

        if not alive_green_king or not alive_red_king:
            draw_map(screen, soldiers, cities, current_player, turn_count, selected_city, floating_texts)
            pygame.display.flip()
            pygame.time.wait(1000)
            winner = "Red" if not alive_green_king else "Green"
            game_over_screen(winner)
            pygame.quit()
            raise SystemExit

    # 绘制
    draw_map(screen, soldiers, cities, current_player, turn_count, selected_city, floating_texts)

    # 资源&提示
    pygame.draw.rect(screen, (35,35,45), (10, 50, 380, 70))
    res_text = font_mid.render(f"Green: {green_resources}      Red: {red_resources}", True, (230,230,240))
    screen.blit(res_text, (20, 60))
    tip_text = font_small.render("ENTER: End Turn   P: Paratrooper Mode   F: Cannon Mode", True, (200, 200, 210))
    screen.blit(tip_text, (20, 90))

    if placing_paratrooper:
        on_text = font_small.render("Paratrooper MODE: Click any valid tile (cost 200)", True, (120, 220, 255))
        screen.blit(on_text, (20, 115))

    if placing_cannon:
        on_text = font_small.render("Cannon MODE: Click within own city range (cost 700)", True, (255, 200, 100))
        screen.blit(on_text, (20, 135))

    # 绘制升级按钮
    pygame.draw.rect(screen, (80, 160, 80), upgrade_buttons["hp"])
    pygame.draw.rect(screen, (160, 80, 80), upgrade_buttons["hurt"])
    pygame.draw.rect(screen, (80, 80, 160), upgrade_buttons["speed"])

    txt1 = font_small.render("HP+10 (300)", True, (255,255,255))
    txt2 = font_small.render("Hurt+5 (300)", True, (255,255,255))
    txt3 = font_small.render("Speed+1 (500)", True, (255,255,255))

    screen.blit(txt1, (upgrade_buttons["hp"].x + 5, upgrade_buttons["hp"].y + 10))
    screen.blit(txt2, (upgrade_buttons["hurt"].x + 5, upgrade_buttons["hurt"].y + 10))
    screen.blit(txt3, (upgrade_buttons["speed"].x + 5, upgrade_buttons["speed"].y + 10))


    pygame.display.flip()
    clock.tick(60)

pygame.quit()