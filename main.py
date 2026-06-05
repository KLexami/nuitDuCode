import pyxel
import math
import random

#FICHIER NATHAN

enemies = []
SIZE = 8

class Enemy:
    def __init__(self, speed, hp, position_x, position_y, sprite,
                 path=None, reward=100, damage=1):
        self.max_hp = hp
        self.hp = hp

        self.speed = speed
        self.position_x = position_x
        self.position_y = position_y

        self.sprite = sprite

        self.reward = reward
        self.damage = damage

        self.waypoint = 0

        if path is not None:
            self.path = path
        else:
            self.path = []

        self.reached_end = False

        enemies.append(self)

    def update(self):
        self.follow_path()

    def draw(self):
        pyxel.blt(self.position_x, self.position_y, 0,
                  self.sprite[0], self.sprite[1], self.SIZE, self.SIZE, 0)
        self.draw_health_bar()
    
    def draw_health_bar(self):
        ratio = self.hp / self.max_hp
        pyxel.rect(self.position_x, self.position_y - 2, self.SIZE, 1, 5)
        pyxel.rect(self.position_x, self.position_y - 2, self.SIZE * ratio, 1, 10)

    def take_damage(self, amount):
        self.hp -= amount
        if not self.is_alive():
            self.destroy()

    def is_alive(self):
        return self.hp > 0

    def destroy(self):
        if self in enemies:
            enemies.remove(self)

    def follow_path(self):
        if self.waypoint >= len(self.path):
            self.reached_end = True
            return

        target_x, target_y = self.path[self.waypoint]
        dx = target_x - self.position_x
        dy = target_y - self.position_y
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance <= self.speed or distance == 0:
            self.position_x, self.position_y = target_x, target_y
            self.waypoint += 1
        else:
            self.position_x += (dx / distance) * self.speed
            self.position_y += (dy / distance) * self.speed

class Tower:
    def __init__(self, position_x, position_y, damage, range, cooldown, scale=1, attack_type="single"):
        self.scale = scale
        self.position_x = position_x
        self.position_y = position_y

        self.damage = damage
        self.range = range
        self.cooldown = cooldown

        self.attack_type = attack_type

        self.cooldown_timer = 0

    def update(self):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1
            return

        target = self.focus()
        if target is not None:
            self.attack(target)
            self.cooldown_timer = self.cooldown

    def distance_to(self, enemy):
        dx = enemy.position_x - self.position_x
        dy = enemy.position_y - self.position_y
        return (dx ** 2 + dy ** 2) ** 0.5

    def in_range(self, enemy):
        return self.distance_to(enemy) <= self.range

    def on_same_lane(self, enemy):
        return enemy.position_y == self.position_y

    def attack(self, target):
        if self.attack_type == "single":
            target.take_damage(self.damage)

        elif self.attack_type == "lane":
            for enemy in list(enemies):
                if self.on_same_lane(enemy) and self.in_range(enemy):
                    enemy.take_damage(self.damage)

        elif self.attack_type == "splash":
            for enemy in list(enemies):
                dx = enemy.position_x - target.position_x
                dy = enemy.position_y - target.position_y
                if (dx ** 2 + dy ** 2) ** 0.5 <= self.range:
                    enemy.take_damage(self.damage)

        elif self.attack_type == "full":
            for enemy in list(enemies):
                if self.in_range(enemy):
                    enemy.take_damage(self.damage)

    def focus(self):
        best_enemy = None
        max_progress = -1

        for enemy in enemies:
            if not self.in_range(enemy):
                continue
            if (self.attack_type == "lane") and not (self.on_same_lane(enemy)):
                continue
            if enemy.waypoint > max_progress:
                max_progress = enemy.waypoint
                best_enemy = enemy

        return best_enemy


#FICHIER OSCAR :

