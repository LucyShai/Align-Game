import sys
import random
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from ship import Ship
from bullet import Bullet
from alien import Alien


class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()
        self.clock = pygame.time.Clock()
        self.settings = Settings()

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Alien Invasion")

        # Create an instance to store game statistics.
        self.stats = GameStats(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()
        self._create_stars()


    def run_game(self):
        """Start the main loop for the game."""
        while True:
            self._check_events()

            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._update_screen()
            self.clock.tick(60)

    def _check_events(self):
        """ Responds to keyboard events. """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)

    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """Updates position of bullets and remove old bullets"""
        # Update bullet positions
        self.bullets.update()

        # Get rid of bullets that have disappeared.
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        # Remove any bullets and aliens that have collided.
        collisions = pygame.sprite.groupcollide(
                self.bullets, self.aliens, True, True)

        if not self.aliens:
            # Destroy existing bullets and create new fleet.
            self.bullets.empty()
            self._create_fleet()
            
            # Increase game level.
            self.stats.level += 1
            if self.stats.level <= 10:
                self.settings.increase_speed()

    def _create_stars(self):
        """Create a starfield background."""
        self.stars = []
        for _ in range(100):
            star_x = random.randint(0, self.settings.screen_width)
            star_y = random.randint(0, self.settings.screen_height)
            star_size = random.randint(1, 3)
            self.stars.append((star_x, star_y, star_size))

    def _draw_stars(self):
        """Draw stars on the screen."""
        for star in self.stars:
            # Drawing stars slightly darker/different if bg is light, 
            # but usually stars are white for black backgrounds.
            # I'll use a color that contrasts with the current bg choice.
            star_color = (255, 255, 255) if self.settings.bg_color[0] < 100 else (100, 100, 100)
            pygame.draw.circle(self.screen, star_color, (star[0], star[1]), star[2])

    def _draw_lives(self):
        """Draw the remaining ships at the top of the screen."""
        for ship_number in range(self.stats.ships_left):
            ship = Ship(self)
            ship.rect.x = 10 + ship_number * (ship.rect.width + 10)
            ship.rect.y = 10
            # Scale down the mini-ships for the UI
            small_ship = pygame.transform.scale(ship.image, (int(ship.rect.width * 0.5), int(ship.rect.height * 0.5)))
            self.screen.blit(small_ship, (10 + ship_number * (small_ship.get_width() + 5), 10))

    def _create_fleet(self):
        """Create the fleet of aliens in a triangular formation."""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        
        # Calculate how many rows based on level (L1=5, L2=6, ...)
        number_rows = min(self.stats.level + 4, 12)
        
        # Calculate horizontal spacing
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - (2 * alien_height) - ship_height)
        # If too many rows, reduce vertical spacing
        v_spacing = 2 * alien_height
        if number_rows * v_spacing > available_space_y:
            v_spacing = available_space_y // number_rows

        # Create the triangular fleet
        for row_number in range(number_rows):
            # Row 0 has 1 alien, Row 1 has 2, etc. (following image pattern)
            number_aliens_in_row = row_number + 1
            
            # Center the row
            row_width = (2 * number_aliens_in_row - 1) * alien_width
            start_x = (self.settings.screen_width - row_width) // 2
            
            for alien_number in range(number_aliens_in_row):
                self._create_alien_pos(
                    start_x + alien_number * (2 * alien_width),
                    alien_height + row_number * v_spacing
                )

    def _create_alien_pos(self, x, y):
        """Create an alien at a specific position."""
        alien = Alien(self)
        alien.x = float(x)
        alien.rect.x = x
        alien.rect.y = y
        self.aliens.add(alien)


    def _create_alien(self, alien_number, row_number):
        # Deprecated in favor of _create_alien_pos but keeping for compatibility if needed
        pass

    def _update_aliens(self):
        """
        Check if the fleet is at an edge,
          then update the positions of all aliens in the fleet.
        """
        self._check_fleet_edges()
        self.aliens.update()

        # Look for alien-ship collisions.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # Look for aliens hitting the bottom of the screen.
        self._check_aliens_bottom()

    def _draw_level(self):
        """Draw the current level at the top center of the screen."""
        font = pygame.font.SysFont(None, 48)
        level_str = f"Level: {self.stats.level}"
        # Contrast with background color
        text_color = (255, 255, 255) if self.settings.bg_color[0] < 100 else (0, 0, 0)
        level_image = font.render(level_str, True, text_color)
        
        # Position the level at the top center
        level_rect = level_image.get_rect()
        level_rect.centerx = self.screen.get_rect().centerx
        level_rect.top = 10
        
        self.screen.blit(level_image, level_rect)

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _ship_hit(self):
        """Respond to the ship being hit by an alien."""
        if self.stats.ships_left > 0:
            # Decrement ships_left.
            self.stats.ships_left -= 1

            # Get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.rect.midbottom = self.ship.screen_rect.midbottom
            self.ship.x = float(self.ship.rect.x)
            
            # Reset difficulty for current level if hit?
            # Usually we don't reset speed on hit, only on game over.
            # But the user might want it easier. I'll stick to arcade standard.

            # Pause.
            sleep(0.5)
        else:
            self.stats.game_active = False
            # Prepare for reset if they play again
            self.settings.initialize_dynamic_settings()

    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # Treat this the same as if the ship got hit.
                self._ship_hit()
                break




    def _update_screen(self):
        """ Updates the game screen based on game settings. """
        self.screen.fill(self.settings.bg_color)
        self._draw_stars()
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)
        self._draw_lives()
        self._draw_level()
        pygame.display.flip()


if __name__ == '__main__':
    # Make a game instance, and run the game.
    ai = AlienInvasion()
    ai.run_game()

