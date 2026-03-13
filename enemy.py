import arcade
from arcade import Vector
import math
from entity import Entity  # Предполагается, что Entity тоже адаптирован под Arcade

class Enemy(Entity):
    def __init__(self, position, sprite_list, path, shoot, player, collision_sprites):
        super().__init__(position, sprite_list, path, shoot)
        
        self.player = player
        
        # Корректировка позиции по коллизиям
        for sprite in collision_sprites:
            if arcade.check_for_collision(self, sprite):
                # Проверяем midbottom точку
                mid_bottom = Vector(self.center_x, self.bottom)
                if sprite.collides_with_point((mid_bottom.x, mid_bottom.y)):
                    self.bottom = sprite.top
        
        self.shoot = shoot
        self.cooldown = 800  # ms
        self.health = 3
        self.shoot_time = 0

    def get_status(self):
        """Определяет направление взгляда врага"""
        if self.player.center_x < self.center_x:
            self.status = 'left'
        else:
            self.status = 'right'

    def check_fire(self):
        """Проверяет условия для выстрела"""
        enemy_pos = Vector(self.center_x, self.center_y)
        player_pos = Vector(self.player.center_x, self.player.center_y)
        distance = (player_pos - enemy_pos).magnitude()
        
        # Проверка по Y (с допуском 20 пикселей)
        same_y = (self.top - 20 < player_pos.y < self.bottom + 20)
        
        if distance < 600 and same_y and self.can_shoot:
            # Направление пули
            bullet_direction = Vector(1, 0) if self.status == 'right' else Vector(-1, 0)
            y_offset = Vector(0, -16)
            
            # Позиция спавна пули
            position = Vector(self.center_x, self.center_y) + bullet_direction * 80
            
            # Выстрел
            self.shoot(position + y_offset, bullet_direction, self)
            self.bullet_sound.play()
            self.can_shoot = False
            self.shoot_time = arcade.get_time() * 1000  # в миллисекунды

    def update(self, delta_time):
        """Основной update метод"""
        self.get_status()
        self.animate(delta_time)
        self.blink()

        # Таймеры
        self.shoot_timer()
        self.invul_timer()
        self.check_fire()

        # Проверка смерти
        self.check_death()
