import arcade
import os
import sys
import json
from pytmx.util_pygame import load_pygame  # Заменить на arcade-tmx или аналог
from overlay import Overlay  # Нужно адаптировать
from tile import Tile, CollisionTile, MovingPlatform  # Нужно адаптировать
from player import Player  # Уже адаптирован
from bullet import Bullet, FireAnimationManual as FireAnimation  # Уже адаптирован
from enemy import Enemy  # Уже адаптирован

class AllSprites(arcade.SpriteList):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.camera = None  # Будет установлена позже
        
        # Загрузка неба
        self.fg_sky = arcade.load_texture(os.path.join('graphics', 'sky', 'fg_sky.png'))
        self.bg_sky = arcade.load_texture(os.path.join('graphics', 'sky', 'bg_sky.png'))
        
        # Загрузка карты для вычисления размеров
        tmx_map = load_pygame(os.path.join('data', 'map.tmx'))
        self.padding = self.settings['window_width'] / 2
        self.sky_width = self.bg_sky.width
        map_width = tmx_map.width * tmx_map.tilewidth + 2 * self.padding
        self.sky_num = int(map_width // self.sky_width)

    def custom_draw(self, camera):
        """Кастомный рендеринг с сортировкой по Z"""
        camera.use()
        
        # Рисуем небо (параллакс)
        for x in range(self.sky_num):
            xpos = -self.padding + x * self.sky_width
            
            # Фон неба (медленный параллакс)
            self.bg_sky.draw_scaled(
                xpos - camera.position.x / 2.5, 
                800 - camera.position.y / 2.5,
                1.0
            )
            
            # Передний план неба (быстрый параллакс)
            self.fg_sky.draw_scaled(
                xpos - camera.position.x / 2, 
                800 - camera.position.y / 2,
                1.0
            )
        
        # Рисуем спрайты по Z порядку
        for sprite in sorted(self, key=lambda s: getattr(s, 'z', 0)):
            sprite.draw()

class Game(arcade.Window):
    def __init__(self):
        # Загрузка настроек
        with open('settings.json', 'r') as f:
            self.settings = json.load(f)
        
        # Создание окна
        super().__init__(
            width=self.settings['window_width'],
            height=self.settings['window_height'],
            title='Contra',
            resizable=False
        )
        
        arcade.set_background_color(arcade.color.SAND_YELLOW)  # (249,131,103)
        
        # Группы спрайтов
        self.all_sprites = AllSprites(self.settings)
        self.collision_sprites = arcade.SpriteList()
        self.platform_sprites = arcade.SpriteList()
        self.bullet_sprites = arcade.SpriteList()
        self.vulnerable_sprites = arcade.SpriteList()
        
        # Пули и анимации
        self.bullet_texture = arcade.load_texture(os.path.join('graphics', 'bullet.png'))
        self.bullet_animations = [
            arcade.load_texture(os.path.join('graphics', 'fire', '0.png')),
            arcade.load_texture(os.path.join('graphics', 'fire', '1.png'))
        ]
        
        # Камера
        self.camera = arcade.Camera(self.width, self.height)
        self.all_sprites.camera = self.camera
        
        # Музыка
        self.music = arcade.Sound(os.path.join('audio', 'music.wav'), streaming=True)
        
        self.setup()
        self.overlay = Overlay(self.player)  # Нужно адаптировать Overlay
        
        # UI камера
        self.ui_camera = arcade.Camera(self.width, self.height)

    def setup(self):
        """Загрузка уровня"""
        map_tmx = load_pygame(os.path.join('data', 'map.tmx'))
        
        # Тайлы уровня (коллизии)
        level_layer = map_tmx.get_layer_by_name('Level')
        for x, y, gid in level_layer:
            surface = map_tmx.get_tile_image_by_gid(gid)
            if surface:
                CollisionTile(
                    (x * 64, y * 64), 
                    surface, 
                    [self.all_sprites, self.collision_sprites]
                )
        
        # Декоративные слои
        for layer_name in ['BG', 'BG Detail', 'FG Detail Bottom', 'FG Detail Top']:
            layer = map_tmx.get_layer_by_name(layer_name)
            z_index = self.settings['layers'][layer_name]
            for x, y, gid in layer:
                surface = map_tmx.get_tile_image_by_gid(gid)
                if surface:
                    Tile(
                        (x * 64, y * 64),
                        surface,
                        self.all_sprites,
                        z_index
                    )
        
        # Объекты (игрок, враги)
        entities_layer = map_tmx.get_layer_by_name('Entities')
        for obj in entities_layer:
            if obj.name == 'Player':
                self.player = Player(
                    (obj.x, obj.y),
                    [self.all_sprites, self.vulnerable_sprites],
                    'graphics/player',  # Исправлен путь
                    self.collision_sprites,
                    self.shoot
                )
            elif obj.name == 'Enemy':
                Enemy(
                    (obj.x, obj.y),
                    [self.all_sprites, self.vulnerable_sprites],
                    'graphics/enemies',
                    self.shoot,
                    self.player,
                    self.collision_sprites
                )
        
        self.platform_border_rects = []
        
        # Платформы
        platforms_layer = map_tmx.get_layer_by_name('Platforms')
        for obj in platforms_layer:
            if obj.name == 'Platform':
                MovingPlatform(
                    (obj.x, obj.y),
                    obj.image,
                    [self.all_sprites, self.collision_sprites, self.platform_sprites]
                )
            else:
                # Границы платформ
                self.platform_border_rects.append(
                    arcade.Rect(obj.x, obj.y, obj.width, obj.height)
                )

    def bullet_collisions(self):
        """Коллизии пуль"""
        # С препятствиями
        for bullet in self.bullet_sprites:
            hit_list = arcade.check_for_collision_with_list(bullet, self.collision_sprites)
            for obstacle in hit_list:
                bullet.remove_from_sprite_lists()
        
        # С уязвимыми спрайтами
        for sprite in self.vulnerable_sprites:
            hit_list = arcade.check_for_collision_with_list(sprite, self.bullet_sprites, arcade.PymunkPhysicsEngine)
            for bullet in hit_list:
                sprite.damage()
                bullet.remove_from_sprite_lists()

    def shoot(self, position, direction, entity):
        """Выстрел"""
        Bullet(
            position,
            self.bullet_texture,
            direction,
            [self.all_sprites, self.bullet_sprites],
            self.settings
        )
        FireAnimation(
            position,
            direction,
            self.bullet_animations,
            self.all_sprites,
            self.settings,
            entity
        )

    def platform_collisions(self):
        """Коллизии платформ"""
        player_rect = arcade.Rect(self.player.center_x - 20, self.player.center_y - 30, 40, 60)
        
        for platform in self.platform_sprites:
            for border in self.platform_border_rects:
                if platform.collides_with_rect(border):
                    if platform.direction.y < 0:
                        platform.top = border.bottom
                        platform.position.y = platform.center_y
                        platform.direction.y = 1
                    else:
                        platform.bottom = border.top
                        platform.position.y = platform.center_y
                        platform.direction.y = -1
            
            # Коллизия с игроком
            if player_rect.collides_with_rect(platform.get_bounding_box()):
                if self.player.center_y > platform.center_y:
                    platform.bottom = self.player.top
                    platform.position.y = platform.center_y
                    platform.direction.y = -1

    def on_update(self, delta_time):
        """Обновление игры"""
        self.platform_collisions()
        self.all_sprites.update(delta_time)
        self.bullet_collisions()
        
        # Центрирование камеры на игроке
        self.center_camera_to_player()

    def center_camera_to_player(self):
        """Центрирование камеры"""
        screen_center_x = self.player.center_x - (self.width // 2)
        screen_center_y = self.player.center_y - (self.height // 2)
        
        player_centered = arcade.Rect(
            screen_center_x, screen_center_y,
            self.width, self.height
        )
        
        # Ограничиваем камеру границами карты (при необходимости)
        self.camera.move_to(player_centered)

    def on_draw(self):
        """Рендеринг"""
        self.clear()
        
        # Основная камера (мир)
        self.camera.use()
        self.all_sprites.custom_draw(self.camera)
        
        # UI камера (оверлей)
        self.ui_camera.use()
        self.overlay.display()  # Нужно адаптировать overlay

    def on_key_press(self, key, modifiers):
        """Обработка нажатий клавиш"""
        pass  # Добавить управление

    def on_close(self):
        """Закрытие окна"""
        arcade.close_window()

if __name__ == '__main__':
    # Создание и запуск игры
    game = Game()
    arcade.run()
