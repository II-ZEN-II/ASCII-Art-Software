# ASCII Art Software
# Written by Sebastian Zanardo - 2023


import time
import pygame


WINDOW_CAPTION = "ASCII Art Software"
FPS = 0  # If zero then FPS is uncapped

EMPTY = ' '
ASCII_CHARS = '''!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~'''

BACKGROUND_COLOUR = (0, 0, 0)
GRID_COLOUR = (150, 150, 150)
TEXT_COLOUR = (255, 0, 255)
GHOST_TEXT_COLOUR = (65, 55, 65)

SAVE_PATH = "saved/"  # Will be changed in future version when saving UI implemented


def main():

    # Initialise pygame
    pygame.init()
    monitor = pygame.display.Info()
    smallest = min(monitor.current_w, monitor.current_h)
    WINDOW_RESOLUTION = (smallest//2, smallest//2)
    window = pygame.display.set_mode(WINDOW_RESOLUTION)
    clock = pygame.time.Clock()

    pygame.mouse.set_visible(False)
    UI_font = pygame.font.SysFont('Hack', 40)

    # Grid
    width = 500
    height = 500
    square_size = (2, 3)
    canvas = [[EMPTY for x in range(width)] for y in range(height)]

    # Camera
    camera_offset = (WINDOW_RESOLUTION[0]//2, WINDOW_RESOLUTION[1]//2)
    camera_bounds_x = (-50, width * square_size[0] + 50)
    camera_bounds_y = (-50, height * square_size[1] + 50)
    camera_zoom = 10
    camera_zoom_bounds = (3, 25)
    camera_pos = ((width/2)*square_size[0], (height/2)*square_size[1])
    stop_rendering_grid = False

    key_repeat_time = 0.2
    key_repeat_timer = 0
    current_char_index = 2
    current_char = ASCII_CHARS[current_char_index]
    last_mouse_pos = (0,0)

    save = False
    reset = False

    font = pygame.font.SysFont('Hack', int(min(square_size)*camera_zoom))

    while True:
        dt = clock.tick(FPS)/1000
        pygame.display.set_caption(f"{WINDOW_CAPTION} | FPS {int(clock.get_fps())}")

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    terminate()
                elif event.key == pygame.K_TAB:
                    stop_rendering_grid = not(stop_rendering_grid)

            if event.type == pygame.KEYDOWN:
                character = event.unicode
                if character and character in ASCII_CHARS:
                    current_char = character
                    current_char_index = ASCII_CHARS.index(current_char)

            if event.type == pygame.MOUSEWHEEL:
                camera_zoom += round(event.precise_y/30, 1)
                camera_zoom = clamp(camera_zoom, camera_zoom_bounds[0], camera_zoom_bounds[1])
                font = pygame.font.SysFont('Hack', int(min(square_size)*camera_zoom))

        key_repeat_timer -= dt
        if keys[pygame.K_UP] and key_repeat_timer <= 0:
            current_char_index += 1
            current_char_index %= len(ASCII_CHARS)
            current_char = ASCII_CHARS[current_char_index]
            key_repeat_timer = key_repeat_time

        if keys[pygame.K_DOWN] and key_repeat_timer <= 0:
            current_char_index -= 1
            current_char_index %= len(ASCII_CHARS)
            current_char = ASCII_CHARS[current_char_index]
            key_repeat_timer = key_repeat_time

        if not reset and keys[pygame.K_r] and keys[pygame.K_LCTRL]:
            canvas = [[' ' for x in range(width)] for y in range(height)]
            print("Cleared the canvas!")
            reset = True
        elif not keys[pygame.K_r] and not keys[pygame.K_LCTRL]:
            reset = False

        if not save and keys[pygame.K_s] and keys[pygame.K_LCTRL]:
            # find top left and bottom right pixel
            top_left = [width, height]
            bottom_right = [-1, -1]

            for y in range(height):
                for x in range(width):
                    cell = canvas[y][x]
                    if cell == EMPTY:
                        continue

                    if x < top_left[0]:
                        top_left[0] = x
                    if y < top_left[1]:
                        top_left[1] = y
                    if x > bottom_right[0]:
                        bottom_right[0] = x
                    if y > bottom_right[1]:
                        bottom_right[1] = y

            if top_left != [width, height] and bottom_right != [-1, -1]:
                file_name = f"{time.asctime()}"
                file_path = f"{SAVE_PATH}{file_name}.txt"
                with open(file_path, 'w') as file:
                    for y in range(top_left[1], bottom_right[1]+1):
                        row = ""
                        for x in range(top_left[0], bottom_right[0]+1):
                            cell = canvas[y][x]
                            row += cell
                        file.write(row+'\n')

                print(f"Saved! as {file_path}")
            else:
                print("Nothing to save :(")
            save = True
        elif not keys[pygame.K_s] and not keys[pygame.K_LCTRL]:
            save = False

        # Dragging
        if mouse_pressed[1] or mouse_pressed[0] and keys[pygame.K_SPACE]:  # Middle mouse button
            drag_vector = ((last_mouse_pos[0] - mouse_pos[0])/camera_zoom,
                           (last_mouse_pos[1] - mouse_pos[1])/camera_zoom)
            camera_pos = (camera_pos[0] + drag_vector[0], camera_pos[1] + drag_vector[1])
            camera_pos = (clamp(camera_pos[0], camera_bounds_x[0], camera_bounds_x[1]),
                          clamp(camera_pos[1], camera_bounds_y[0], camera_bounds_y[1]))

        # Erasing
        elif mouse_pressed[2]:  # Right mouse button
            # inside of grid panel
            if mouse_pos[0] > 0 and mouse_pos[0] < WINDOW_RESOLUTION[0] and mouse_pos[1] > 0 and mouse_pos[1] < WINDOW_RESOLUTION[1]:
                grid_pos =  (int(((mouse_pos[0]-camera_offset[0])/camera_zoom + camera_pos[0])/square_size[0]),
                             int(((mouse_pos[1]-camera_offset[1])/camera_zoom + camera_pos[1])/square_size[1]))
                if grid_pos[0] >= 0 and grid_pos[0] < width and grid_pos[1] >= 0 and grid_pos[1] < height:
                    # inside of grid and can paint
                    canvas[grid_pos[1]][grid_pos[0]] = EMPTY

        # Painting
        elif mouse_pressed[0]:  # Left mouse button
            world_pos = ((mouse_pos[0]-camera_offset[0])/camera_zoom + camera_pos[0],
                            (mouse_pos[1]-camera_offset[1])/camera_zoom + camera_pos[1])
            grid_pos =  (int(world_pos[0]/square_size[0]),
                            int(world_pos[1]/square_size[1]))
            if inside_bounds(grid_pos[0], 0, width-1) and inside_bounds(grid_pos[1], 0, height-1):
                # inside of grid and can paint
                canvas[grid_pos[1]][grid_pos[0]] = current_char

        last_mouse_pos = mouse_pos

        # Rendering
        window.fill(BACKGROUND_COLOUR)

        # instead of trying to render all cells and checkng whether they are inside of the screen
        #   find the top left and bottom right screen coordinates in world space and draw all the
        #   cells between them.

        # for drawing lines draw to top and bottom of screen unless the grid ends.

        top_left_world_pos = (int((camera_pos[0]-camera_offset[0]/camera_zoom)/square_size[0]),
                              int((camera_pos[1]-camera_offset[1]/camera_zoom)/square_size[1]))
        bottom_right_world_pos = (int((camera_pos[0]+camera_offset[0]/camera_zoom)//square_size[0]),
                                  int((camera_pos[1]+camera_offset[1]/camera_zoom)//square_size[1]))

        # Rendering cells
        start_x = max(0, top_left_world_pos[0])
        end_x = min(width, bottom_right_world_pos[0])
        start_y = max(0, top_left_world_pos[1])
        end_y = min(height, bottom_right_world_pos[1])

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_position = ((x*square_size[0] - camera_pos[0]) * camera_zoom  + camera_offset[0],
                                   (y*square_size[1] - camera_pos[1]) * camera_zoom  + camera_offset[1])

                character = canvas[y][x]
                if character == EMPTY:
                    continue

                text = font.render(character, True, TEXT_COLOUR)
                window.blit(text, screen_position)

        origin_screen_pos = (int(-camera_pos[0] * camera_zoom + camera_offset[0]),
                            int(-camera_pos[1] * camera_zoom + camera_offset[1]))
        max_screen_pos = (int(((width)*square_size[0] - camera_pos[0]) * camera_zoom  + camera_offset[0]),
                          int(((height)*square_size[1] - camera_pos[1]) * camera_zoom  + camera_offset[1]))

        line_start_x = max(origin_screen_pos[0], 0)
        line_end_x = min(max_screen_pos[0], WINDOW_RESOLUTION[0])

        line_start_y = max(origin_screen_pos[1], 0)
        line_end_y = min(max_screen_pos[1], WINDOW_RESOLUTION[1])

        if not stop_rendering_grid:
            # drawing horizontal lines
            for y in range(start_y, end_y+1):
                screen_position = (y*square_size[1] - camera_pos[1]) * camera_zoom  + camera_offset[1]
                pygame.draw.line(window, GRID_COLOUR, (line_start_x, screen_position), (line_end_x, screen_position))

            # drawing vertical lines
            for x in range(start_x, end_x+1):
                screen_position = (x*square_size[0] - camera_pos[0]) * camera_zoom  + camera_offset[0]
                pygame.draw.line(window, GRID_COLOUR, (screen_position, line_start_y), (screen_position, line_end_y))

        # center of camera
        pygame.draw.circle(window, (255, 255, 255), camera_offset, 2)

        ghost_text = UI_font.render(current_char, True, GHOST_TEXT_COLOUR)
        window.blit(ghost_text, mouse_pos)
        pygame.draw.circle(window, (255, 255, 255), mouse_pos, 5)

        pygame.display.flip()


def inside_bounds(value, minimum, maximum):
    return value >= minimum and value <= maximum


def clamp(value, minimum, maximum):
    return min(max(value, minimum), maximum)


def terminate():
    pygame.quit()
    raise SystemExit


if __name__ == "__main__":
    main()