class App:
    TOWER_STATS = {
        1: (1, 40, 30, "single"),
        2: (2, 32, 45, "splash"),
        3: (1, 64, 20, "lane"),
        4: (3, 48, 60, "single"),
        5: (1, 80, 90, "full"),
        6: (5, 40, 40, "single"),
    }

    def __init__(self):
        pyxel.init(256, 256, title="Nuit du Code", fps=60, quit_key=pyxel.KEY_NONE, display_scale=3)
        self.state = 0 #0: menu, 1: game, 2: shop
        self.gold = 100
        self.selected = 1
        pyxel.mouse(True)
        pyxel.load("theme.pyxres", exclude_images=False, exclude_tilemaps=True, exclude_sounds=True, exclude_musics=True)

        Enemy.SIZE = SIZE
        self.game_map = create_map()            # carte 32x32 de Noe
        self.towers = []                        # instances Tower de Nathan

        self.path_tiles = [(0, 4), (10, 4), (10, 14), (22, 14),
                           (22, 26), (5, 26), (5, 31)]
        self.path = [(tx * SIZE, ty * SIZE) for tx, ty in self.path_tiles]
        self.carve_path()

        self.frame = 0
        self.spawned = 0
        self.wave_size = 12
        self.spawn_interval = 40
        self.wave = 1

        pyxel.run(self.update, self.draw)

    #  carte / chemin 
    def carve_path(self):
        for (x1, y1), (x2, y2) in zip(self.path_tiles, self.path_tiles[1:]):
            if x1 == x2:
                for ty in range(min(y1, y2), max(y1, y2) + 1):
                    add_path(self.game_map, x1, ty, 99, None)
            else:
                for tx in range(min(x1, x2), max(x1, x2) + 1):
                    add_path(self.game_map, tx, y1, 99, None)

    #  ennemis 
    def spawn_enemy(self):
        Enemy(speed=0.7, hp=6 + self.wave, position_x=self.path[0][0],
              position_y=self.path[0][1], sprite=(0, 0),
              path=self.path[1:], reward=5)

    #  placement des tours 
    def place_tower(self, tx, ty):
        z = self.selected - 1
        if not (0 <= tx < 32 and 0 <= ty < 32):
            return
        if not (0 <= z < 6):
            return
        if if_elem(self.game_map, tx, ty):
            return
        self.game_map, self.gold = add_tower(self.game_map, tx, ty, z, self.gold)
        if if_elem(self.game_map, tx, ty):
            dmg, rng, cd, atk = self.TOWER_STATS[self.selected]
            self.towers.append(Tower(tx * SIZE, ty * SIZE, dmg, rng, cd, attack_type=atk))

    def update(self):
        if pyxel.btnp(pyxel.KEY_E):
            self.state = 1

        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.state = 0

        if pyxel.btnp(pyxel.KEY_SPACE):
            if self.state == 1:
                self.state = 2
            elif self.state == 2:
                self.state = 1

        if pyxel.btnp(pyxel.KEY_G):
            self.gold += 1

        for i, key in enumerate((pyxel.KEY_1, pyxel.KEY_2, pyxel.KEY_3,
                                 pyxel.KEY_4, pyxel.KEY_5, pyxel.KEY_6)):
            if pyxel.btnp(key):
                self.selected = i + 1

        if self.state == 2 and pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and pyxel.mouse_y >= 128:
            idx = (pyxel.mouse_y - 128) // 64 * 4 + pyxel.mouse_x // 64 + 1
            if 1 <= idx <= 6:
                self.selected = idx

        if self.state == 1:
            self.update_game()

    def update_game(self):
        self.frame += 1

        if self.spawned < self.wave_size and self.frame % self.spawn_interval == 0:
            self.spawn_enemy()
            self.spawned += 1

        if self.spawned >= self.wave_size and not enemies:
            self.wave += 1
            self.spawned = 0

        for enemy in list(enemies):
            enemy.update()

        for enemy in list(enemies):
            if enemy.reached_end:
                enemy.destroy()

        before = set(enemies)
        for tower in self.towers:
            tower.update()
        for enemy in before - set(enemies):
            self.gold += enemy.reward

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.place_tower(pyxel.mouse_x // SIZE, pyxel.mouse_y // SIZE)

    def draw_game(self):
        pyxel.rect(0, 0, 256, 256, 3)

        for tx in range(32):
            for ty in range(32):
                cell = self.game_map[tx][ty]
                if cell[0] == 99:
                    pyxel.rect(tx * SIZE, ty * SIZE, SIZE, SIZE, 4)
                elif cell[0] != 0:
                    pic = cell[1]
                    if pic:
                        pyxel.blt(tx * SIZE, ty * SIZE, 0, pic[0], pic[1], SIZE, SIZE, 0)
                    else:
                        pyxel.rect(tx * SIZE, ty * SIZE, SIZE, SIZE, 11)

        for enemy in list(enemies):
            enemy.draw()

    def draw(self):

        pyxel.cls(0)
        if self.state == 0: # MENU / PAUSE
            pyxel.fill(0, 0, 1)
            pyxel.text(95, 20, "LE JEU EST EN PAUSE", 8)
            pyxel.rectb(70, 67, 126, 30, 7)
            pyxel.text(82, 80, "APPUYEZ SUR 'E' POUR JOUER", 8)

        elif self.state == 1: # JEU / AFFICHAGE PRINCIPAL
            self.draw_game()
            pyxel.text(200, 5, "SHOP:'ESPACE'", 8)
            pyxel.rectb(195, 1, 60, 15, 7)
            pyxel.text(100, 5, f"VAGUE : {self.wave}", 8)

        elif self.state == 2: #SHOP
            pyxel.rectb(70, 67, 126, 30, 7)
            pyxel.text(82, 80, "APPUYEZ SUR 'E' POUR JOUER", 8)

            # GRILLE DE SHOP
            pyxel.rectb(0, 128, 64, 64, 7)
            pyxel.rectb(64, 128, 64, 64, 7)
            pyxel.rectb(128, 128, 64, 64, 7)
            pyxel.rectb(192, 128, 64, 64, 7)

            pyxel.rectb(0, 192, 64, 64, 7)
            pyxel.rectb(64, 192, 64, 64, 7)
            pyxel.rectb(128, 192, 64, 64, 7)
            pyxel.rectb(192, 192, 64, 64, 7)

            pyxel.text(5, 133, "1", 8)
            pyxel.text(69, 133, "2", 8)
            pyxel.text(133, 133, "3", 8)
            pyxel.text(197, 133, "4", 8)

            pyxel.text(5, 197, "5", 8)
            pyxel.text(69, 197, "6", 8)
            pyxel.text(133, 197, "7", 8)
            pyxel.text(197, 197, "8", 8)

            if 1 <= self.selected <= 6:
                col = (self.selected - 1) % 4
                row = (self.selected - 1) // 4
                pyxel.rectb(col * 64, 128 + row * 64, 64, 64, 10)


        pyxel.text(5, 5, f"PIECES D'OR : {self.gold}", 10)
        pyxel.text(5, 15, f"TOUR SÉLECTIONNÉE : {self.selected}", 5)


#FICHIER NOE

def init(self):
        pyxel.init(256, 256, title="Nuit du Code", fps=60, quit_key=pyxel.KEY_ESCAPE, display_scale=3)
        self.state = 0 #0: menu, 1: game
        pyxel.mouse(True)
        pyxel.load("theme.pyxres", exclude_images=False, exclude_tilemaps=True, exclude_sounds=True, exclude_musics=True)
        pyxel.run(self.update, self.draw)

class Tilemap:
    def __init__(self):
        Tilemap.load(0,2,"themes.pyxres")
        Tilemap.set(0,2)

def create_map():
    return [[[0, None] for _ in range(32)] for _ in range(32)]

def if_elem(game_map, x, y):
    if game_map[x][y][0] != 0:
        return True
    return False

def add_tower(game_map, x, y, z, money):
    money_per_tower = [10, 20, 30, 40, 50, 60]
    towers = [1, 2, 3, 4, 5, 6]
    tower_pics = [(0, 32), (8, 32), (16, 32), (24, 32), (32, 32), (40, 32)]
    if 0 <= z < len(towers):
        if not if_elem(game_map, x, y) and money >= money_per_tower[z]:
            game_map[x][y][0] = towers[z]
            game_map[x][y][1] = tower_pics[z]
            money -= money_per_tower[z]
        else:
            print("Pas assez d'argent")
    return game_map, money


def add_path(game_map, x, y, type, pic):
    if not if_elem(game_map, x, y):
        game_map[x][y][0] = type
        game_map[x][y][1] = pic
    return game_map


def create_path():
    paths = ["straight", "left", "right", "merge", "split", "4th"]
    random.shuffle(paths)
    return paths


def print_map(game_map):
    for x in range(32):
        for y in range(32):
            print(game_map[x][y], end=" ")
        print()

def get_themes_id(file):
    pyxel.images[0].load(100, 100, "themes.pyxres")

    return id

def main():
    Tilemap.load()
    game_map = create_map()
    money = 100
    game_map, money = add_tower(game_map, 0, 1, 0, money)
    id = Tilemap.set(0,2)
    print_map(game_map)

App()
