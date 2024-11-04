import random, pygame, neat

# Initialize Pygame
pygame.init()

# Set up the clock to control frame rate
CLOCK = pygame.time.Clock()
# Define colors
RED = (255, 0, 0)
BLACK = (0, 0, 0)
FPS = 60  # Frames per second

# Set up window dimensions and create the window
WN_WIDTH = 400
WN_HEIGHT = 500
WN = pygame.display.set_mode((WN_WIDTH, WN_HEIGHT))
pygame.display.set_caption("Flappy Bird (AI Edition")  # Set window title

# Load images and set dimensions
BG = pygame.image.load("assets/bird_bg.png")  # Background image
BIRD_IMG = pygame.image.load("assets/bird.png")  # Bird image
BIRD_SIZE = (40, 26)  # Size of the bird image
BIRD_IMG = pygame.transform.scale(BIRD_IMG, BIRD_SIZE)  # Scale bird image
GRAVITY = 4  # Gravity effect on the bird
JUMP = 30  # Jump height when the bird jumps

# Pipe settings
PIPE_X0 = 400  # Initial x position for pipes
PIPE_BOTTOM_IMG = pygame.image.load("assets/pipe.png")  # Pipe image
PIPE_TOP_IMG = pygame.transform.flip(PIPE_BOTTOM_IMG, False, True)  # Flipped pipe image for top
PIPE_BOTTOM_HEIGHTS = [90, 122, 154, 186, 218, 250]  # Possible heights for bottom pipes
GAP_PIPE = 150  # Gap between top and bottom pipes
PIPE_EVENT = pygame.USEREVENT  # Custom event for pipe generation
pygame.time.set_timer(PIPE_EVENT, 1000)  # Set timer to generate pipes every second
FONT = pygame.font.SysFont("comicsans", 30)  # Font for displaying text
SCORE_INCREASE = .01  # Score increment per frame
GEN = 0  # Generation counter for NEAT

# Class for pipe objects
class Pipe:
    def __init__(self, height):
        # Set the position of bottom and top pipes based on height
        bottom_midtop = (PIPE_X0, WN_HEIGHT - height)
        top_midbottom = (PIPE_X0, WN_HEIGHT - height - GAP_PIPE)
        # Create rectangles for the bottom and top pipes
        self.bottom_pipe_rect = PIPE_BOTTOM_IMG.get_rect(midtop=bottom_midtop)
        self.top_pipe_rect = PIPE_TOP_IMG.get_rect(midbottom=top_midbottom)

    def display_pipe(self):
        # Draw pipes on the window
        WN.blit(PIPE_BOTTOM_IMG, self.bottom_pipe_rect)
        WN.blit(PIPE_TOP_IMG, self.top_pipe_rect)

