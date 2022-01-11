"""
game name: STRILENI PTAKU
name of author: FiVerka
game description: my own version of shot down birds

player's mission: shoot down as many light birds as possible in 30 seconds
player's rating:
    25 points for shooting down small objects (small flowers, small birds) or
    10 points for shooting down other objects (flowers, birds),
    points are deducted, if the player shoots down a dark bird
player's options:
    left-click on labels (switching between game scenes - frames)
    left-click on shooting objects (shoot down objects)
    right-lick or arrow UP (reload bullets)
    move the mouse from left to right or arrow LEFT and RIGHT
        (looking around the landscape), arrow DOWN (to stop looking around)
    key SPACE (the game round is temporarily stopped)

##############
game structure

FRAMES:
    START_GAME: main screen
        INSTRUCTIONS: screen with instructions
        ARE_YOU_SURE: frame with final question before closing the game window
    NEW_GAME: round of the game is running if NEW_GAME is True
        TIMER_3_2_1: countdown before the player is allowed to play
        TIMER: countdown during one game round
        PAUSE: to pause the game round
    END_GAME: end the round of the game -> START_GAME and so on

#################
program structure

imports
global VARIABLES
lists of shooting objects (flowers and birds)
dictionaries of colors, batches, groups, images, animations and sounds
functions: set_anchor(), reset()
variables (bird images & animations)

classes
MyWindow
    Background  # layers
        Landscape  # 1st (then small birds)
        Land  # 2nd (then small flowers, birds)
        Grass  # 3rd (then flowers)
        Frame  # 4th
            Start
            Instructions
            AreYouSure  # 5th
            End
            Pause
    Score
    Object  # objects with fixed coordinators to the window
        Bullet
    ShootingStableObject  # objects with fixed coordinators to the landscape
        Flower
        Cloud
    ShootingDynamicObject  # moving objects
        Bird
        DarkBird
    Timer

instances
event handlers
    draw, key_press, mouse_motion, mouse_press
    update_add_flower, update_add_bird, update_add_dark_bird, update_timer
"""

import pyglet
from pyglet import gl
from pathlib import Path
from random import randrange, choice

WIDTH = 800  # for window
HEIGHT = 742  # for window
CAPTION = "Střílení ptáků"  # for window
SCROLL_SPEED = 100  # for scrolling background
LENGTH_OF_ROUND = 30  # seconds
NUMBER_OF_FLOWERS = 20  # 60
NUMBER_OF_BIRDS = 4  # 20
NUMBER_OF_DARK_BIRDS = 1

# setting dt for pyglet.clock.schedule_interval
DT_BEFORE_NEW_GAME = 0.5
DT_NEW_GAME = 0.8  # float(f"0.{randrange(4, 10)}")

START_GAME = True  # main screen
INSTRUCTIONS = False  # screen with instructions
NEW_GAME = False  # round of the game is running if NEW_GAME is True
TIMER_3_2_1 = False  # countown before new game
TIMER = False  # countdown during the game
PAUSE = False  # de/activate of a pause during the game
ARE_YOU_SURE = False  # question before closing the game window
END_GAME = False  # end of the game

list_of_flowers = []
list_of_birds = []
list_of_dark_birds = []


class MouseStateHandler(dict):
    """
    Simple handler that tracks the state of buttons on the mouse. If a
    button is pressed then this handler holds a True value for it.
    """
    def on_mouse_press(self, x, y, button, modifiers):
        self[button] = True

    def on_mouse_release(self, x, y, button, modifiers):
        self[button] = False

    def __getitem__(self, mouse):
        return self.get(mouse, False)


# dictionary of used colors
colors = {
    "white": (255, 255, 255, 255),
    "red": (180, 0, 0, 255),
    "black": (0, 0, 0, 255),
    "brown": (63, 32, 6, 255),
    "yellow": (203, 190, 103, 255), }

# batch for pyglet.sprite.Sprite
batches = {
    key: pyglet.graphics.Batch() for key in [
        "main", "landscape", "land", "birds_small", "flowers_small", "grass",
        "flowers", "clouds", "birds", "bullets", "score", "start_game",
        "end_game", "instructions", "pause", "none", "cursor"]}

# group for pyglet.sprite.Sprite
groups = {
    item: pyglet.graphics.OrderedGroup(index) for index, item in enumerate([
        "background_landscape",
        "background_bird_small",
        "background_land_&_cloud",
        "background_flower_small",
        "foreground_bird",
        "foreground_grass",
        "foreground_flower",
        "foreground_gray_bullet",
        "foreground_bullet",
        "foreground_timer_&_score",
        "foreground_gray_frame",  # start/end game, pause, instructions
        "foreground_text_on_gray_frame",  # for text: -"-
        "foreground_cursor"])}


# loading images, animations and sounds into dictionaries
IMAGES_DIRECTORY = Path("media/images")
SOUNDS_DIRECTORY = Path("media/sounds")

images = {}
animations = {}
sounds = {}
for path in IMAGES_DIRECTORY.glob("*.png"):
    images[path.stem] = pyglet.image.load(path)
for path in IMAGES_DIRECTORY.glob("*.gif"):
    animations[path.stem] = pyglet.image.load_animation(path)
for path in SOUNDS_DIRECTORY.glob("*.wav"):
    sounds[path.stem] = pyglet.media.load(path, streaming=False)


# creating a function for setting the anchor for images and animations
# and application of the function
def set_anchor(img, x, y):
    """
    function for setting the anchor for images and animations
    """
    if isinstance(img, pyglet.image.Animation):
        for frame in img.frames:
            frame.image.anchor_x = x
            frame.image.anchor_y = y
    else:
        img.anchor_x = x
        img.anchor_y = y


