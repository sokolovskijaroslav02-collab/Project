import arcade
import os
import json
from arcade import Vector

class Tile(arcade.Sprite):
    def __init__(self, position, texture, sprite_list, z):
        super().__init__(
            texture=texture,
            center_x=position[0],
            center_y=position[1]
        )
        self.z = z
        
        # Hitbox для коллизий (немного меньше по высоте)
        self.hitbox = arcade.Rect(
            self.left, self.bottom,
            self.width, self.height * 0.5
        )

class CollisionTile(Tile):
    def __init__(self, position, texture, sprite_list):
        # Загрузка настроек
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        
        z_level = settings['layers']['Level']
        super().__init__(position, texture, sprite_list, z_level)
        
        # Сохраняем старую позицию для коллизий
        self.old_center_x = self.center_x
        self.old_center_y = self.center_y

class MovingPlatform(CollisionTile):
    def __init__(self, position, texture, sprite_list):
        super().__init__(position, texture, sprite_list)
        
        # Направление движения (вверх = -1)
        self.direction = Vector(0, -1)
        self.speed = 200  # пикселей/сек
        
        # Текущая позиция
        self.position = Vector(self.center_x, self.center_y)

    def move(self, delta_time):
        """Движение платформы"""
        self.position.y += self.direction.y * self.speed * delta_time
        self.center_y = round(self.position.y)

    def update(self, delta_time):
        """Обновление платформы"""
        # Сохраняем старую позицию
        self.old_center_x = self.center_x
        self.old_center_y = self.center_y
        
        self.move(delta_time)
