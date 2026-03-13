import arcade
from arcade import Vector
import math

class Bullet(arcade.Sprite):
    def __init__(self, position, texture, direction, sprite_list, settings):
        super().__init__(texture=texture, center_x=position[0], center_y=position[1])
        
        # Поворот текстуры если направление влево
        if direction.x < 0:
            self.texture = arcade.Texture.create_fitted(
                texture.name + "_flipped", 
                texture.image, 
                arcade.color.WHITE, 1
            )
            self.texture.image = arcade.Image.flip_vertical(arcade.Image.flip_horizontal(texture.image), False)
        
        self.z = settings['layers']['Level']
        self.start_time = arcade.get_time()
        
        # Позиция и направление
        self.position = Vector(position[0], position[1])
        self.direction = direction
        self.speed = 2000

    def update(self, delta_time):
        self.move(delta_time)
        self.check_lifetime()

    def move(self, delta_time):
        self.position += self.direction * self.speed * delta_time
        self.center_x = round(self.position.x)
        self.center_y = round(self.position.y)

    def check_lifetime(self):
        if arcade.get_time() - self.start_time > 1.0:  # 1000ms = 1s
            self.remove_from_sprite_lists()

class FireAnimation(arcade.AnimatedTimeSprite):
    def __init__(self, position, direction, texture_sequence, sprite_list, settings, entity):
        # Создаем анимированный спрайт из последовательности текстур
        super().__init__(
            texture_sequence=texture_sequence,
            center_x=position[0],
            center_y=position[1]
        )
        
        # Смещение
        x_offset = 60 if direction.x > 0 else -60
        y_offset = 10 if getattr(entity, 'duck', False) else -16
        self.offset = Vector(x_offset, y_offset)
        
        self.entity = entity
        self.z = settings['layers']['Level']
        
        # Настройка анимации (15 кадров в секунду)
        self._frames_per_second = 15

    def update(self, delta_time):
        # Обновляем позицию относительно entity
        self.move_to_entity()
        super().update_animation(delta_time)

    def move_to_entity(self):
        entity_pos = Vector(self.entity.center_x, self.entity.center_y)
        new_pos = entity_pos + self.offset
        self.center_x = new_pos.x
        self.center_y = new_pos.y

# Альтернативная реализация FireAnimation без AnimatedTimeSprite (более гибкая)
class FireAnimationManual(arcade.Sprite):
    def __init__(self, position, direction, texture_list, sprite_list, settings, entity):
        # Берем первый кадр
        super().__init__(texture=texture_list[0], center_x=position[0], center_y=position[1])
        
        # Смещение
        x_offset = 60 if direction.x > 0 else -60
        y_offset = 10 if getattr(entity, 'duck', False) else -16
        self.offset = Vector(x_offset, y_offset)
        
        self.entity = entity
        self.textures = texture_list  # Список текстур для анимации
        
        # Подготовка перевернутых текстур если нужно
        if direction.x < 0:
            self.textures = [
                arcade.Texture.create_fitted(
                    tex.name + "_flipped", 
                    tex.image, 
                    arcade.color.WHITE, 1
                ) for tex in texture_list
            ]
        
        self.frame_index = 0
        self.frame_time = 0
        self.animation_speed = 15  # кадров в секунду
        self.z = settings['layers']['Level']

    def update(self, delta_time):
        self.animate(delta_time)
        self.move_to_entity()

    def animate(self, delta_time):
        self.frame_time += delta_time
        if self.frame_time >= 1.0 / self.animation_speed:
            self.frame_time = 0
            self.frame_index += 1
            
            if self.frame_index >= len(self.textures):
                self.remove_from_sprite_lists()
            else:
                self.set_texture(self.textures[self.frame_index])

    def move_to_entity(self):
        entity_pos = Vector(self.entity.center_x, self.entity.center_y)
        new_pos = entity_pos + self.offset
        self.center_x = new_pos.x
        self.center_y = new_pos.y
