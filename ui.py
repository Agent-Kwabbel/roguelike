import pygame

import sprites
from settings import W, H

YELLOW = (250, 220, 60)
GREY = (170, 170, 185)
WHITE = (245, 245, 250)
CARD = (22, 20, 34, 215)
BACK_RECT = pygame.Rect(16, 16, 120, 38)


def tint(color, amount, alpha=235):
    # kleur mengen met de donkere achtergrond van de kaarten
    r = int(22 + (color[0] - 22) * amount)
    g = int(20 + (color[1] - 20) * amount)
    b = int(34 + (color[2] - 34) * amount)
    return (r, g, b, alpha)


def card(screen, rect, border=None, fill=CARD, radius=12):
    rect = pygame.Rect(rect)
    surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(surface, fill, (0, 0, rect.w, rect.h), border_radius=radius)
    screen.blit(surface, rect.topleft)
    if border:
        pygame.draw.rect(screen, border, rect, 2, border_radius=radius)


def button(screen, rect, label, active, accent=YELLOW, sub=None, size=30, disabled=False):
    rect = pygame.Rect(rect)
    if active and not disabled:
        # actieve knop schuift een stukje op en krijgt een gloed
        rect.x += 6
        glow = pygame.Surface((rect.w + 12, rect.h + 12), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*accent, 40), (0, 0, rect.w + 12, rect.h + 12), border_radius=16)
        screen.blit(glow, (rect.x - 6, rect.y - 6))
        card(screen, rect, accent, tint(accent, 0.25))
        pygame.draw.rect(screen, accent, (rect.x + 8, rect.y + 10, 4, rect.h - 20), border_radius=2)
        color = accent
    else:
        card(screen, rect, (70, 68, 95))
        color = (110, 110, 120) if disabled else WHITE

    font = sprites.font(size)
    if sub:
        text_y = rect.y + rect.h / 2 - font.get_height() / 2 - 9
    else:
        text_y = rect.y + rect.h / 2 - font.get_height() / 2 + 2
    screen.blit(font.render(label, True, color), (rect.x + 22, text_y))
    if sub:
        small = sprites.font(22).render(sub, True, GREY)
        screen.blit(small, (rect.x + 22, text_y + font.get_height() + 2))
    return rect


def hovered(rects):
    pos = pygame.mouse.get_pos()
    for i, rect in enumerate(rects):
        if pygame.Rect(rect).collidepoint(pos):
            return i
    return None


def clicked(events, rects):
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(rects):
                if pygame.Rect(rect).collidepoint(event.pos):
                    return i
    return None


def navigate(events, selected, rects, columns=1):
    """Muis en toetsenbord samen. Geeft (selected, gekozen index of None) terug."""
    count = len(rects)
    chosen = None
    for event in events:
        if event.type == pygame.MOUSEMOTION:
            index = hovered(rects)
            if index is not None:
                selected = index
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = hovered(rects)
            if index is not None:
                selected = index
                chosen = index
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                selected = (selected - columns) % count
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                selected = (selected + columns) % count
            elif columns > 1 and event.key in (pygame.K_LEFT, pygame.K_a):
                selected = (selected - 1) % count
            elif columns > 1 and event.key in (pygame.K_RIGHT, pygame.K_d):
                selected = (selected + 1) % count
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                chosen = selected
    return selected, chosen


def back_button(screen):
    active = BACK_RECT.collidepoint(pygame.mouse.get_pos())
    button(screen, BACK_RECT, "< Terug", active, size=26)


def back_clicked(events):
    return clicked(events, [BACK_RECT]) is not None


def blur(screen, darkness=140):
    small = pygame.transform.smoothscale(screen, (W // 8, H // 8))
    screen.blit(pygame.transform.smoothscale(small, (W, H)), (0, 0))
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((8, 6, 18, darkness))
    screen.blit(overlay, (0, 0))


def title(screen, text, size, color, y, x=W / 2):
    font = sprites.font(size)
    image = font.render(text, True, color)
    shadow = font.render(text, True, (0, 0, 0))
    screen.blit(shadow, (x - image.get_width() / 2 + 3, y + 4))
    screen.blit(image, (x - image.get_width() / 2, y))


# ---------- ja/nee vraag ----------

def confirm_rects():
    return [pygame.Rect(W / 2 - 170, H / 2 + 20, 160, 52), pygame.Rect(W / 2 + 10, H / 2 + 20, 160, 52)]


def handle_confirm(events, selected):
    """Geeft (selected, True/False/None) terug. Esc is nee."""
    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return selected, False
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            selected = 1 - selected
    selected, chosen = navigate(events, selected, confirm_rects())
    if chosen is None:
        return selected, None
    return selected, chosen == 0


def draw_confirm(screen, question, detail, selected):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    card(screen, (W / 2 - 220, H / 2 - 110, 440, 210), YELLOW)
    title(screen, question, 44, WHITE, H / 2 - 88)
    if detail:
        title(screen, detail, 24, GREY, H / 2 - 38)
    yes, no = confirm_rects()
    button(screen, yes, "Ja", selected == 0, (240, 110, 110))
    button(screen, no, "Nee", selected == 1)