# Class for bird objects
class Bird:
    def __init__(self):
        # Create a rectangle for the bird at the center of the window
        self.bird_rect = BIRD_IMG.get_rect(center=(WN_WIDTH // 2, WN_HEIGHT // 2))
        self.dead = False  # Status to check if the bird is alive
        self.score = 0  # Initialize score

    def collision(self, pipes):
        # Check for collisions with pipes or boundaries
        for pipe in pipes:
            if self.bird_rect.colliderect(pipe.bottom_pipe_rect) or \
               self.bird_rect.colliderect(pipe.top_pipe_rect):
                return True  # Collision detected
        # Check if bird hits the ground or flies too high
        if self.bird_rect.midbottom[1] >= WN_HEIGHT or self.bird_rect.midtop[1] < 0:
            return True
        return False  # No collision

    def find_nearest_pipes(self, pipes):
        # Find the nearest pipes to the bird
        nearest_pipe_top = None
        nearest_pipe_bottom = None
        min_distance = WN_WIDTH  # Start with max possible distance
        for pipe in pipes:
            curr_distance = pipe.bottom_pipe_rect.topright[0] - self.bird_rect.topleft[0]
            if curr_distance < 0:
                continue  # Pipe is behind the bird
            elif curr_distance <= min_distance:
                min_distance = curr_distance
                nearest_pipe_bottom = pipe.bottom_pipe_rect
                nearest_pipe_top = pipe.top_pipe_rect
        return nearest_pipe_top, nearest_pipe_bottom  # Return nearest pipes

    def get_distances(self, top_pipe, bottom_pipe):
        # Calculate distances to the nearest pipes
        distance = [WN_WIDTH] * 3  # Default distances
        distance[0] = top_pipe.centerx - self.bird_rect.centerx  # Horizontal distance to top pipe
        distance[1] = self.bird_rect.topleft[1] - top_pipe.bottomright[1]  # Vertical distance to top pipe
        distance[2] = bottom_pipe.topright[1] - self.bird_rect.bottomright[1]  # Vertical distance to bottom pipe
        return distance  # Return distances

    def draw_lines(self, top_pipe, bottom_pipe):
        # Draw lines from the bird to the nearest pipes for visualization
        pygame.draw.line(WN, RED, self.bird_rect.midright, top_pipe.midbottom, 5)
        pygame.draw.line(WN, RED, self.bird_rect.midright, bottom_pipe.midtop, 5)

# Main game loop function
def game_loop(genomes, config):
    global GEN
    GEN += 1  # Increment generation count
    birds = []  # List of bird instances
    nets = []  # List of neural networks
    ge = []  # List of genomes

    pipe_list = []  # List to store active pipes

    # Initialize birds, genomes, and networks
    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)  # Create neural network for each genome
        genome.fitness = 0  # Initialize fitness
        nets.append(net)
        birds.append(Bird())
        ge.append(genome)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()  # Quit if window is closed
                quit()
            if event.type == PIPE_EVENT:
                # Generate a new pipe at a random height
                bottom_height = random.choice(PIPE_BOTTOM_HEIGHTS)
                pipe_list.append(Pipe(bottom_height))

        # Draw background
        WN.blit(BG, (0, 0))
        remove_pipes = []  # List to keep track of pipes to remove

        for pipe in pipe_list:
            # Move pipes to the left
            pipe.top_pipe_rect.x -= 3
            pipe.bottom_pipe_rect.x -= 3
            pipe.display_pipe()  # Draw pipes

            # Check if pipes are off screen
            if pipe.top_pipe_rect.x < -100:
                remove_pipes.append(pipe)  # Mark for removal

        # Remove off-screen pipes
        for r in remove_pipes:
            pipe_list.remove(r)

        alive_birds = 0  # Count of alive birds
        max_score = 0  # Track maximum score

        # Process each bird
        for i, bird in enumerate(birds):
            if not bird.dead:
                bird.bird_rect.centery += GRAVITY  # Apply gravity
                bird.score += SCORE_INCREASE  # Increment score

                alive_birds += 1  # Count alive birds
                max_score = max(max_score, bird.score)  # Update max score
                ge[i].fitness += bird.score  # Update genome fitness

                WN.blit(BIRD_IMG, bird.bird_rect)  # Draw the bird
                bird.dead = bird.collision(pipe_list)  # Check for collisions
                
                nearest_pipes = bird.find_nearest_pipes(pipe_list)  # Find nearest pipes
                if nearest_pipes[0]:
                    distances = bird.get_distances(nearest_pipes[0], nearest_pipes[1])  # Get distances to pipes
                    bird.draw_lines(nearest_pipes[0], nearest_pipes[1])  # Draw lines to pipes
                else:
                    distances = [WN_WIDTH] * 3  # Default distances if no pipes are found

                # Activate the neural network with distances
                output = nets[i].activate(distances)
                max_ind = output.index(max(output))  # Get index of the highest output
                if max_ind == 0:
                    bird.bird_rect.centery -= JUMP  # Jump if output suggests

        # If no birds are alive, exit the loop
        if alive_birds == 0:
            return

        # Display generation, birds alive, and max score
        msg = f"Gen: {GEN} Birds Alive: {alive_birds} Score: {int(max_score)}"
        text = FONT.render(msg, True, BLACK)
        WN.blit(text, (40, 20))  # Render the text on screen
        pygame.display.update()  # Update the display
        CLOCK.tick(FPS)  # Control frame rate

# Run the game
neat_config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, 
    neat.DefaultSpeciesSet, neat.DefaultStagnation, "config.txt")  # Load NEAT configuration
population = neat.Population(neat_config)  # Create population for NEAT
stats = neat.StatisticsReporter()  # Create a statistics reporter
population.add_reporter(stats)  # Add reporter to population
population.run(game_loop, 50)  # Run the game loop for 50 generations
