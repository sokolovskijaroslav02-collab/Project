import arcade
import os

class Overlay:
    def __init__(self, player):
        self.player = player
        self.health_texture = arcade.load_texture(
            os.path.join('graphics', 'health.png')
        )
        self.health_width = self.health_texture.width
        self.health_spacing = 4  # Расстояние между иконками
    
    def display(self, ui_camera):
        """
        Отображение оверлея (HP игрока)
        ui_camera - UI камера для правильного позиционирования
        """
        ui_camera.use()
        
        # Рисуем иконки здоровья
        for i in range(self.player.health):
            x = 10 + i * (self.health_width + self.health_spacing)
            y = 10
            
            self.health_texture.draw_scaled(
                x + self.health_width // 2,  # Центрируем по X
                y + self.health_width // 2,  # Центрируем по Y
                1.0  # Масштаб
            )
