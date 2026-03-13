import arcade
from arcade import Vector, key
from entity import Entity
import sys

class Player(Entity):
    def __init__(self, position, sprite_lists, path, collision_sprites, shoot):
        super().__init__(position, sprite_lists, path, shoot)
        self.shoot = shoot

        # Движение
        self.gravity = 40 * 60  # пикселей/сек^2 (умножили на 60 FPS)
        self.jump_speed = 1100
        self.on_floor = False
        self.moving_floor = None
        
        self.collision_sprites = collision_sprites
        
        # Размеры для коллизий (hitbox)
        self.hitbox_width = 40
        self.hitbox_height = 60

    def get_status(self):
        """Определяет текущую анимацию"""
        base_status = self.status.split('_')[0]
        
        # idle
        if self.direction.x == 0 and self.on_floor:
            self.status = f"{base_status}_idle"
        # jump
        if self.direction.y < 0 and not self.on_floor:  # Вверх = отрицательное Y
            self.status = f"{base_status}_jump"
        # duck
        if self.on_floor and self.duck:
            self.status = f"{base_status}_duck"

    def check_contact(self):
        """Проверка контакта с полом"""
        # Создаем маленький rect снизу для проверки пола
        bottom_rect = arcade.Rect(
            self.center_x - self.hitbox_width // 2,
            self.bottom - 5,
            self.hitbox_width,
            5
        )
        
        for sprite in self.collision_sprites:
            if bottom_rect.collides_with_rect(sprite.get_bounding_box()):
                if self.direction.y > 0:  # Падаем вниз
                    self.on_floor = True
        
        # Проверяем движущуюся платформу
        if self.moving_floor and hasattr(self.moving_floor, 'direction'):
            self.moving_floor = self.moving_floor

    def collision(self, direction):
        """Обработка коллизий"""
        for sprite in self.collision_sprites:
            if arcade.check_for_collision(self, sprite):
                sprite_rect = sprite.get_bounding_box()
                
                if direction == 'horizontal':
                    # Слева
                    if (self.left <= sprite_rect.right and 
                        self.old_center_x - self.width/2 >= sprite_rect.right):
                        self.left = sprite_rect.right
                    
                    # Справа
                    if (self.right >= sprite_rect.left and 
                        self.old_center_x + self.width/2 <= sprite_rect.left):
                        self.right = sprite_rect.left
                    
                    self.position.x = self.center_x
                
                elif direction == 'vertical':
                    # Снизу (пол)
                    if (self.bottom >= sprite_rect.top and 
                        self.old_center_y + self.height/2 <= sprite_rect.top):
                        self.bottom = sprite_rect.top
                        self.on_floor = True
                    
                    # Сверху (потолок)
                    if (self.top <= sprite_rect.bottom and 
                        self.old_center_y - self.height/2 >= sprite_rect.bottom):
                        self.top = sprite_rect.bottom
                    
                    self.position.y = self.center_y
                    if self.top <= sprite_rect.bottom:
                        self.direction.y = 0
        
        # Сброс флага пола если летим
        if self.on_floor and self.direction.y < 0:
            self.on_floor = False

    def check_death(self):
        """Проверка смерти"""
        if self.health <= 0:
            arcade.close_window()
            sys.exit()

    def input(self, keys):
        """Обработка ввода"""
        # Горизонтальное движение
        if keys[key.LEFT] or keys[key.A]:
            self.direction.x = -1
            self.status = 'left'
        elif keys[key.RIGHT] or keys[key.D]:
            self.direction.x = 1
            self.status = 'right'
        else:
            self.direction.x = 0
        
        # Вертикальное движение
        if (keys[key.UP] or keys[key.W]) and self.on_floor:
            self.direction.y = -self.jump_speed  # Вверх = отрицательное
        
        # Приседание
        if keys[key.DOWN] or keys[key.S] or keys[key.LCTRL]:
            self.duck = True
        else:
            self.duck = False
        
        # Блокировка движения при приседании
        if self.duck and self.on_floor:
            self.direction.x = 0
        
        # Стрельба
        if keys[key.SPACE] and self.can_shoot:
            direction = Vector(1, 0) if self.status.split('_')[0] == 'right' else Vector(-1, 0)
            position = Vector(self.center_x, self.center_y) + direction * 80
            
            y_offset = Vector(0, -16) if not self.duck else Vector(0, 10)
            
            self.shoot(position + y_offset, direction, self)
            arcade.play_sound(self.bullet_sound, 0.5)
            self.can_shoot = False
            self.shoot_time = arcade.get_time() * 1000

    def move(self, delta_time):
        """Движение игрока"""
        # Горизонтальное движение
        self.position.x += self.direction.x * self.speed * delta_time
        self.center_x = round(self.position.x)
        self.collision('horizontal')
        
        # Вертикальное движение + гравитация
        self.direction.y += self.gravity * delta_time
        self.position.y += self.direction.y * delta_time
        
        # Привязка к движущейся платформе
        if (self.moving_floor and 
            hasattr(self.moving_floor, 'direction') and 
            self.moving_floor.direction.y > 0 and 
            self.direction.y > 0):
            self.direction.y = 0
            self.bottom = self.moving_floor.top
            self.position.y = self.center_y
            self.on_floor = True
        
        self.center_y = round(self.position.y)
        self.collision('vertical')
        self.moving_floor = None

    def update(self, delta_time, keys):
        """Основной update"""
        # Сохраняем старую позицию для коллизий
        self.old_center_x = self.center_x
        self.old_center_y = self.center_y
        
        # Ввод
        self.input(keys)
        self.get_status()
        self.move(delta_time)
        self.check_contact()
        self.animate(delta_time)
        self.blink()

        # Таймеры
        self.shoot_timer()
        self.invul_timer()

        # Проверка смерти
        self.check_death()
