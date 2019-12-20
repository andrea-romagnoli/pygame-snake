import copy
import random
import sqlite3
from enum import Enum

import pygame

# Constants
DIRECTION = Enum('Direction', 'UP RIGHT DOWN LEFT')
SCREEN_WIDTH = 390
SCREEN_HEIGHT = 300
DELTA = 30
BACKGROUND_COLOR = (0, 0, 0)
SNAKE_COLOR = (0, 128, 255)
FOOD_COLOR = (255, 0, 128)
FPS = 4
POINT_EAT = 10


def main():
    # PyGame initialisation
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    pygame.init()
    pygame.font.init()

    screen.fill(BACKGROUND_COLOR)
    text_title = pygame.font.SysFont('Consolas', 28)
    text_menu = pygame.font.SysFont('Consolas', 18)

    # Variables initialisation
    menu_item_selected = 'start'
    menu_main_items_y = {
        'start': 80,
        'exit': 100
    }
    letters_position = [
        140,
        150,
        160
    ]
    done = False
    menu_main = True
    menu_end = False
    menu_win = False
    first_iteration = True
    fps = 60
    highscore = None

    # Database initialisation
    db = Database('snake.db')
    db.create_table_if_not_exists('highscore', ['username varchar(3)',
                                                'score integer',
                                                'performed_at datetime DEFAULT CURRENT_TIMESTAMP'])

    if db.select_count_star_from('highscore') == 0:
        db.insert_into_values('highscore', ["'___'", '0', "datetime(CURRENT_TIMESTAMP, 'localtime')"])

    # Game loop
    while not done:

        # Event handling (i.e. keys pressing)
        direction = None
        enter = False
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    direction = DIRECTION.UP
                elif event.key == pygame.K_RIGHT:
                    direction = DIRECTION.RIGHT
                elif event.key == pygame.K_DOWN:
                    direction = DIRECTION.DOWN
                elif event.key == pygame.K_LEFT:
                    direction = DIRECTION.LEFT
                elif event.key == pygame.K_RETURN:
                    enter = True
            elif event.type == pygame.QUIT:
                done = True

        # Main menu
        if menu_main:
            if first_iteration:
                fps = 60
                highscore = db.get_highscore_tuple()
                first_iteration = False

            # Draw menu_main texts
            screen.fill((0, 0, 0))
            screen.blit(text_title.render('Snakeful Python', False, (0, 255, 0)), (30, 30))
            screen.blit(text_menu.render('start the game', False, (0, 255, 0)), (46, menu_main_items_y['start']))
            screen.blit(text_menu.render('exit', False, (0, 255, 0)), (46, menu_main_items_y['exit']))
            screen.blit(text_menu.render('highscore: ' + str(highscore[1]), False, (0, 255, 0)), (46, 180))
            screen.blit(text_menu.render('performed by: ' + str.upper(highscore[0]), False, (0, 255, 0)), (46, 200))

            # Change cursor position
            if direction == DIRECTION.UP:
                menu_item_selected = Utilities.dictionary_next_key(menu_main_items_y, menu_item_selected)
            elif direction == DIRECTION.DOWN:
                menu_item_selected = Utilities.dictionary_prev_key(menu_main_items_y, menu_item_selected)

            screen.blit(text_menu.render('>', False, (0, 255, 0)), (30, menu_main_items_y[menu_item_selected]))

            # Do selected action
            if enter:
                if menu_item_selected == 'start':
                    first_iteration = True
                    menu_main = False
                elif menu_item_selected == 'exit':
                    done = True

        # Game over without highscore
        elif menu_end:
            if first_iteration:
                first_iteration = False
                frame_show = 240
                fps = 60
            screen.fill((0, 0, 0))
            if frame_show <= 60 or (120 <= frame_show <= 180):
                screen.blit(text_title.render('Game Over', False, (0, 255, 0)), (130, 30))
            frame_show -= 1
            if frame_show < 0:
                first_iteration = True
                menu_main = True
                menu_end = False

        # Game over with highscore
        elif menu_win:
            if first_iteration:
                first_iteration = False
                fps = 60
                letter_selected = 0
                username = ['A', 'A', 'A']
            screen.fill((0, 0, 0))
            screen.blit(text_title.render('Game Over: Highscore!', False, (0, 255, 0)), (30, 30))
            screen.blit(text_menu.render('username: ', False, (0, 255, 0)), (46, 80))
            screen.blit(text_menu.render(username[0], False, (0, 255, 0)), (letters_position[0], 80))
            screen.blit(text_menu.render(username[1], False, (0, 255, 0)), (letters_position[1], 80))
            screen.blit(text_menu.render(username[2], False, (0, 255, 0)), (letters_position[2], 80))
            screen.blit(text_menu.render('<press enter to confirm>', False, (0, 255, 0)), (46, 120))

            if enter:
                db.update_highscore('highscore', ''.join(username), snake.score)
                first_iteration = True
                menu_main = True
                menu_win = False
            elif direction == DIRECTION.DOWN:
                username[letter_selected] = Utilities.list_next_key(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
                                                                    username[letter_selected])
            elif direction == DIRECTION.UP:
                username[letter_selected] = Utilities.list_prev_key(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
                                                                    username[letter_selected])
            elif direction == DIRECTION.RIGHT:
                letter_selected += 1
                if letter_selected > 2:
                    letter_selected = 0
            elif direction == DIRECTION.LEFT:
                letter_selected -= 1
                if letter_selected < 0:
                    letter_selected = 2

            screen.blit(text_menu.render('^', False, (0, 255, 0)), (letters_position[letter_selected], 100))



        # Game
        else:
            # Game initialisation
            if first_iteration:
                snake = Snake(120, 120, DIRECTION.RIGHT, DELTA, SNAKE_COLOR)
                food = Food(DELTA, FOOD_COLOR)
                food.generate(SCREEN_WIDTH, SCREEN_HEIGHT, (snake.x, snake.y), None)
                first_iteration = False
                fps = FPS

            # Game's logic
            else:
                snake_old_position = snake.move(direction)
                if food.is_eat_by_snake(snake.x, snake.y):
                    snake.add_score(POINT_EAT)
                    snake.increase_tail(snake_old_position)
                    food.generate(SCREEN_WIDTH, SCREEN_HEIGHT, (snake.x, snake.y), snake.tail)
                elif snake.is_outside_screen(SCREEN_WIDTH, SCREEN_HEIGHT):
                    _, score, _ = db.get_highscore_tuple()
                    first_iteration = True
                    if snake.score > score:
                        menu_win = True
                    else:
                        menu_end = True
                    continue
                elif snake.is_touching_tail():
                    _, score, _ = db.get_highscore_tuple()
                    first_iteration = True
                    if snake.score > score:
                        menu_win = True
                    else:
                        menu_end = True
                    continue

            # Draw
            screen.fill((0, 0, 0))
            snake.draw(screen)
            food.draw(screen)

        # Update the frame
        pygame.display.flip()
        clock.tick(fps)


