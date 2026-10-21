import pygame

import ambient
import sound
import sprites
from settings import W, H

WHITE = (245, 245, 250)
GREY = (170, 170, 185)
DIM = (110, 110, 125)
YELLOW = (250, 220, 60)
GREEN = (120, 220, 130)
RED = (240, 110, 110)
BLUE = (120, 190, 250)
PURPLE = (190, 120, 250)
COIN = (240, 200, 60)
CARD = (22, 20, 34, 215)
BORDER = (70, 68, 95)
BACK_RECT = pygame.Rect(16, 16, 110, 36)
FOOTER_HEIGHT = 34


def tint(color, amount, alpha=235):
    # mix a colour with the dark background of the cards
    r = int(22 + (color[0] - 22) * amount)
    g = int(20 + (color[1] - 20) * amount)
    b = int(34 + (color[2] - 34) * amount)
    return (r, g, b, alpha)


def card(screen, rect, border=None, fill=CARD, radius=12, shadow=False):
    rect = pygame.Rect(rect)
    if shadow:
        under = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(under, (0, 0, 0, 90), (0, 0, rect.w, rect.h), border_radius=radius)
        screen.blit(under, (rect.x + 4, rect.y + 6))
    surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(surface, fill, (0, 0, rect.w, rect.h), border_radius=radius)
    screen.blit(surface, rect.topleft)
    if border:
        pygame.draw.rect(screen, border, rect, 2, border_radius=radius)


def glow(screen, rect, color, radius=16, spread=6, alpha=45):
    rect = pygame.Rect(rect)
    surface = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2), pygame.SRCALPHA)
    pygame.draw.rect(surface, (*color, alpha), surface.get_rect(), border_radius=radius)
    screen.blit(surface, (rect.x - spread, rect.y - spread))


def text(screen, label, size, color, pos, align="left", shadow=False):
    """Draw text at pos, align is left, center or right. Returns the rect."""
    image = sprites.font(size).render(str(label), True, color)
    x, y = pos
    if align == "center":
        x -= image.get_width() / 2
    elif align == "right":
        x -= image.get_width()
    if shadow:
        screen.blit(sprites.font(size).render(str(label), True, (0, 0, 0)), (x + 2, y + 2))
    screen.blit(image, (x, y))
    return pygame.Rect(x, y, image.get_width(), image.get_height())


def title(screen, label, size, color, y, x=W / 2):
    font = sprites.font(size)
    image = font.render(label, True, color)
    shadow = font.render(label, True, (0, 0, 0))
    screen.blit(shadow, (x - image.get_width() / 2 + 3, y + 4))
    screen.blit(image, (x - image.get_width() / 2, y))


def button(screen, rect, label, active, accent=YELLOW, sub=None, size=30, disabled=False):
    rect = pygame.Rect(rect)
    if active and not disabled:
        # the active button slides a bit to the right and gets a glow
        rect.x += 6
        glow(screen, rect, accent)
        card(screen, rect, accent, tint(accent, 0.25))
        pygame.draw.rect(screen, accent, (rect.x + 8, rect.y + 10, 4, rect.h - 20), border_radius=2)
        color = accent
    else:
        card(screen, rect, BORDER)
        color = DIM if disabled else WHITE

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


def center_button(screen, rect, label, active, accent=YELLOW, size=28, disabled=False):
    """Button with the label in the middle, for dialogs and action buttons."""
    rect = pygame.Rect(rect)
    if disabled:
        card(screen, rect, BORDER, (30, 28, 42, 220))
        color = DIM
    elif active:
        glow(screen, rect, accent)
        card(screen, rect, accent, tint(accent, 0.35))
        color = WHITE
    else:
        card(screen, rect, tint(accent, 0.6, 255)[:3], tint(accent, 0.12))
        color = accent
    font = sprites.font(size)
    image = font.render(label, True, color)
    screen.blit(image, (rect.centerx - image.get_width() / 2, rect.centery - image.get_height() / 2 + 2))
    return rect


