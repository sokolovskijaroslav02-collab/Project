import arcade
import os
import json
from arcade import Vector, Texture
from math import sin
import glob

class Entity(arcade.Sprite):
    def __init__(self, position, sprite_list, path, shoot):
        super().__init__(center_x=position[0], center_y=position[1])
        
        # Загрузка настроек
        with open('settings.json', 'r') as f:
            self.settings = json.load(f)
        
        self.import_assets(path)
        self.frame_index = 0
        self.status = 'right'
        
        # Устанавливаем первую текстуру
        self.set_texture(self.animations[self.status][0])
        self.z = self.settings['layers']['Level']
        
        # Движение
        self.position = Vector(position[0], position[1])
        self.direction = Vector(0, 0)
        self.speed = 500

        # Коллизии
        self.old_center_x = self.center_x
        self.old_center_y = self.center_y

        # Таймеры стрельбы
        self.can_shoot = True
        self.shoot_time = None
        self.duck = False
        self.cooldown = 200  # ms
        self.is_vulnerable = True
        self.hit_time = None
        self.invul_duration = 200  # ms

        # Здоровье
        self.health = 20

        # Звуки
        self.bullet_sound = arcade.Sound(os.path.join('audio', 'bullet.wav'), streaming=False)
        self.hit_sound = arcade.Sound(os.path.join('audio', 'hit.wav'), streaming=False)

    def import_assets(self, path):
        """Загрузка анимаций из папок"""
        self.animations = {}
        
        for folder_name in os.listdir(path):
            folder_path = os.path.join(path, folder_name)
            if os.path.isdir(folder_path):
                self.animations[folder_name] = []
                
                # Загружаем все PNG файлы в папке
                image_files = glob.glob(os.path.join(folder_path, "*.png")) + \
                             glob.glob(os.path.join(folder_path, "*.jpg"))
                
                for file_path in sorted(image_files):
                    texture = arcade.load_texture(file_path)
                    self.animations[folder_name].append(texture)

    def blink(self):
        """Эффект мигания при неуязвимости"""
        if not self.is_vulnerable:
            if self.wave_value():
                # Создаем белую маску для эффекта мигания
                white_texture = self.create_blink_texture()
                self.set_texture(white_texture)

    def create_blink_texture(self):
        """Создает белую текстуру для эффекта мигания"""
        # Простая реализация - делаем текстуру полупрозрачной белой
        blink_texture = arcade.Texture.create_fitted(
            "blink", 
            self.texture.image.convert("RGBA"), 
            arcade.color.WHITE, 
            0.7  # полупрозрачность
        )
        return blink_texture

    def wave_value(self):
        """Синусоидальная волна для мигания"""
        value = sin(arcade.get_time() * 10)  # *10 для более быстрого мигания
        return value > 0

    def shoot_timer(self):
        """Таймер перезарядки"""
        if not self.can_shoot:
            current_time = arcade.get_time() * 1000  # в миллисекунды
            if current_time - self.shoot_time > self.cooldown:
                self.can_shoot = True

    def invul_timer(self):
        """Таймер неуязвимости"""
        if not self.is_vulnerable:
            current_time = arcade.get_time() * 1000
            if current_time - self.hit_time > self.invul_duration:
                self.is_vulnerable = True

    def damage(self):
        """Получение урона"""
        if self.is_vulnerable:
            self.health -= 1
            arcade.play_sound(self.hit_sound, 0.5)
            self.is_vulnerable = False
            self.hit_time = arcade.get_time() * 1000

    def check_death(self):
        """Проверка смерти"""
        if self.health <= 0:
            self.remove_from_sprite_lists()

    def animate(self, delta_time):
        """Анимация"""
        animation_speed = 7  # кадров в секунду
        self.frame_index += animation_speed * delta_time
        
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0
        
        # Устанавливаем текущий кадр
        new_texture = self.animations[self.status][int(self.frame_index)]
        self.set_texture(new_texture)

    def update(self, delta_time):
        """Основной update метод"""
        self.animate(delta_time)
        self.blink()
        self.shoot_timer()
        self.invul_timer()