class Utilities:

    @staticmethod
    def dictionary_next_key(dictionary, key):
        """
        Return next element in the dictionary, given the key.
        :param dictionary: Dictionary
        :param dictionary: Key
        :return: New element
        """
        return Utilities.__dictionary_get_key(dictionary, key, +1)

    @staticmethod
    def dictionary_prev_key(dictionary, key):
        """
        Return previous element in the dictionary, given the key.
        :param dictionary: Dictionary
        :param dictionary: Key
        :return: New element
        """
        return Utilities.__dictionary_get_key(dictionary, key, -1)

    @staticmethod
    def __dictionary_get_key(dictionary, key, sign):
        """
        Return the next or previous element in the dictionary, given the key and the direction.
        :param dictionary: Dictionary
        :param key: Key
        :param sign: Only the sign matters, specifies the direction (<0 previous key, >0 next key)
        :return: New element
        """
        menu_list = list(dictionary)
        index = menu_list.index(key) + sign
        if sign < 0 and index < 0:
            index = len(dictionary) - 1
        elif sign > 0 and index >= len(dictionary):
            index = 0
        elif sign == 0:
            raise ValueError('Non-zero value expected.')
        return menu_list[index]

    @staticmethod
    def list_prev_key(lista, value):
        """
        Return the previous element in the list, given the value.
        :param lista: List
        :param value: Value to search inside the list
        :return: New value
        """
        index = lista.index(value)
        if index == 0:
            index = len(lista) - 1
        else:
            index -= 1
        return lista[index]

    @staticmethod
    def list_next_key(lista, value):
        """
        Return the next element in the list, given the value.
        :param lista: List
        :param value: Value to search inside the list
        :return: New value
        """
        index = lista.index(value)
        if index == len(lista) - 1:
            index = 0
        else:
            index += 1
        return lista[index]


