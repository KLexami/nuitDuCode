import pyxel


class enemy:
    def __init__(self, speed, hp, effects, position_x, position_y):
        
        self.speed = speed
        self.hp = hp
        self.effects = effects

        self.position_x = position_x
        self.position_y = position_y

    def draw(self, sprite):
        self.sprite = sprite

    def movement(self, x, y):
        self.position








def update():
    if pyxel.btnp(pyxel.KEY_Q):
        pyxel.quit

def draw():
    pyxel.cls(0)
    pyxel.rect(10, 10, 20, 20, 10)




if __name__ == "main":
    pyxel.init(128, 128, title="Nuit du code")

    pyxel.run(update, draw)
    main()