def badge(screen, label, pos, color, align="left", size=18):
    """Small pill with text, returns the rect."""
    image = sprites.font(size).render(label, True, color)
    rect = pygame.Rect(0, 0, image.get_width() + 14, image.get_height() + 4)
    if align == "center":
        rect.midtop = pos
    elif align == "right":
        rect.topright = pos
    else:
        rect.topleft = pos
    card(screen, rect, color, tint(color, 0.2), radius=rect.h // 2)
    screen.blit(image, (rect.x + 7, rect.y + 3))
    return rect


def keycap(screen, label, pos):
    """Draw a keyboard key, returns its width."""
    image = sprites.font(18).render(label, True, WHITE)
    rect = pygame.Rect(pos[0], pos[1], max(22, image.get_width() + 12), 22)
    pygame.draw.rect(screen, (30, 28, 44), rect.move(0, 2), border_radius=5)
    pygame.draw.rect(screen, (62, 60, 86), rect, border_radius=5)
    pygame.draw.rect(screen, (100, 98, 130), rect, 1, border_radius=5)
    screen.blit(image, (rect.centerx - image.get_width() / 2, rect.y + 5))
    return rect.w


def footer(screen, hints):
    """Bar at the bottom with key hints, hints is a list of (key, label)."""
    surface = pygame.Surface((W, FOOTER_HEIGHT), pygame.SRCALPHA)
    surface.fill((8, 6, 18, 190))
    screen.blit(surface, (0, H - FOOTER_HEIGHT))
    pygame.draw.line(screen, (50, 48, 70), (0, H - FOOTER_HEIGHT), (W, H - FOOTER_HEIGHT))

    font = sprites.font(20)
    total = 0
    for key, label in hints:
        total += max(22, font.size(key)[0] + 12) + 6 + font.size(label)[0] + 22
    x = W / 2 - (total - 22) / 2
    y = H - FOOTER_HEIGHT + 6
    for key, label in hints:
        x += keycap(screen, key, (x, y)) + 6
        image = font.render(label, True, GREY)
        screen.blit(image, (x, y + 4))
        x += image.get_width() + 22


def progress_bar(screen, rect, fraction, color, back=(40, 38, 58)):
    rect = pygame.Rect(rect)
    fraction = max(0, min(1, fraction))
    radius = rect.h // 2
    pygame.draw.rect(screen, back, rect, border_radius=radius)
    if fraction > 0:
        fill = pygame.Rect(rect.x, rect.y, max(rect.h, rect.w * fraction), rect.h)
        pygame.draw.rect(screen, color, fill, border_radius=radius)
        # light line on top so it looks a bit shiny
        shine = tuple(min(255, c + 60) for c in color)
        pygame.draw.line(screen, shine, (fill.x + radius, fill.y + 2), (fill.right - radius, fill.y + 2))


def scrollbar(screen, rect, first, visible, total):
    if total <= visible:
        return
    rect = pygame.Rect(rect)
    pygame.draw.rect(screen, (50, 48, 70), rect, border_radius=rect.w // 2)
    height = rect.h * visible / total
    top = rect.y + rect.h * first / total
    pygame.draw.rect(screen, GREY, (rect.x, top, rect.w, height), border_radius=rect.w // 2)


def tabs(screen, rects, labels, active, accent=YELLOW):
    mouse = hovered(rects)
    for i, rect in enumerate(rects):
        rect = pygame.Rect(rect)
        if i == active:
            card(screen, rect, accent, tint(accent, 0.3), radius=10)
            color = WHITE
        else:
            border = GREY if i == mouse else BORDER
            card(screen, rect, border, radius=10)
            color = GREY
        image = sprites.font(26).render(labels[i], True, color)
        screen.blit(image, (rect.centerx - image.get_width() / 2, rect.centery - image.get_height() / 2 + 2))


def check_mark(screen, center, color, size=8):
    x, y = center
    points = [(x - size, y), (x - size / 3, y + size * 0.7), (x + size, y - size * 0.7)]
    pygame.draw.lines(screen, color, False, points, 3)


def lock(screen, center, color):
    x, y = center
    pygame.draw.arc(screen, color, (x - 6, y - 12, 12, 14), 0, 3.15, 2)
    pygame.draw.rect(screen, color, (x - 8, y - 4, 16, 12), border_radius=2)


def hovered(rects, pos=None):
    if pos is None:
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


def wheel(events):
    """How far the mouse wheel moved down this frame (negative is up)."""
    amount = 0
    for event in events:
        if event.type == pygame.MOUSEWHEEL:
            amount -= event.y
    return amount


def navigate(events, selected, rects, columns=1):
    """Mouse and keyboard together. Returns (selected, chosen index or None)."""
    count = len(rects)
    chosen = None
    old = selected
    for event in events:
        if event.type == pygame.MOUSEMOTION:
            index = hovered(rects, event.pos)
            if index is not None:
                selected = index
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = hovered(rects, event.pos)
            if index is not None:
                selected = index
                chosen = index
        elif event.type == pygame.MOUSEWHEEL:
            selected = max(0, min(count - 1, selected - event.y * columns))
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
    if chosen is not None:
        sound.play("menu_select")
    elif selected != old:
        sound.play("menu_move")
    return selected, chosen


def back_button(screen):
    active = BACK_RECT.collidepoint(pygame.mouse.get_pos())
    center_button(screen, BACK_RECT, "< Back", active, GREY, size=24)


def back_clicked(events):
    if clicked(events, [BACK_RECT]) is None:
        return False
    sound.play("menu_back")
    return True


def darken(screen, alpha):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((8, 6, 18, alpha))
    screen.blit(overlay, (0, 0))


def draw_background(screen, state, darkness=150):
    """The world slowly scrolling by behind the menus."""
    t = state["menu_time"]
    camera = pygame.Vector2(t * 30, t * 12)
    state["world"].draw(screen, camera)
    state["world"].draw_roofs(screen, camera)
    ambient.draw(screen, camera, state["world"])
    darken(screen, darkness)


def blur(screen, darkness=140):
    small = pygame.transform.smoothscale(screen, (W // 8, H // 8))
    screen.blit(pygame.transform.smoothscale(small, (W, H)), (0, 0))
    darken(screen, darkness)


# ---------- yes/no question ----------

def confirm_rects():
    return [pygame.Rect(W / 2 - 170, H / 2 + 24, 160, 48), pygame.Rect(W / 2 + 10, H / 2 + 24, 160, 48)]


def handle_confirm(events, selected):
    """Returns (selected, True/False/None). Esc and N mean no."""
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key in (pygame.K_ESCAPE, pygame.K_n):
            return selected, False
        if event.key == pygame.K_y:
            return selected, True
        if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            selected = 1 - selected
            sound.play("menu_move")
    selected, chosen = navigate(events, selected, confirm_rects())
    if chosen is None:
        return selected, None
    return selected, chosen == 0


def draw_confirm(screen, question, detail, selected):
    darken(screen, 160)
    card(screen, (W / 2 - 220, H / 2 - 110, 440, 210), BORDER, (26, 24, 40, 245), shadow=True)
    pygame.draw.rect(screen, YELLOW, (W / 2 - 220, H / 2 - 110, 440, 4), border_radius=2)
    title(screen, question, 42, WHITE, H / 2 - 84)
    if detail:
        title(screen, detail, 24, GREY, H / 2 - 36)
    yes, no = confirm_rects()
    center_button(screen, yes, "Yes", selected == 0, RED)
    center_button(screen, no, "No", selected == 1, GREY)
    text(screen, "Y / N", 20, DIM, (W / 2, H / 2 + 80), "center")
