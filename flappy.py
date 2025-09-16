try:
    import pygame, random, time
    from pygame.locals import *
except ModuleNotFoundError as e:
    print("Le module 'pygame' n'est pas installé. Veuillez exécuter 'pip install pygame' dans votre terminal.")
    raise e

# VARIABLES
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SPEED = 20
GRAVITY = 2.5
GAME_SPEED = 15

GROUND_WIDTH = 2 * SCREEN_WIDTH
GROUND_HEIGHT = 100

PIPE_WIDTH = 80
PIPE_HEIGHT = 500

PIPE_GAP = 150

wing = 'assets/audio/wing.wav'
hit = 'assets/audio/hit.wav'

pygame.mixer.init()

# Fonction utilitaire pour afficher du texte (menus uniquement)
def blit_text(surface, text_surface, pos, reverse_mode=False):
    """Dessine le texte dans le bon sens, même si reverse_mode est activé (menus uniquement)."""
    if reverse_mode:
        flipped_text = pygame.transform.flip(text_surface, False, True)
        new_y = SCREEN_HEIGHT - pos[1] - text_surface.get_height()
        surface.blit(flipped_text, (pos[0], new_y))
    else:
        surface.blit(text_surface, pos)

class Bird(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        
        self.images = [pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha(),
                       pygame.image.load('assets/sprites/bluebird-midflap.png').convert_alpha(),
                       pygame.image.load('assets/sprites/bluebird-downflap.png').convert_alpha()]
        
        self.speed = SPEED
        self.current_image = 0
        self.image = self.images[0]
        self.mask = pygame.mask.from_surface(self.image)
        
        self.rect = self.image.get_rect()
        self.rect[0] = SCREEN_WIDTH / 6
        self.rect[1] = SCREEN_HEIGHT / 2

    def update(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]
        self.speed += GRAVITY
        self.rect[1] += self.speed

    def bump(self):
        self.speed = -SPEED

    def begin(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]

class Pipe(pygame.sprite.Sprite):
    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)
        
        self.image = pygame.image.load('assets/sprites/pipe-green.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDTH, PIPE_HEIGHT))
        
        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.inverted = inverted
        
        if inverted:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect[1] = -(self.rect[3] - ysize)
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize
        
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect[0] -= GAME_SPEED

class Ground(pygame.sprite.Sprite):
    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('assets/sprites/base.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (GROUND_WIDTH, GROUND_HEIGHT))
        
        self.mask = pygame.mask.from_surface(self.image)
        
        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT
        
    def update(self):
        self.rect[0] -= GAME_SPEED

def is_off_screen(sprite):
    return sprite.rect[0] < -(sprite.rect[2])

def get_random_pipes(xpos):
    size = random.randint(100, 300)
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return pipe, pipe_inverted

# Character roster
BIRDS_BESTIAIRE = [
    {
        "name": "Blue Bird",
        "sprites": [
            'assets/sprites/bluebird-upflap.png',
            'assets/sprites/bluebird-midflap.png',
            'assets/sprites/bluebird-downflap.png'
        ]
    },
    {
        "name": "Red Bird",
        "sprites": [
            'assets/sprites/redbird-upflap.png',
            'assets/sprites/redbird-midflap.png',
            'assets/sprites/redbird-downflap.png'
        ]
    },
    {
        "name": "Yellow Bird",
        "sprites": [
            'assets/sprites/yellowbird-upflap.png',
            'assets/sprites/yellowbird-midflap.png',
            'assets/sprites/yellowbird-downflap.png'
        ]
    },
]

def load_bird_images(bird_entry):
    return [pygame.image.load(img).convert_alpha() for img in bird_entry["sprites"]]

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Flappy Bird')

def start_game(selected_bird, reverse_mode):
    # Initialize sprite groups
    bird_group = pygame.sprite.Group()
    bird = Bird()
    bird.images = load_bird_images(BIRDS_BESTIAIRE[selected_bird])
    bird.image = bird.images[0]
    bird.mask = pygame.mask.from_surface(bird.image)
    bird_group.add(bird)

    # Initialize ground
    ground_group = pygame.sprite.Group()
    for i in range(2):
        ground = Ground(GROUND_WIDTH * i)
        ground_group.add(ground)

    # Initialize pipes
    pipe_group = pygame.sprite.Group()
    for i in range(2):
        pipes = get_random_pipes(SCREEN_WIDTH * i + 800)
        pipe_group.add(pipes[0])
        pipe_group.add(pipes[1])

    # Game variables
    clock = pygame.time.Clock()
    score = 0
    font_score = pygame.font.SysFont(None, 48)
    font_end = pygame.font.SysFont(None, 36)
    passed_pipes = []
    
    # Backgrounds
    day_background = pygame.image.load('assets/sprites/background-day.png')
    day_background = pygame.transform.scale(day_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    night_background = pygame.image.load('assets/sprites/background-night.png')
    night_background = pygame.transform.scale(night_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    change_bg_time = 30
    start_time = time.time()

    # Load begin image
    try:
        BEGIN_IMAGE = pygame.image.load('assets/sprites/message.png').convert_alpha()
    except:
        BEGIN_IMAGE = pygame.Surface((160, 160), pygame.SRCALPHA)
        font_msg = pygame.font.SysFont(None, 24)
        msg_text = font_msg.render("Press SPACE", True, (255, 255, 255))
        msg_text2 = font_msg.render("to start!", True, (255, 255, 255))
        BEGIN_IMAGE.blit(msg_text, (40, 60))
        BEGIN_IMAGE.blit(msg_text2, (50, 100))

    # Start screen
    begin = True
    while begin:
        clock.tick(15)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return
            if event.type == KEYDOWN and event.key in (K_SPACE, K_UP):
                bird.bump()
                try:
                    pygame.mixer.music.load(wing)
                    pygame.mixer.music.play()
                except:
                    pass
                begin = False

        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg = day_background
        game_surface.blit(bg, (0, 0))
        game_surface.blit(BEGIN_IMAGE, (120, 150))
        score_text = font_score.render(f"Score : {score}", True, (255, 255, 255))
        blit_text(game_surface, score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 20), reverse_mode)

        if is_off_screen(ground_group.sprites()[0]):
            ground_group.remove(ground_group.sprites()[0])
            new_ground = Ground(GROUND_WIDTH - 20)
            ground_group.add(new_ground)

        bird.begin()
        ground_group.update()
        bird_group.draw(game_surface)
        ground_group.draw(game_surface)

        if reverse_mode:
            flipped = pygame.transform.flip(game_surface, False, True)
            screen.blit(flipped, (0, 0))
        else:
            screen.blit(game_surface, (0, 0))

        pygame.display.update()

    # Main game loop
    while True:
        clock.tick(15)
        elapsed = time.time() - start_time
        bg = night_background if elapsed > change_bg_time else day_background

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return
            if event.type == KEYDOWN and event.key in (K_SPACE, K_UP):
                bird.bump()
                try:
                    pygame.mixer.music.load(wing)
                    pygame.mixer.music.play()
                except:
                    pass

        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        game_surface.blit(bg, (0, 0))

        if is_off_screen(ground_group.sprites()[0]):
            ground_group.remove(ground_group.sprites()[0])
            new_ground = Ground(GROUND_WIDTH - 20)
            ground_group.add(new_ground)

        if is_off_screen(pipe_group.sprites()[0]):
            pipe_group.remove(pipe_group.sprites()[0])
            pipe_group.remove(pipe_group.sprites()[0])
            pipes = get_random_pipes(SCREEN_WIDTH * 2)
            pipe_group.add(pipes[0])
            pipe_group.add(pipes[1])

        bird_group.update()
        ground_group.update()
        pipe_group.update()

        bird_group.draw(game_surface)
        pipe_group.draw(game_surface)
        ground_group.draw(game_surface)

        for pipe in pipe_group:
            if (pipe.rect[0] + PIPE_WIDTH < bird.rect[0] and 
                pipe not in passed_pipes and not pipe.inverted):
                score += 1
                passed_pipes.append(pipe)

        # Score affiché normalement pendant le jeu
        score_text = font_score.render(f"Score : {score}", True, (255, 255, 255))
        game_surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 20))

        if reverse_mode:
            flipped = pygame.transform.flip(game_surface, False, True)
            screen.blit(flipped, (0, 0))
        else:
            screen.blit(game_surface, (0, 0))

        pygame.display.update()

        if (pygame.sprite.groupcollide(bird_group, ground_group, False, False, pygame.sprite.collide_mask) or
            pygame.sprite.groupcollide(bird_group, pipe_group, False, False, pygame.sprite.collide_mask)):
            try:
                pygame.mixer.music.load(hit)
                pygame.mixer.music.play()
            except:
                pass
            time.sleep(1)
            return show_game_over(screen, score, font_end, reverse_mode)

def show_game_over(screen, score, font_end, reverse_mode):
    while True:
        screen.fill((0, 0, 0))
        over_text = font_end.render("Game Over", True, (255, 0, 0))
        score_text = font_end.render(f"Votre score : {score}", True, (255, 255, 255))
        retry_text = font_end.render("Appuyez sur R pour recommencer", True, (255, 255, 0))
        quit_text = font_end.render("Ou ECHAP pour quitter", True, (200, 200, 200))
        
        # Ici les textes respectent le mode inversé
        blit_text(screen, over_text, (SCREEN_WIDTH // 2 - over_text.get_width() // 2, 180), reverse_mode)
        blit_text(screen, score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 240), reverse_mode)
        blit_text(screen, retry_text, (SCREEN_WIDTH // 2 - retry_text.get_width() // 2, 300), reverse_mode)
        blit_text(screen, quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, 340), reverse_mode)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return False
            if event.type == KEYDOWN:
                if event.key == K_r:
                    return True
                if event.key == K_ESCAPE:
                    pygame.quit()
                    return False

# Main game loop
def main():
    while True:
        selected_bird = 0
        reverse_mode = False
        font_title = pygame.font.SysFont(None, 48)
        font = pygame.font.SysFont(None, 32)
        
        selecting = True
        while selecting:
            screen.fill((0, 0, 0))
            
            title = font_title.render("Choisissez votre couleur d'oiseau", True, (255, 255, 0))
            blit_text(screen, title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60), reverse_mode)
            
            name = BIRDS_BESTIAIRE[selected_bird]["name"]
            text = font.render(f"Oiseau : {name}", True, (255, 255, 255))
            blit_text(screen, text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 130), reverse_mode)
            
            try:
                img = pygame.image.load(BIRDS_BESTIAIRE[selected_bird]["sprites"][1]).convert_alpha()
                img = pygame.transform.scale(img, (60, 60))
                img_x = SCREEN_WIDTH // 2 - 30
                img_y = 200
                screen.blit(img, (img_x, img_y))
                
                arrow_color = (255, 255, 0)
                pygame.draw.polygon(screen, arrow_color, [
                    (img_x - 40, img_y + 30),
                    (img_x - 10, img_y + 10),
                    (img_x - 10, img_y + 50)
                ])
                pygame.draw.polygon(screen, arrow_color, [
                    (img_x + 70 + 40, img_y + 30),
                    (img_x + 70 + 10, img_y + 10),
                    (img_x + 70 + 10, img_y + 50)
                ])
            except:
                no_img_text = font.render("Image non trouvée", True, (255, 100, 100))
                blit_text(screen, no_img_text, (SCREEN_WIDTH // 2 - no_img_text.get_width() // 2, 220), reverse_mode)
            
            instr = font.render("← → changer, V : inversé, Entrée/Espace : valider", True, (200, 200, 200))
            blit_text(screen, instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2, 350), reverse_mode)
            
            if reverse_mode:
                revtxt = font.render("MODE INVERSÉ ACTIVÉ", True, (255, 100, 100))
                blit_text(screen, revtxt, (SCREEN_WIDTH // 2 - revtxt.get_width() // 2, 400), reverse_mode)
            
            pygame.display.update()
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    return
                if event.type == KEYDOWN:
                    if event.key == K_LEFT:
                        selected_bird = (selected_bird - 1) % len(BIRDS_BESTIAIRE)
                    if event.key == K_RIGHT:
                        selected_bird = (selected_bird + 1) % len(BIRDS_BESTIAIRE)
                    if event.key == K_v:
                        reverse_mode = not reverse_mode
                    if event.key in (K_RETURN, K_SPACE):
                        selecting = False

        restart = start_game(selected_bird, reverse_mode)
        if not restart:
            break

if __name__ == "__main__":
    main()