for image in images.values():
    set_anchor(img=image, x=image.width // 2, y=image.height // 2)

for animation in animations.values():
    set_anchor(
        img=animation,
        x=animation.get_max_width() // 2,
        y=animation.get_max_height() // 2)

# assigning a variable to some images to differentiate them
# according to the direction of flight and the color of the bird
light_bird_flies_to_right = animations["light_bird"]
light_bird_flies_to_left = light_bird_flies_to_right.get_transform(flip_x=True)

falling_light_bird_flies_to_right = images["falling_light_bird"]
falling_light_bird_flies_to_left = images["falling_light_bird_flip"]

dark_bird_flies_to_right = animations["dark_bird"]
dark_bird_flies_to_left = dark_bird_flies_to_right.get_transform(flip_x=True)

falling_dark_bird_flies_to_right = images["falling_dark_bird"]
falling_dark_bird_flies_to_left = images["falling_dark_bird_flip"]


def reset():
    """
    The function is activated as soon as the player left-clicks on the "OK"
    in frame "END_GAME", then frame "START_GAME" is displayed.
    Reset applies to the list of bullets (it contains 8 bullets), score,
    timers, updating the position of the clouds (coordinator x),
    delete the contents of the set_of_moves and set "stop" as default value
    (via window.reset()).
    """
    global list_of_gray_bullets, list_of_bullets
    global cloud_left_a, cloud_left_b, cloud_right_a, cloud_right_b

    for item in window, timer_3_2_1, timer, score:
        item.reset()

    list_of_gray_bullets = [
        Bullet(images["bullet_gray"], 37 * num) for num in range(1, 9)]
    list_of_bullets = [
        Bullet(images["bullet"], 37 * num) for num in range(1, 9)]

    for cloud in cloud_left_a, cloud_left_b, cloud_right_a, cloud_right_b:
        cloud.pic.x, cloud.pic.y = cloud.value_x, cloud.value_y


class MyWindow(pyglet.window.Window):
    def __init__(self):
        super(MyWindow, self).__init__(
            width=WIDTH, height=HEIGHT, caption=CAPTION,
            resizable=False, fullscreen=False)
        # self.set_mouse_visible(visible=False)
        self.set_exclusive_mouse(True)
        self.set_icon(images["bird_icon"])
        self.clear()

        # set a key and mouse state handler
        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.mouse_buttons = MouseStateHandler()
        self.push_handlers(self.mouse_buttons)
        self.mouse_moves = {"left": False, "middle": True, "right": False}
        # examples of the use of handlers in practice:
        # if self.keys[pyglet.window.key.SPACE]: pass
        # if self.mouse_buttons[pyglet.window.mouse.LEFT]: pass
        # if self.mouse_moves["middle"]: pass

        # from key_press and mouse_motion for move background
        self.set_of_moves = set()

        # default mouse cursor position
        self.mouse_position = {"x": WIDTH / 2, "y": HEIGHT / 2}

        # set up the cursor
        self.cursor = pyglet.sprite.Sprite(
            img=images["mini_target"],
            x=self.mouse_position["x"],
            y=self.mouse_position["y"],
            batch=batches["cursor"],
            group=groups["foreground_cursor"])

        # dict for saving coordinators when the left mouse button is pressed
        self.left_mouse_button_coordinates = {"x": None, "y": None}

        # to freeze the mouse coordinators during the pause to avoid cheating
        self.remeber_actual_position_of_mouse_cursor = True
        self.mouse_position_before_pause = {"x": None, "y": None}
        self.set_up_actual_position_of_mouse_cursor = False

        pyglet.clock.schedule_interval(self.update_cursor, .01)
        # pyglet.clock.schedule_interval(self.update, 0.5)

    def reset(self):
        """
        during the reset: the game window is cleared, as well as
        the default motion value is set in mouse_moves and set_of_moves:
        do not move!
        """
        self.clear()
        self.mouse_moves = {"left": False, "middle": True, "right": False}
        self.set_of_moves.clear()
        self.set_of_moves.add("stop")

    def update_cursor(self, dt):
        """
        updating mouse cursor coordinators x and y
        """
        self.cursor.x = self.mouse_position["x"]
        self.cursor.y = self.mouse_position["y"]

    def update(self, dt):
        pass

    def key_press(self, symbol, modifier):
        """
        it is a key function for storing and updating the instruction
        in the set_of_moves based on the arrow keys pressed:
        e.g. the key right arrow is pressed, so "right" is saved
        in the set_of_moves
        """
        # update set_of_moves
        # stop-right and stop-left: for zero speed for stable objects (flowers)
        # we have reached the end of the picture "landscape"
        if TIMER:  # after NEW_GAME after TIMER_3_2_1...
            if not PAUSE:
                # look around the landscape to the right when the key
                # RIGHT is pressed
                if symbol == pyglet.window.key.RIGHT:
                    if "stop-right" in self.set_of_moves:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("stop-right")
                    else:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("right")
                # look around the landscape to the left when the key
                # LEFT is pressed
                if symbol == pyglet.window.key.LEFT:
                    if "stop-left" in self.set_of_moves:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("stop-left")
                    else:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("left")
                # stand still (do not look around the landscape) when the key
                # DOWN is pressed
                if symbol == pyglet.window.key.DOWN:
                    if "stop-right" in self.set_of_moves:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("stop-right")
                    elif "stop-left" in self.set_of_moves:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("stop-left")
                    else:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("stop")

                # the cursor position is displayed in the middle of the window
                if symbol == pyglet.window.key.BACKSPACE:
                    self.mouse_position = {"x": WIDTH / 2, "y": HEIGHT / 2}
                    self.set_of_moves.clear()
                    self.set_of_moves.add("stop")

    def mouse_motion(self, x, y, dx, dy):
        """
        the function adjusts the mouse movement behavior during the game,
        the mouse movement is frozen during the PAUSE or TIMER_3_2_1
        to avoid cheating,
        the mouse cursor cannot leave the game window,
        it is a key function for storing and updating the instruction
        in the set_of_moves and mouse_moves according to the behavior
        of the mouse movement:
        e.g. the mouse cursor is located on the right of the game window, so
        "right" is saved in the set_of_moves and "True" in mouse_moves["right"]
        """
        self.mouse_position["x"] += dx
        self.mouse_position["y"] += dy

        # steps for freeze the cursor to avoid cheating during PAUSE
        # step 1)
        if TIMER:
            if self.set_up_actual_position_of_mouse_cursor:
                self.mouse_position = {
                    "x": self.mouse_position_before_pause["x"],
                    "y": self.mouse_position_before_pause["y"]}
                self.remeber_actual_position_of_mouse_cursor = True
                self.set_up_actual_position_of_mouse_cursor = False
        # step 2)
        if PAUSE:
            if self.remeber_actual_position_of_mouse_cursor:
                self.mouse_position_before_pause = {
                    "x": self.mouse_position["x"],
                    "y": self.mouse_position["y"]}
                self.remeber_actual_position_of_mouse_cursor = False
                self.set_up_actual_position_of_mouse_cursor = True

        # the cursor position does not leave the window
        if self.cursor.x < 0:
            self.mouse_position["x"] = 0
        if self.cursor.x > WIDTH:
            self.mouse_position["x"] = WIDTH
        if self.cursor.y < 0:
            self.mouse_position["y"] = 0
        if self.cursor.y > HEIGHT:
            self.mouse_position["y"] = HEIGHT

        if TIMER_3_2_1:  # freeze the cursor to avoid cheating
            self.mouse_position = {"x": WIDTH / 2, "y": HEIGHT / 2}
            self.set_of_moves.clear()
            self.set_of_moves.add("stop")

        # update mouse_moves and set_of_moves
        # stop-right and stop-left: for zero speed for flowers,
        # we have reached the end of the picture "landscape"
        if TIMER:  # after NEW_GAME after TIMER_3_2_1...
            if not PAUSE:
                # look around the landscape to the right when the mouse
                # cursor is to the right of the window
                if (WIDTH - 20) < self.cursor.x:
                    self.mouse_moves["right"] = True
                    self.mouse_moves["middle"] = False
                    self.mouse_moves["left"] = False
                    if "stop-right" in self.set_of_moves:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("stop-right")
                    else:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("right")
                # look around the landscape to the left when the mouse
                # cursor is to the left of the window
                elif self.cursor.x < 20:
                    self.mouse_moves["right"] = False
                    self.mouse_moves["middle"] = False
                    self.mouse_moves["left"] = True
                    if "stop-left" in self.set_of_moves:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("stop-left")
                    else:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("left")
                # stand still (do not look around the landscape) when the mouse
                # cursor is in the middle of the window
                else:
                    self.mouse_moves["right"] = False
                    self.mouse_moves["middle"] = True
                    self.mouse_moves["left"] = False
                    if "stop-right" in self.set_of_moves:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("stop-right")
                    elif "stop-left" in self.set_of_moves:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("stop-left")
                    else:
                        self.set_of_moves.clear()
                        self.set_of_moves.add("stop")

    def mouse_press(self, x, y, button, modifiers):
        """
        the function saves the coordinators x and y
        when the left mouse button is pressed
        """
        self.left_mouse_button_coordinates["x"] = self.mouse_position["x"]
        self.left_mouse_button_coordinates["y"] = self.mouse_position["y"]


class Background(MyWindow):
    def __init__(self, image, value_x, value_y, group):
        self.image = image
        self.value_x = value_x
        self.value_y = value_y
        self.group = group
        self.pic = self.set_sprite()

        # set speed for scroll background
        self.step = SCROLL_SPEED
        self.speed_scroll = {"x": 0, "y": 0}
        self.speed = self.step

        pyglet.clock.schedule_interval(self.update, 1/30)

    def set_sprite(self, batch=batches["main"]):
        return pyglet.sprite.Sprite(
            img=self.image,
            x=self.value_x,
            y=self.value_y,
            batch=batch,
            group=self.group)

    def update(self, dt):
        """
        function determines the behavior of the background based
        on set_of_moves:
        e.g. the background moves to the right, when "right" in set_of_moves,
        the background can only be moved during the game round,
        the breakpoint is activated when the end of the image representing
        the background is reached
        """
        # freezing the possibility of looking around the landscape
        if START_GAME:
            self.pic.x = self.value_x
            self.pic.y = self.value_y
            self.speed_scroll["x"] = 0

        if TIMER:  # after NEW_GAME after TIMER_3_2_1...
            # freezing the possibility of looking around the landscape
            if PAUSE:
                self.speed_scroll["x"] = 0
            else:
                # setting the speed of looking around the landscape
                # according to what is stored in set_of_moves
                if "stop-left" in window.set_of_moves:
                    if "right" in window.set_of_moves:
                        self.speed_scroll["x"] = -self.speed
                elif "stop-right" in window.set_of_moves:
                    if "left" in window.set_of_moves:
                        self.speed_scroll["x"] = self.speed
                else:
                    if "stop" in window.set_of_moves:
                        self.speed_scroll["x"] = 0
                    if "right" in window.set_of_moves:
                        self.speed_scroll["x"] = -self.speed
                    if "left" in window.set_of_moves:
                        self.speed_scroll["x"] = self.speed
        if END_GAME:
            # freezing the possibility of looking around the landscape
            self.speed_scroll["x"] = 0

        self.pic.x += dt * self.speed_scroll["x"]

        # set stop scroll for landscape (background)
        # we have reached the end of the picture
        if self.pic.x > (self.pic.width // 2):
            self.pic.x = self.pic.width // 2
            window.set_of_moves.clear()
            window.set_of_moves.add("stop-left")
        if self.pic.x < (window.width - self.pic.width // 2):
            self.pic.x = (window.width - self.pic.width // 2)
            window.set_of_moves.clear()
            window.set_of_moves.add("stop-right")


class Landscape(Background):
    def __init__(self):
        super(Landscape, self).__init__(
            image=images["landscape"],
            value_x=window.width // 2,
            value_y=window.height // 2,
            group=groups["background_landscape"])
        self.pic = self.set_sprite(batch=batches["landscape"])


class Land(Background):
    def __init__(self):
        super(Land, self).__init__(
            image=images["land"],
            value_x=window.width // 2,
            value_y=images["land"].height // 2,
            group=groups["background_land_&_cloud"])
        self.pic = self.set_sprite(batch=batches["land"])


class Grass(Background):
    def __init__(self):
        super(Grass, self).__init__(
            image=images["grass"],
            value_x=window.width // 2,
            value_y=images["grass"].height // 2,
            group=groups["foreground_grass"])
        self.pic = self.set_sprite(batch=batches["grass"])


class Score(MyWindow):
    def __init__(self):
        self.number = 0
        self.score_label = self.create_label()

        pyglet.clock.schedule_interval(self.update, 1/30)

    def create_label(self):
        return pyglet.text.Label(
            text=str(self.number),
            font_name="Arial",
            font_size=40,
            bold=True,
            color=colors["black"],
            x=20,
            y=(HEIGHT - 40),
            anchor_x="left",
            anchor_y="center",
            batch=batches["score"],
            group=groups["foreground_timer_&_score"])

    def reset(self):
        """
        the default score is zero
        """
        self.number = 0

    def update(self, dt):
        """
        the score is regularly updated during the game round
        """
        self.score_label.text = str(self.number)


class Object(MyWindow):
    def __init__(self, image, value_x, value_y, group):
        self.image = image
        self.value_x = value_x
        self.value_y = value_y
        self.group = group
        self.pic = self.set_sprite()

    def set_sprite(self, batch=batches["main"]):
        return pyglet.sprite.Sprite(
            img=self.image,
            x=self.value_x,
            y=self.value_y,
            batch=batch,
            group=self.group)


class Bullet(Object):
    def __init__(self, image, value_x):
        self.image = image
        self.value_x = value_x
        super(Bullet, self).__init__(
            image=self.image,
            value_x=self.value_x,
            value_y=40,
            group=groups["foreground_bullet"] if self.image == images[
                "bullet"] else groups["foreground_gray_bullet"])
        self.pic = self.set_sprite(batches["bullets"])
        self.pic.scale = 0.31

        self.down = False

    def falling_bullet(self, dt):
        """
        the function sets coordinator y = the minimum where the bullet
        must fall down so that it is outside the visible area
        of the playing field
        """
        # for gray bullet
        if self.pic.y >= -80:
            self.pic.y -= 10

    def check_bullet(self):
        """
        the function is called when a player clicks the left mouse button
        during a game round and len(list_of_gray_bullets) > 0,
        this function calls the function falling_bullet() and sets how often
        it will be called before the bullet disappears
        from the visible playing area
        """
        pyglet.clock.schedule_interval(self.falling_bullet, 1/60)


class ShootingStableObject(MyWindow):
    def __init__(self, image, value_x, value_y, group):
        self.image = image
        self.value_x = value_x
        self.value_y = value_y
        self.group = group
        self.pic = self.set_sprite()

        self.alive = True

        # set 0 speed for object during scroll background
        self.step = SCROLL_SPEED
        self.speed_scroll = {"x": 0, "y": 0}
        self.speed = self.step

        pyglet.clock.schedule_interval(self.update, 1/30)

    def set_sprite(self, batch=batches["main"]):
        return pyglet.sprite.Sprite(
            img=self.image,
            x=self.value_x,
            y=self.value_y,
            batch=batch,
            group=self.group)

    def check_shot(self, version):
        """
        check whether the object was shot down (the player left-clicked
        on the object and len(list_of_bullets) > 0) according to the set
        range (different for object size), if the object is shot down,
        it returns "True" and the variable "self.alive" is set to "False"
        """
        left_button_x = window.left_mouse_button_coordinates["x"]
        left_button_y = window.left_mouse_button_coordinates["y"]
        pic_x, pic_y = self.pic.x, self.pic.y
        pic_width, pic_height = self.pic.width, self.pic.height
        value_width = (
            ((pic_width // 7) * 2) if version == "small" else (
                ((pic_width // 8) * 2)))
        value_heigth = (
            ((pic_height // 7) * 2) if version == "small" else (
                ((pic_height // 8) * 2)))
        if left_button_x in range(
                int(pic_x - value_width),
                int(pic_x + value_width)) and (
                left_button_y in range(
                int(pic_y - value_heigth),
                int(pic_y + value_heigth))):
            self.alive = False
            return True
        else:
            return False

    def update(self, dt):
        """
        the function updates the position of the stable object
        """
        # the location of the object on the playing area is stable,
        # it is important to maintain its stable position only when
        # looking around the landscape (this is when the "right" or "left"
        # is set in the set_of_moves)
        if TIMER:  # after NEW_GAME after TIMER_3_2_1...
            if PAUSE:
                self.speed_scroll["x"] = 0
            else:
                if "stop" in window.set_of_moves:
                    self.speed_scroll["x"] = 0
                if "stop-left" in window.set_of_moves:
                    self.speed_scroll["x"] = 0
                if "stop-right" in window.set_of_moves:
                    self.speed_scroll["x"] = 0
                if "right" in window.set_of_moves:
                    self.speed_scroll["x"] = -self.speed
                if "left" in window.set_of_moves:
                    self.speed_scroll["x"] = self.speed
        if END_GAME:
            self.speed_scroll["x"] = 0

        self.pic.x += dt * self.speed_scroll["x"]


class Flower(ShootingStableObject):
    def __init__(self):
        self.image = choice([images["flower_small"], choice([
            images["flower1"], images["flower2"],
            images["flower3"], images["flower4"]])])
        super(Flower, self).__init__(
            image=self.image,
            value_x=randrange(
                int(landscape.pic.x - 620), int(landscape.pic.x + 620)),
            value_y=randrange(
                int(landscape.pic.y - 180),
                int(landscape.pic.y + 30)) if self.image == images[
                    "flower_small"] else randrange(
                        int(landscape.pic.y - 280),
                        int(landscape.pic.y - 180)),
            group=groups["background_flower_small"] if self.image == images[
                "flower_small"] else groups["foreground_flower"])
        self.pic = self.set_sprite(batch=batches[
            "flowers_small"] if self.image == images[
            "flower_small"] else batches["flowers"])


class Cloud(ShootingStableObject):
    def __init__(self, image, value_x, value_y):
        self.image = image
        self.value_x = value_x
        self.value_y = value_y
        super(Cloud, self).__init__(
            image=self.image,
            value_x=self.value_x,
            value_y=self.value_y,
            group=groups["background_land_&_cloud"])
        self.pic = self.set_sprite(batch=batches["clouds"])

        # set default attributes for move functions (move_up, move_down, move)
        self.cloud_left_value_y = 630
        self.cloud_right_value_y = 658
        self.movevement_of_cloud = True
        if self.image == images["cloud_left"]:
            self.value = self.cloud_left_value_y
        elif self.image == images["cloud_right"]:
            self.value = self.cloud_right_value_y

        pyglet.clock.schedule_interval(self.move, 1/10)

    def move_up(self, dt):
        """
        determining the coordinator y for moving the cloud up,
        the function instructs to change the direction of movement
        when the maximum value of y is reached
        """
        if self.pic.y <= self.value + 7:
            self.pic.y += 1
        if self.pic.y >= self.value + 8:
            self.movevement_of_cloud = False  # change of direction of movement

    def move_down(self, dt):
        """
        determining the coordinator y for moving the cloud down,
        the function instructs to change the direction of movement
        when the minimum value of y is reached
        """
        if self.pic.y >= self.value - 7:
            self.pic.y -= 1
        if self.pic.y <= self.value - 8:
            self.movevement_of_cloud = True  # change of direction of movement

    def move(self, dt):
        """
        the function coordinates the behavior of the cloud:
        the cloud is at the same position x, but moves up and down,
        functions move_up() and move_down() are called alternately
        according to the direction of movement
        """
        if self.movevement_of_cloud:
            self.move_up(dt)
        else:
            self.move_down(dt)


class ShootingDynamicObject(MyWindow):
    def __init__(self, image, value_x, value_y, group):
        self.image = image
        self.value_x = value_x
        self.value_y = value_y
        self.group = group
        self.pic = self.set_sprite()

        self.alive = True

        # set speed for object during scroll background
        if self.direction_of_flight["to_right"]:
            self.step = SCROLL_SPEED // 2
        if self.direction_of_flight["to_left"]:
            self.step = -(SCROLL_SPEED // 2)

        self.speed_scroll = {"x": self.step, "y": 0}
        self.speed = self.step

        pyglet.clock.schedule_interval(self.update, 1/30)

    def set_sprite(self, batch=batches["main"]):
        return pyglet.sprite.Sprite(
            img=self.image,
            x=self.value_x,
            y=self.value_y,
            batch=batch,
            group=self.group)

    def update(self, dt):
        """
        the function periodically updates the behavior of the dynamic object
        based on the background behavior -> based on what is stored in
        set_of_moves
        """
        # adjusting the speed of the dynamic object's movement during
        # background scrolling based on what is in the set_of_moves
        # at the same time the direction of flight is differentiated
        if not PAUSE:
            if "stop" in window.set_of_moves:
                self.speed_scroll["x"] = self.speed
            if "stop-left" in window.set_of_moves:
                self.speed_scroll["x"] = self.speed
            if "stop-right" in window.set_of_moves:
                self.speed_scroll["x"] = self.speed
            if "right" in window.set_of_moves:
                if self.direction_of_flight["to_right"]:
                    self.speed_scroll["x"] = -self.speed
                if self.direction_of_flight["to_left"]:
                    self.speed_scroll["x"] = 3 * self.speed
            if "left" in window.set_of_moves:
                if self.direction_of_flight["to_right"]:
                    self.speed_scroll["x"] = 3 * self.speed
                if self.direction_of_flight["to_left"]:
                    self.speed_scroll["x"] = -self.speed
            if landscape.speed_scroll["x"] == 0:
                self.speed_scroll["x"] = self.speed
        if PAUSE:
            self.speed_scroll["x"] = 0

        self.pic.x += dt * self.speed_scroll["x"]

    def check_position_pic_x(self):
        """
        to identify when the moving object leaves the visible playing field
        """
        if not START_GAME:
            if self.direction_of_flight["to_right"]:
                if self.scale == 4/10:
                    return (self.pic.x >= (landscape.pic.x + 720))
                if self.scale == 2/10:
                    return (self.pic.x >= (landscape.pic.x + 660))
            if self.direction_of_flight["to_left"]:
                if self.scale == 4/10:
                    return (self.pic.x <= (landscape.pic.x - 720))
                if self.scale == 2/10:
                    return (self.pic.x <= (landscape.pic.x - 660))
        else:
            if self.direction_of_flight["to_right"]:
                if self.scale == 4/10:
                    return (self.pic.x >= (landscape.pic.x + 460))
                if self.scale == 2/10:
                    return (self.pic.x >= (landscape.pic.x + 420))
            if self.direction_of_flight["to_left"]:
                if self.scale == 4/10:
                    return (self.pic.x <= (landscape.pic.x - 460))
                if self.scale == 2/10:
                    return (self.pic.x <= (landscape.pic.x - 420))

    def check_position_pic_y(self):
        """
        to identify when the moving object leaves the visible playing field
        and then is deleted
        """
        self.pos_y = 300 if self.scale == 2/10 else 100  # for scale 4/10
        if self.pic.y <= self.pos_y:
            pyglet.clock.unschedule(self.rotation_object)
            pyglet.clock.unschedule(self.falling_object)
            pyglet.clock.unschedule(self.update)

    def check_shot(self):
        """
        check whether the object was shot down (the player left-clicked
        on the object and len(list_of_bullets) > 0) according to the set
        range, if the object is shot down, it returns "True" and
        the variable "self.alive" is set to "False", at the same time
        the function "change_object_image_after_shot_down()" is called
        """
        left_button_x = window.left_mouse_button_coordinates["x"]
        left_button_y = window.left_mouse_button_coordinates["y"]
        bird_x, bird_y = self.pic.x, self.pic.y
        bird_width = self.pic.width
        bird_height = self.pic.height
        if left_button_x in range(
                int(bird_x - (((bird_width // 2) // 5) * 2)),
                int(bird_x + (((bird_width // 2) // 5) * 2))) and (
                left_button_y in range(
                int(bird_y - (((bird_height // 2) // 10) * 2)),
                int(bird_y + (((bird_height // 2) // 8) * 2)))):
            self.alive = False
            pyglet.clock.schedule_once(
                self.change_object_image_after_shot_down, 0.1)
            return True
        else:
            return False

    def rotation_object(self, dt):
        """
        rotation of the object during the shooting down of the object and
        its fall down outside the visible area of the playing field
        """
        if not PAUSE:
            if self.pic.rotation <= 360:
                self.pic.rotation += 10

    def falling_object(self, dt):
        """
        the function is called after shooting down the dynamic object and
        changing its image, the function rotation_object() is
        called while the object is falling down, at the same time,
        the behavior of the object changes during background scrolling:
        now it is a stable object with zero speed for coordinator x,
        his position is adjusted only while looking around the landscape
        (only "right" or "left" is in the set_of_moves), at the same time,
        the function check_position_pic_y() is called to control when
        the dynamic object disappears from the visible playing area
        so that it can be removed
        """
        pyglet.clock.schedule_interval(self.rotation_object, 0.06)
        self.speed = SCROLL_SPEED // 3

        if not PAUSE:
            if self.pic.y > -60:
                self.pic.y -= 10
            if "stop-left" in window.set_of_moves:
                self.speed_scroll["x"] = 0
            if "stop-right" in window.set_of_moves:
                self.speed_scroll["x"] = 0
            if "stop" in window.set_of_moves:
                self.speed_scroll["x"] = 0
            if "right" in window.set_of_moves:
                self.speed_scroll["x"] = -self.speed
            if "left" in window.set_of_moves:
                self.speed_scroll["x"] = self.speed

        self.pic.x += dt * self.speed_scroll["x"]
        self.check_position_pic_y()

    def change_object_image_after_shot_down(self, t):
        """
        upload a new image after shooting down the dynamic object,
        at the same time the function "falling_object()" is called
        """
        self.pic = pyglet.sprite.Sprite(
            img=self.pic_of_falling_bird,
            x=window.left_mouse_button_coordinates["x"],
            y=window.left_mouse_button_coordinates["y"],
            batch=self.batch,
            group=self.group)
        self.pic.scale = self.scale
        self.pic.rotation = 180
        pyglet.clock.schedule_interval(self.falling_object, 1/60)

    def set_x_for_straight_flight(self):
        """
        to identify the coordinator x from which the bird will fly,
        the bird flies from behind the invisible playing field
        """
        if not START_GAME:
            if self.direction_of_flight["to_right"]:
                if self.scale == 4/10:
                    self.value_x = int(landscape.pic.x - 720)
                if self.scale == 2/10:
                    self.value_x = int(landscape.pic.x - 660)
            if self.direction_of_flight["to_left"]:
                if self.scale == 4/10:
                    self.value_x = int(landscape.pic.x + 720)
                if self.scale == 2/10:
                    self.value_x = int(landscape.pic.x + 660)
        else:
            if self.direction_of_flight["to_right"]:
                if self.scale == 4/10:
                    self.value_x = int(landscape.pic.x - 460)
                if self.scale == 2/10:
                    self.value_x = int(landscape.pic.x - 420)
            if self.direction_of_flight["to_left"]:
                if self.scale == 4/10:
                    self.value_x = int(landscape.pic.x + 460)
                if self.scale == 2/10:
                    self.value_x = int(landscape.pic.x + 420)
        return self.value_x


class Bird(ShootingDynamicObject):
    def __init__(self):
        self.image = choice(
             [light_bird_flies_to_right, light_bird_flies_to_left])
        self.scale = choice([2/10, 4/10])
        self.group = groups[
            "background_bird_small"] if self.scale == 2/10 else (
                groups["foreground_bird"])
        self.batch = batches["birds"] if self.scale == 4/10 else (
            batches["birds_small"])

        # determination of flight direction and image of falling bird
        if self.image == light_bird_flies_to_right:
            self.direction_of_flight = {"to_right": True, "to_left": False}
            self.pic_of_falling_bird = falling_light_bird_flies_to_right
        if self.image == light_bird_flies_to_left:
            self.direction_of_flight = {"to_right": False, "to_left": True}
            self.pic_of_falling_bird = falling_light_bird_flies_to_left

        super(Bird, self).__init__(
            image=self.image,
            value_x=self.set_x_for_straight_flight(),  # self.value_x,
            value_y=randrange(
                int(landscape.pic.y - 180),
                int(landscape.pic.y + 280)) if self.scale == 4/10 else (
                randrange(int(landscape.pic.y + 80),
                          int(landscape.pic.y + 280))),
            group=self.group)
        self.pic = self.set_sprite(
            batch=self.batch)
        self.pic.scale = self.scale


class DarkBird(ShootingDynamicObject):
    def __init__(self):
        self.image = choice(
             [dark_bird_flies_to_right, dark_bird_flies_to_left])
        self.scale = choice([2/10, 4/10])
        self.group = groups[
            "background_bird_small"] if self.scale == 2/10 else (
                groups["foreground_bird"])
        self.batch = batches["birds"] if self.scale == 4/10 else (
            batches["birds_small"])

        # determination of flight direction and image of falling bird
        if self.image == dark_bird_flies_to_right:
            self.direction_of_flight = {"to_right": True, "to_left": False}
            self.pic_of_falling_bird = falling_dark_bird_flies_to_right
        if self.image == dark_bird_flies_to_left:
            self.direction_of_flight = {"to_right": False, "to_left": True}
            self.pic_of_falling_bird = falling_dark_bird_flies_to_left

        super(DarkBird, self).__init__(
            image=self.image,
            value_x=self.set_x_for_straight_flight(),  # self.value_x,
            value_y=randrange(
                int(landscape.pic.y - 180),
                int(landscape.pic.y + 280)) if self.scale == 4/10 else (
                randrange(int(landscape.pic.y + 80),
                          int(landscape.pic.y + 280))),
            group=self.group)
        self.pic = self.set_sprite(
            batch=self.batch)
        self.pic.scale = self.scale


class Frame(Background):
    def __init__(self):
        super(Frame, self).__init__(
            image=images["gray_frame"],
            value_x=window.width // 2,
            value_y=window.height // 2,
            group=groups["foreground_gray_frame"])
        # it is important to enter the following code in the subclass
        # to display the gray frame:
        # super().__init__()
        # self.pic = self.set_sprite(batch=batches["name_of_batch"])

    def create_label(
            self, text, font_size, value_y, color=colors["black"],
            value_x=(WIDTH // 2), width=None, height=None,
            anchor_x="center", batch=None, group=None):
        return pyglet.text.Label(
            text,
            font_name="Arial",
            font_size=font_size,
            bold=True,
            color=color,
            x=value_x,
            y=value_y,
            width=width,
            height=height,
            anchor_x=anchor_x,
            batch=batch,
            group=group)

    def check_click(self, text, version):
        """
        Check mouse left click on label,
        if the label is centered, version == "middle",
        if the label is at the top right, version == "top_right".
        """
        left_button_x = window.left_mouse_button_coordinates["x"]
        left_button_y = window.left_mouse_button_coordinates["y"]
        label_x, label_y = text.x, text.y
        label_width, label_height = text.width, text.height
        if version == "middle":
            if left_button_x in range(
                    label_x - (label_width // 2),
                    label_x + (label_width // 2)) and (
                    left_button_y in range(
                    label_y,
                    label_y + label_height)):
                return True
        if version == "top_right":
            if left_button_x in range(
                    label_x - label_width,
                    label_x) and (
                    left_button_y in range(
                    label_y,
                    label_y + label_height)):
                return True

    def mouse_motion(self, x, y, dx, dy, text, version):
        """
        Check mouse over the label,
        if the label is centered, version == "middle",
        if the label is at the top right, version == "top_right".
        """
        label_x, label_y = text.x, text.y
        label_width, label_height = text.width, text.height
        if version == "middle":
            if window.mouse_position["x"] in range(
                    label_x - (label_width // 2),
                    label_x + (label_width // 2)) and (
                    window.mouse_position["y"] in range(
                    label_y,
                    label_y + label_height)):
                text.color = colors["yellow"]
                return True
            else:
                text.color = colors["black"]
        if version == "top_right":
            if window.mouse_position["x"] in range(
                    label_x - label_width,
                    label_x) and (
                    window.mouse_position["y"] in range(
                    label_y,
                    label_y + label_height)):
                text.color = colors["yellow"]
                return True
            else:
                text.color = colors["black"]


class Start(Frame):
    def __init__(self):
        self.text1 = "STŘÍLENÍ PTÁKŮ"
        self.text2 = "START"
        self.text3 = "KONEC"
        self.text4 = "INSTRUKCE"
        self.text5 = "Pro zahájení nové hry klikněte na \"START\"."

        super().__init__()
        self.pic = self.set_sprite(batch=batches["start_game"])

        self.start_text1 = self.create_label(
            text=self.text1, font_size=40, color=colors["brown"],
            value_y=((window.height // 7) * 5), batch=batches["start_game"],
            group=groups["foreground_text_on_gray_frame"])
        self.start_text2 = self.create_label(
            text=self.text2, font_size=40, value_y=((window.height // 10) * 5),
            width=180, height=40, batch=batches["start_game"],
            group=groups["foreground_text_on_gray_frame"])
        self.start_text3 = self.create_label(
            text=self.text3, font_size=40, value_y=((window.height // 10) * 3),
            width=180, height=40, batch=batches["start_game"],
            group=groups["foreground_text_on_gray_frame"])
        self.start_text4 = self.create_label(
            text=self.text4, font_size=20, value_x=(window.width - 20),
            value_y=(window.height - 40), width=158, height=20,
            anchor_x="right", batch=batches["start_game"],
            group=groups["foreground_text_on_gray_frame"])
        self.start_text5 = self.create_label(
            text=self.text5, font_size=20, value_y=40,
            batch=batches["start_game"],
            group=groups["foreground_text_on_gray_frame"])

    def check_click_to_start(self):
        """
        check mouse left click on label "START"
        """
        if super().check_click(self.start_text2, "middle"):
            return True

    def check_click_to_end(self):
        """
        check mouse left click on label "KONEC"
        """
        if super().check_click(self.start_text3, "middle"):
            return True

    def check_click_to_instructions(self):
        """
        check mouse left click on label "INSTRUKCE"
        """
        if super().check_click(self.start_text4, "top_right"):
            return True


class Instructions(Frame):
    def __init__(self):
        self.text1 = "INSTRUKCE"
        self.text2 = "VRÁTIT SE ZPÁTKY"
        self.text3 = (
            "Pro návrat na úvodní obrazovku klikněte"
            " na \"VRÁTIT SE ZPÁTKY\".")
        self.text4 = "Sestřelte co nejvíce bílých ptáků za 1 minutu:"
        self.text5 = "Velký pták = 10 bodů"
        self.text6 = "Malý pták = 25 bodů"
        self.text7 = "Získejte body navíc za sestřelení kytičky:"
        self.text8 = "Velká kytka = 10 bodů"
        self.text9 = "Malá kytka = 25 bodů"
        self.text10 = "Nabíjíte pravým tlačítkem myši anebo šipkou ↑."
        self.text11 = "Po krajině se pohybujte myší anebo šipkami: ←, ↓, →"
        self.text12 = "Pauzu spustíte mezerníkem."

        super().__init__()
        self.pic = self.set_sprite(batch=batches["instructions"])

        self.instruction_text1 = self.create_label(
            text=self.text1, font_size=40,
            value_y=((window.height // 7) * 5),
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text2 = self.create_label(
            text=self.text2, font_size=20, value_x=(window.width - 20),
            value_y=(window.height - 40), width=260, height=20,
            anchor_x="right", batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text3 = self.create_label(
            text=self.text3, font_size=18, value_y=40,
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text4 = self.create_label(
            text=self.text4, font_size=20,
            value_y=450,
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text5 = self.create_label(
            text=self.text5, font_size=20,
            value_x=((window.width // 8) * 2),
            value_y=410,
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text6 = self.create_label(
            text=self.text6, font_size=20,
            value_x=((window.width // 8) * 6),
            value_y=410,
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text7 = self.create_label(
            text=self.text7, font_size=20,
            value_y=350,
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text8 = self.create_label(
            text=self.text8, font_size=20,
            value_x=((window.width // 8) * 2),
            value_y=310,
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text9 = self.create_label(
            text=self.text9, font_size=20,
            value_x=((window.width // 8) * 6),
            value_y=310,
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text10 = self.create_label(
            text=self.text10, font_size=20,
            value_y=250,
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text11 = self.create_label(
            text=self.text11, font_size=20,
            value_y=210,
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])
        self.instruction_text12 = self.create_label(
            text=self.text12, font_size=20,
            value_y=170,
            batch=batches["instructions"],
            group=groups["foreground_text_on_gray_frame"])

    def check_click_to_back(self):
        """
        check mouse left click on label "VRÁTIT SE ZPÁTKY"
        """
        if super().check_click(self.instruction_text2, "top_right"):
            return True


class AreYouSure(Frame):
    def __init__(self):
        self.text1 = "Jste si jistí, že chcete ukončit hru?"
        self.text2 = "ANO"
        self.text3 = "NE"

        self.are_you_sure_text1 = self.create_label(
            text=self.text1, font_size=20, color=colors["black"],
            value_y=((window.height // 14) * 8))
        self.are_you_sure_text2 = self.create_label(
            text=self.text2, font_size=20, width=60, height=20,
            value_x=((window.width // 6) * 2),
            value_y=((window.height // 14) * 6))
        self.are_you_sure_text3 = self.create_label(
            text=self.text3, font_size=20, width=40, height=20,
            value_x=((window.width // 6) * 4),
            value_y=((window.height // 14) * 6))

    def draw_quads(self):
        """
        drawing a quadrangle
        """
        gl.glBegin(gl.GL_QUADS)  # vykresleni ctyruhelniku
        gl.glColor3f(0.4, 0.4, 0.3)
        gl.glVertex2i(
            (WIDTH - ((WIDTH // 6) * 1)), (HEIGHT - ((HEIGHT // 3) * 1)))
        gl.glColor3f(0.4, 0.4, 0.3)
        gl.glVertex2i(
            (WIDTH - ((WIDTH // 6) * 5)), (HEIGHT - ((HEIGHT // 3) * 1)))
        gl.glColor3f(0.1, 0.1, 0.0)
        gl.glVertex2i(
            (WIDTH - ((WIDTH // 6) * 5)), (HEIGHT - ((HEIGHT // 3) * 2)))
        gl.glColor3f(0.1, 0.1, 0.0)
        gl.glVertex2i(
            (WIDTH - ((WIDTH // 6) * 1)), (HEIGHT - ((HEIGHT // 3) * 2)))
        gl.glEnd()

    def draw(self):
        """
        function for drawing a quadrangle and labels (i.e. Frame ARE_YOU_SURE)
        """
        self.draw_quads()
        for text in [
                self.are_you_sure_text1,
                self.are_you_sure_text2, self.are_you_sure_text3]:
            text.draw()

    def check_click_to_yes(self):
        """
        check mouse left click on label "ANO"
        """
        if super().check_click(self.are_you_sure_text2, "middle"):
            return True

    def check_click_to_no(self):
        """
        check mouse left click on label "NE"
        """
        if super().check_click(self.are_you_sure_text3, "middle"):
            return True


class End(Frame):
    def __init__(self):
        self.text1 = "KONEC HRY"
        self.text2 = f"Skóre: {str(score.number)}"
        self.text3 = "OK"
        self.text4 = "Pro přechod na úvodní obrazovku klikněte na \"OK\"."

        super().__init__()
        self.pic = self.set_sprite(batch=batches["end_game"])

        self.end_text1 = self.create_label(
            text=self.text1, font_size=40, value_y=((window.height // 7) * 5),
            batch=batches["end_game"],
            group=groups["foreground_text_on_gray_frame"])
        self.end_text2 = self.create_label(
            text=self.text2, font_size=40, value_y=((window.height // 9) * 4),
            batch=batches["end_game"],
            group=groups["foreground_text_on_gray_frame"])
        self.end_text3 = self.create_label(
            text=self.text3, font_size=40, value_y=((window.height // 9) * 2),
            width=80, height=40, batch=batches["end_game"],
            group=groups["foreground_text_on_gray_frame"])
        self.end_text4 = self.create_label(
            text=self.text4, font_size=20, value_y=40,
            batch=batches["end_game"],
            group=groups["foreground_text_on_gray_frame"])

    def check_click_to_reset(self):
        """
        check mouse left click on label "OK"
        """
        if super().check_click(self.end_text3, "middle"):
            return True


class Pause(Frame):
    def __init__(self):
        self.text1 = "PAUZA"
        self.text2 = "Právě jste stiskli \"MEZERNÍK\"."
        self.text3 = "Pro návrat do hry stiskněte opět \"MEZERNÍK\"."

        super().__init__()
        self.pic = self.set_sprite(batch=batches["pause"])

        self.pause_text1 = self.create_label(
            text=self.text1, font_size=40, value_y=((window.height // 7) * 5),
            batch=batches["pause"],
            group=groups["foreground_text_on_gray_frame"])
        self.pause_text2 = self.create_label(
            text=self.text2, font_size=30, value_y=((window.height // 9) * 4),
            batch=batches["pause"],
            group=groups["foreground_text_on_gray_frame"])
        self.pause_text3 = self.create_label(
            text=self.text3, font_size=20, value_y=40,
            batch=batches["pause"],
            group=groups["foreground_text_on_gray_frame"])


class Timer(MyWindow):
    def __init__(self, start, font_size, value_y):
        self.start = start
        self.clock = int(self.start)
        self.font_size = font_size
        self.value_y = value_y
        self.running = True
        self.countdown = self.create_label()

    def create_label(self):
        return pyglet.text.Label(
            text=str(int(self.clock)),
            font_name="Arial",
            font_size=self.font_size,
            bold="True",
            x=window.width // 2,
            y=self.value_y,
            anchor_x="center",
            anchor_y="center",
            group=groups["foreground_timer_&_score"])

    def reset(self):
        """
        the function activates the countdown (i.e. running = True),
        sets the default value of the countdown and text color
        """
        self.clock = int(self.start)
        self.running = True
        self.countdown.text = str(int(self.clock))
        self.countdown.color = colors["white"]

    def update(self, dt):
        """
        one second is counted down during each update, the text color changes
        to red in the last ten seconds and a beep is added,
        a special beep sounds after the last second and indicates
        the start or end of the game
        """
        if self.running:
            self.clock -= 1
            self.countdown.text = str(int(self.clock))
            if self.clock > 10:
                self.countdown.color = colors["black"]
            elif 10 >= self.clock >= 1:
                self.countdown.color = colors["red"]
                sounds["beep"].play()
            elif self.clock < 1:
                self.running = False
                self.countdown.text = ""
                sounds["beep_ping"].play()


# instances
window = MyWindow()
landscape = Landscape()
land = Land()

cloud_left_a = Cloud(images["cloud_left"], 105, 635)
cloud_left_b = Cloud(images["cloud_left"], 125, 633)
cloud_right_a = Cloud(images["cloud_right"], 838, 658)
cloud_right_b = Cloud(images["cloud_right"], 858, 655)
list_of_clouds = [cloud_left_a, cloud_left_b, cloud_right_a, cloud_left_b]

grass = Grass()
score = Score()

timer_3_2_1 = Timer(
    start="3", font_size=360, value_y=(window.height // 2))
timer = Timer(
    start=str(LENGTH_OF_ROUND + 3), font_size=40, value_y=(HEIGHT - 40))

list_of_gray_bullets = [
    Bullet(images["bullet_gray"], 37 * num) for num in range(1, 9)]
list_of_bullets = [
    Bullet(images["bullet"], 37 * num) for num in range(1, 9)]

start = Start()
instructions = Instructions()
are_you_sure = AreYouSure()
pause = Pause()
end = End()


def draw():
    """
    the function coordinates the drawing of individual elements of the game
    """
    global START_GAME, INSTRUCTIONS, ARE_YOU_SURE, NEW_GAME, TIMER_3_2_1
    global END_GAME, TIMER
    global timer_3_2_1, timer

    gl.glClearColor(0.0, 1.0, 1.0, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    batches["landscape"].draw()
    batches["birds_small"].draw()
    batches["land"].draw()
    batches["clouds"].draw()
    batches["flowers_small"].draw()
    batches["birds"].draw()
    batches["grass"].draw()
    batches["flowers"].draw()
    batches["bullets"].draw()
    batches["score"].draw()

    if START_GAME:
        batches["start_game"].draw()

    if INSTRUCTIONS:
        batches["instructions"].draw()

    if ARE_YOU_SURE:
        are_you_sure.draw()

    if NEW_GAME:
        # one timer is replaced by another timer
        if TIMER_3_2_1:
            timer_3_2_1.countdown.draw()
            if timer_3_2_1.countdown.text == "":
                TIMER_3_2_1 = False
                TIMER = True
        # the game round ends as soon as the countdown ends
        if TIMER:
            timer.countdown.draw()
            if timer.countdown.text == "":
                TIMER = False
                NEW_GAME = False
                END_GAME = True

    if PAUSE:
        batches["pause"].draw()

    if END_GAME:
        # final score is updated to be displayed
        end.end_text2.text = f"Skóre: {str(score.number)}"
        batches["end_game"].draw()

    batches["cursor"].draw()


def key_press(symbol, modifier):
    """
    the function coordinates the game logic based on the player's input:
    i.e. which keys the player pressed
    """
    global TIMER, PAUSE
    global list_of_gray_bullets, list_of_bullets
    window.key_press(symbol, modifier)

    if TIMER:  # after NEW_GAME after TIMER_3_2_1...
        if not PAUSE:
            if symbol == pyglet.window.key.UP:
                # charging bullets
                list_of_gray_bullets = [
                    Bullet(
                        images[
                            "bullet_gray"], 37 * num) for num in range(1, 9)]
                list_of_bullets = [
                    Bullet(images["bullet"], 37 * num) for num in range(1, 9)]
                sounds["shotgun_reload"].play()
        if symbol == pyglet.window.key.SPACE:
            # pause switch
            if PAUSE:
                PAUSE = False
            else:
                PAUSE = True


def mouse_motion(x, y, dx, dy):
    """
    the function coordinates the game logic based on the player's input:
    i.e. move the mouse around the game window
    """
    global START_GAME, INSTRUCTIONS, ARE_YOU_SURE
    window.mouse_motion(x, y, dx, dy)

    # change the color of the label text after hovering the mouse
    if START_GAME and not ARE_YOU_SURE:
        start.mouse_motion(x, y, dx, dy, start.start_text2, "middle")
        start.mouse_motion(x, y, dx, dy, start.start_text3, "middle")
        start.mouse_motion(x, y, dx, dy, start.start_text4, "top_right")

    if ARE_YOU_SURE:
        are_you_sure.mouse_motion(
            x, y, dx, dy, are_you_sure.are_you_sure_text2, "middle")
        are_you_sure.mouse_motion(
            x, y, dx, dy, are_you_sure.are_you_sure_text3, "middle")

    if INSTRUCTIONS:
        instructions.mouse_motion(
            x, y, dx, dy, instructions.instruction_text2, "top_right")

    if END_GAME:
        end.mouse_motion(x, y, dx, dy, end.end_text3, "middle")


def mouse_press(x, y, button, modifiers):
    """
    the function coordinates the game logic based on the player's input:
    i.e. which mouse button the player pressed, at which point
    on the playing area in the case of the left mouse button
    """
    global START_GAME, INSTRUCTIONS, NEW_GAME, TIMER, TIMER_3_2_1, ARE_YOU_SURE
    global END_GAME
    global list_of_bullets, list_of_gray_bullets, list_of_flowers

    shot_down_flower = False
    shot_down_bird = False
    window.mouse_press(x, y, button, modifiers)

    if button == pyglet.window.mouse.LEFT:
        if TIMER:  # after NEW_GAME after TIMER_3_2_1...
            if not PAUSE:
                # erasing bullets
                if list_of_bullets:
                    del list_of_bullets[-1]

                    # check the shooting down of the bird and erasing bird
                    if list_of_birds:
                        for index, bird in enumerate(list_of_birds):
                            bird.check_shot()
                            if not bird.alive:
                                pyglet.clock.unschedule(bird.update)
                                bird.pic.delete()
                                del list_of_birds[index]
                                shot_down_bird = True
                                score.number += 25 if bird.scale == 2/10 else (
                                    10)

                    # check the shooting down of the bird and erasing bird
                    if list_of_dark_birds:
                        for index, bird in enumerate(list_of_dark_birds):
                            bird.check_shot()
                            if not bird.alive:
                                pyglet.clock.unschedule(bird.update)
                                bird.pic.delete()
                                del list_of_dark_birds[index]
                                shot_down_bird = True
                                score.number -= 25 if bird.scale == 2/10 else (
                                    10)

                    # check the shooting down of the flower and erasing flower
                    if list_of_flowers:
                        for index, flower in enumerate(list_of_flowers):
                            flower.check_shot(
                                version="small" if flower.image == images[
                                    "flower_small"] else "normal")
                            if not flower.alive:
                                pyglet.clock.unschedule(flower.update)
                                del list_of_flowers[index]
                                shot_down_flower = True
                                score.number += 25 if flower.image == images[
                                    "flower_small"] else 10

                    # playing sounds based on whether
                    # the object was shot down or not
                    if shot_down_bird:
                        sounds["shot_splat"].play()
                        sounds["shot_bird"].play()
                        shot_down_bird = False
                    elif shot_down_flower:
                        sounds["shot_splat"].play()
                        shot_down_flower = False
                    else:
                        sounds["shot"].play()

                # playing the sound of an empty gun
                else:
                    sounds["shotgun_empty"].play()

                # erasing gray bullets
                if list_of_gray_bullets:
                    list_of_gray_bullets[-1].check_bullet()   # falling bullet
                    del list_of_gray_bullets[-1]

        if START_GAME:
            if not ARE_YOU_SURE:  # the player does not want to end the game

                # new game can begin as soon as the player left-clicks
                # on the "START"
                if start.check_click_to_start():
                    NEW_GAME = True
                    TIMER_3_2_1 = True
                    START_GAME = False
                    # reset the label text color to prevent yellow text
                    # in "START"
                    start.start_text2.color = colors["black"]

                    # resetting adding flowers
                    pyglet.clock.unschedule(update_add_flower)
                    for flower in list_of_flowers:
                        pyglet.clock.unschedule(flower.update)
                    del list_of_flowers
                    list_of_flowers = []
                    pyglet.clock.schedule_interval(
                        update_add_flower, DT_NEW_GAME)

                # instructions are displayed as soon as the player
                # left-clicks on the "INSTRUKCE"
                if start.check_click_to_instructions():
                    START_GAME = False
                    INSTRUCTIONS = True
                    # reset left_mouse_coordinates to allow click between
                    # START_GAME and INSTRUCTIONS ("START", "INSTRUKCE")
                    window.left_mouse_button_coordinates["x"] = 0
                    window.left_mouse_button_coordinates["y"] = 0
                    # reset the label text color to prevent yellow text
                    # in "INSTRUKCE"
                    start.start_text4.color = colors["black"]
            if start.check_click_to_end():
                ARE_YOU_SURE = True
                # reset the label text color to prevent yellow text in "KONEC"
                start.start_text3.color = colors["black"]
            if are_you_sure.check_click_to_yes():
                window.close()
            if are_you_sure.check_click_to_no():
                ARE_YOU_SURE = False
                # reset the label text color to prevent yellow text in "NE"
                are_you_sure.are_you_sure_text3.color = colors["black"]

        if INSTRUCTIONS:
            # main screen "START_GAME" is displayed as soon as the player
            # left-clicks on the "VRÁTIT SE ZPÁTKY"
            if instructions.check_click_to_back():
                START_GAME = True
                INSTRUCTIONS = False
                # reset the label text color to prevent yellow text in "START"
                instructions.instruction_text2.color = colors["black"]

        if END_GAME:
            # main screen "START_GAME" is displayed as soon as the player
            # left-clicks on the "OK"
            if end.check_click_to_reset():
                START_GAME = True
                END_GAME = False
                # reset the label text color to prevent yellow text in "OK"
                end.end_text3.color = colors["black"]

                reset()

    if button == pyglet.window.mouse.RIGHT:

        # charging bullets
        if TIMER:  # after NEW_GAME after TIMER_3_2_1...
            if not PAUSE:
                list_of_gray_bullets = [
                    Bullet(
                        images[
                            "bullet_gray"], 37 * num) for num in range(1, 9)]
                list_of_bullets = [
                    Bullet(images["bullet"], 37 * num) for num in range(1, 9)]
                sounds["shotgun_reload"].play()


window.push_handlers(
    on_draw=draw,
    on_key_press=key_press,
    on_mouse_motion=mouse_motion,
    on_mouse_press=mouse_press)


def update_add_flower(dt):
    """
    the function coordinates the addition and removal of flowers
    """
    if not PAUSE:
        # flowers are added regularly until their maximum number is reached
        if len(list_of_flowers) < NUMBER_OF_FLOWERS:
            list_of_flowers.append(Flower())

        # the first flower added is removed as soon as their maximum number is
        # reached, subsequently the flower is added & game dynamics is ensured
        if len(list_of_flowers) == NUMBER_OF_FLOWERS:
            pyglet.clock.unschedule(list_of_flowers[0].update)
            del list_of_flowers[0]


def update_add_bird(dt):
    """
    the function coordinates the addition and removal of birds
    """
    if not PAUSE:
        # birds are added regularly until their maximum number is reached
        if len(list_of_birds) <= NUMBER_OF_BIRDS:
            list_of_birds.append(Bird())

        # a bird that leaves a visible playing field the bird is deleted
        # and replaced by a new bird & game dynamics is ensured
        for bird in list_of_birds:
            if bird.check_position_pic_x():
                pyglet.clock.unschedule(bird.update)
                bird.pic.delete()
                list_of_birds.remove(bird)


def update_add_dark_bird(dt):
    """
    the function coordinates the addition and removal of dark birds
    """
    if not PAUSE:
        # dark birds are added regularly until their maximum number is reached
        if len(list_of_dark_birds) <= NUMBER_OF_DARK_BIRDS:
            list_of_dark_birds.append(DarkBird())

        # a dark bird that leaves a visible playing field the bird is deleted
        # and replaced by a new dark bird & game dynamics is ensured
        for bird in list_of_dark_birds:
            if bird.check_position_pic_x():
                pyglet.clock.unschedule(bird.update)
                bird.pic.delete()
                list_of_dark_birds.remove(bird)


def update_timer(dt):
    """
    the function coordinates the behavior of timers
    """
    if NEW_GAME:
        # the timer countdown is regularly updated every second
        for item in timer_3_2_1, timer:
            item.update(dt)

            if TIMER:
                # the timer countdown is paused if there is a pause
                if PAUSE:
                    timer.running = False
                else:
                    timer.running = True


pyglet.clock.schedule_interval(update_add_flower, DT_BEFORE_NEW_GAME)
pyglet.clock.schedule_interval(update_add_bird, 0.5)
pyglet.clock.schedule_interval(update_add_dark_bird, 1)
pyglet.clock.schedule_interval(update_timer, 1)

pyglet.app.run()
