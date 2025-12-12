import pygame

WIDTH, HEIGHT = 800, 600
FPS = 60


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Voxelbound - Prototype")
    clock = pygame.time.Clock()

    player = pygame.Rect(WIDTH // 2 - 16, HEIGHT // 2 - 16, 32, 32)
    speed = 300

    font = pygame.font.SysFont(None, 24)
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        vx = 0
        vy = 0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            vx += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            vx -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            vy += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            vy -= 1

        if vx != 0 or vy != 0:
            norm = (vx * vx + vy * vy) ** 0.5
            player.x += int((vx / norm) * speed * dt) if norm != 0 else 0
            player.y += int((vy / norm) * speed * dt) if norm != 0 else 0

        screen.fill((30, 30, 40))
        pygame.draw.rect(screen, (200, 180, 60), player)

        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (200, 200, 200))
        screen.blit(fps_text, (10, 10))

        instr = font.render("WASD / Arrows to move — Esc to quit", True, (200, 200, 200))
        screen.blit(instr, (10, 30))

        pygame.display.flip()

    pygame.quit()