class Food:

    def __init__(self, delta, color):
        """
        :param delta: Side of the square
        :param color: An RGB tuple describing the color
        """
        self.x = -delta
        self.y = -delta
        self.delta = delta
        self.color = color

    def draw(self, screen):
        """
        Draw the Food.
        :param screen: Surface object of PyGame
        :return: Rect object of PyGame
        """
        pygame.draw.rect(screen, self.color, pygame.Rect(self.x, self.y, self.delta, self.delta))

    def generate(self, screen_width, screen_height, snake_head, snake_tail):
        """
        Generate a new food.
        :param screen_width: Total screen width
        :param screen_height: Total screen height
        :param snake_head: A tuple describing the position of Snake's head
        :param snake_tail: A list of tuples describing the positions of Snake's tail chunks
        :return: A tuple with the position (X,Y) of the generated food
        """
        if snake_tail:
            snake_tail_copy = copy.deepcopy(snake_tail)
            snake_tail_copy.append(snake_head)
        else:
            snake_tail_copy = [snake_head]
        while True:
            self.x = (random.randint(1, screen_width / self.delta) - 1) * self.delta
            self.y = (random.randint(1, screen_height / self.delta) - 1) * self.delta
            found = True
            for snake_chunk in snake_tail_copy:
                if self.x == snake_chunk[0] and self.y == snake_chunk[1]:
                    found = False
                    break
            if found:
                return self.x, self.y
        # TODO: If the screen is filled, the game is won

    def is_eat_by_snake(self, snake_x, snake_y):
        """
        Check a collision with Snake.
        :param snake_x: Position (axis X) of Snake
        :param snake_y: Position (axis Y) of Snake
        :return: If a collision occurred
        """
        if snake_x == self.x and snake_y == self.y:
            return True
        else:
            return False


class Database:

    def __init__(self, db_name):
        self.db_name = db_name
        self.db_conn = sqlite3.connect(self.db_name)
        self.db_cursor = self.db_conn.cursor()

    def create_table_if_not_exists(self, table, columns):
        self.db_cursor.execute("CREATE TABLE IF NOT EXISTS " + table + "(" + ','.join(columns) + ');')
        self.db_conn.commit()

    def select_count_star_from(self, table):
        self.db_cursor.execute("SELECT COUNT(*) FROM " + table + ";")
        return self.db_cursor.fetchone()[0]

    def insert_into_values(self, table, values):
        self.db_cursor.execute("INSERT INTO " + table + " VALUES (" + ','.join(values) + ");")
        self.db_conn.commit()

    def print_all_values_from(self, table):
        for record in self.db_cursor.execute("SELECT * FROM " + table + ";"):
            print("RECORD: " + ','.join([str(field) for field in record]))

    def update_highscore(self, table, username, score):
        self.db_cursor.execute(
            "UPDATE {} SET username='{}', score='{}', performed_at=datetime(CURRENT_TIMESTAMP, 'localtime');".format(
                table, username, score))
        self.db_conn.commit()

    def get_highscore_tuple(self):
        """
        Get the highest score.
        :return: A tuple with three values (username, score, performed_at)
        """
        self.db_cursor.execute("SELECT username, score, performed_at FROM highscore ORDER BY score DESC;")
        record = self.db_cursor.fetchone()
        return record[0], record[1], record[2]


class Snake:

    def __init__(self, x, y, direction_initial, delta, color):
        """
        :param x: Position (axis X)
        :param y: Position (axis Y)
        :param direction_initial: Initial direction of Snake (UP, RIGHT, DOWN, LEFT from 0 to 3)
        :param delta: Side of the square
        :param color: An RGB tuple describing the color
        :param score: The score
        """
        if x % delta != 0 or y % delta != 0:
            raise Exception('Initial snake position must be a multiple of delta.')
        self.x = x
        self.y = y
        self.tail = []
        self.direction_actual = direction_initial
        self.delta = delta
        self.color = color
        self.score = 0

    def draw(self, screen):
        """
        Draw the Snake.
        :param screen: Surface object of PyGame
        :return: Rect object of PyGame
        """
        pygame.draw.rect(screen, self.color, pygame.Rect(self.x, self.y, self.delta, self.delta))
        if self.tail:
            for tail_chunk in self.tail:
                pygame.draw.rect(screen, self.color, pygame.Rect(tail_chunk[0], tail_chunk[1], self.delta, self.delta))

    def move(self, direction_desired):
        """
        Move the Snake.
        :param direction_desired: Desired direction of Snake (UP, RIGHT, DOWN, LEFT from 0 to 3)
        :return: A tuple with the previous position (X,Y) of the Snake's head
        """
        old_position = self.x, self.y

        # Change direction if possible
        if direction_desired:
            if direction_desired == DIRECTION.UP:
                if self.direction_actual == DIRECTION.RIGHT:
                    self.direction_actual = DIRECTION.UP
                elif self.direction_actual == DIRECTION.LEFT:
                    self.direction_actual = DIRECTION.UP
            elif direction_desired == DIRECTION.RIGHT:
                if self.direction_actual == DIRECTION.DOWN:
                    self.direction_actual = DIRECTION.RIGHT
                elif self.direction_actual == DIRECTION.UP:
                    self.direction_actual = DIRECTION.RIGHT
            elif direction_desired == DIRECTION.DOWN:
                if self.direction_actual == DIRECTION.LEFT:
                    self.direction_actual = DIRECTION.DOWN
                elif self.direction_actual == DIRECTION.RIGHT:
                    self.direction_actual = DIRECTION.DOWN
            elif direction_desired == DIRECTION.LEFT:
                if self.direction_actual == DIRECTION.UP:
                    self.direction_actual = DIRECTION.LEFT
                elif self.direction_actual == DIRECTION.DOWN:
                    self.direction_actual = DIRECTION.LEFT

        # Record the move
        if self.direction_actual == DIRECTION.UP:
            self.y -= self.delta
        elif self.direction_actual == DIRECTION.RIGHT:
            self.x += self.delta
        elif self.direction_actual == DIRECTION.DOWN:
            self.y += self.delta
        else:
            self.x -= self.delta

        # Move the tail
        if self.tail:
            self.tail.pop(0)
            self.tail.append(old_position)

        return old_position

    def increase_tail(self, old_position):
        """
        Increase the tail size.
        :param old_position: A tuple with the previous position (X,Y) of the Snake's head
        :return: A list with all the tail positions
        """
        self.tail.append(old_position)

    def add_score(self, point):
        """
        Increase the score.
        :param point: The amount to increase the score
        :return: The new score
        """
        self.score += point
        return self.score

    def is_outside_screen(self, screen_width, screen_height):
        """
        Check if it is outside the allowed space.
        :param screen_width:
        :param screen_height:
        :return: If a trespassing occuirred
        """
        if self.y >= screen_height or self.y < 0 or self.x >= screen_width or self.x < 0:
            return True
        else:
            return False

    def is_touching_tail(self):
        """
        Check if it is touching its own tail.
        :return: If it is touching its own tail
        """
        for tail_chunk in self.tail:
            if (self.x, self.y) == tail_chunk:
                return True
        return False


if __name__ == '__main__':
    main()
