import sdl2
import sdl2.rect as sdlr
import math

from .virtualization.iscreen import *
from .graphics.colorspace import *

from .matter import *
from .matter.movable import *

from .physics.mathematics import *

###############################################################################
class IPlanetInfo(object):
    def __init__(self, master):
        super(IPlanetInfo, self).__init__()
        self.master = master

class Plane(object):
    def __init__(self, name, initial_mode = 0):
        super(Plane, self).__init__()
        self.info = None
        self.__caption = name
        self.__mode = initial_mode
        self.__background, self.__bg_alpha = -1, 1.0
        self.__mleft, self.__mtop, self.__mright, self.__mbottom = 0.0, 0.0, 0.0, 0.0
        self.__head_matter, self.__focused_matter, self.__hovering_matter = None, None, None
        self.__translate_x, self.__translate_y = 0.0, 0.0
        self.__scale_x, self.__scale_y = 1.0, 1.0
        self.size_cache_invalid()

    def __del__(self):
        self.erase()

# public
    def name(self):
        return self.__caption

    def master(self):
        screen = None

        if self.info:
            screen = self.info.master

        return screen

    def change_mode(self, mode):
        if mode != self.__mode:
            self.no_selected()
            self.__mode = mode
            self.size_cache_invalid()
            self.notify_updated()

    def current_mode(self):
        return self.__mode

    def matter_unmasked(self, m):
        info = __plane_matter_info(self, m)

        return info and __unsafe_matter_unmasked(info, self.__mode)

# public
    def construct(self, Width, Height): pass
    def load(self, Width, Height): pass
    def reflow(self, width, height): pass
    def update(self, count, interval, uptime): pass
    def can_exit(self): return False

    def draw(self, renderer, X, Y, Width, Height):
        dsX, dsY = math.max(0.0, X), math.max(0.0, Y)
        dsWidth, dsHeight = X + Width, Y + Height

        if self.__bg_alpha > 0.0:
            game_fill_rect(renderer, dsX, dsY, dsWidth, dsHeight, self.__background, self.__bg_alpha)

        if self.__head_matter:
            clip = sdlr.SDL_Rect(0, 0, 0, 0)
            child = self.__head_matter

            while True:
                info = child.info

                if __unsafe_matter_unmasked(info, self.__mode):
                    gwidth, gheight = child.get_extent(info.x, info.y)

                    gx = (info.x + self.__translate_x) * self.__scale_x + X
                    gy = (info.y + self.__translate_y) * self.__scale_y + Y

                    if rectangle_overlay(gx, gy, gx + gwidth, gy + gheight, dsX, dsY, dsWidth, dsHeight):
                        clip.x = int(math.floor(gx))
                        clip.y = int(math.floor(gy))
                        clip.w = int(math.ceil(gwidth))
                        clip.h = int(math.ceil(gheight))

                        sdl2.SDL_RenderSetClipRect(renderer, clip)
                        child.draw(renderer, gx, gy, gwidth, gheight)

                        if info.selected:
                            sdl2.SDL_RenderSetClipRect(renderer, None)
                            self.draw_visible_selection(renderer, gx, gy, gwidth, gheight)

                child = info.next
                if child == self.__head_matter:
                    break
            
            sdl2.SDL_RenderSetClipRect(renderer, None)

    def draw_visible_selection(self, renderer, x, y, width, height):
        game_draw_rect(renderer, x, y, width, height, 0x00FFFF)
    
# public
    def find_matter(self, x, y):
        found = None

        if self.__head_matter:
            head_info = self.__head_matter.info
            child = head_info.prev

            while True:
                info = child.info

                if __unsafe_matter_unmasked(info, self.__mode):
                    if not child.concealled():
                        sx, sy, sw, sh = __unsafe_get_matter_bound(child, info)

                        sx += self.__translate_x * self.__scale_x
                        sy += self.__translate_y * self.__scale_y

                        if sx <= x and x <= (sx + sw) and sy <= y and y <= (sy + sh):
                            if child.is_colliding_width_mouse(x - sx, y - sy):
                                found = child
                                break

                child = info.prev

                if child == head_info.prev:
                    break

        return found

    def get_matter_location(self, m, fx, fy):
        info = __plane_matter_info(self, m)
        x, y = False, 0.0

        if info and __unsafe_matter_unmasked(info, self.__mode):
            sx, sy, sw, sh = __unsafe_get_matter_bound(m, info)
            x = sx + sw * fx
            y = sy + sh * fy

        return x, y

    def get_matter_boundary(self, m):
        info = __plane_matter_info(self, m)
        x, y, width, height = False, 0.0, 0.0, 0.0
        
        if info and __unsafe_matter_unmasked(info, self.__mode):
            x, y, width, height = __unsafe_get_matter_bound(m, info)

        return x, y, width, height

    def get_matters_boundary(self):
        self.__recalculate_matters_extent_when_invalid()

        w = self.__mright - self.__mleft
        h = self.__mbottom - self.__mtop

        return self.__mleft, self.__mtop, w, h

    def insert_at(self, m, target, anchor, delta): pass

    def move(self, m, x, y):
        info = __plane_matter_info(self, m)

        if info:
            if __unsafe_matter_unmasked(info, self.__mode):
                if __unsafe_do_moving_via_info(self, info, x, y, False):
                    self.notify_updated()
        elif self.__head_matter:
            child = self.__head_matter

            while True:
                info = child.info

                if info.selected and __unsafe_matter_unmasked(info, self.__mode):
                    __unsafe_do_moving_via_info(self, info, x, y, False)

                child = info.next
                if child == self.__head_matter:
                    break
            
            self.notify_update()
    
    def move_to(self, m, target, anchor, delta): pass
    
    def remove(self, m):
        info = __plane_matter_info(self, m)

        if info and __unsafe_matter_unmasked(info, self.__mode):
            prev_info = info.prev
            next_info = info.next

            prev_info.next = info.next
            next_info.prev = info.prev

            if self.__head_matter == m:
                if self.__head_matter == info.next:
                    self.__head_matter = None
                else:
                    self.__head_matter = info.next

            if self.__hovering_matter == m:
                self.__hovering_matter = None
            
            self.notify_updated()
            self.size_cache_invalid()
    
    def erase(self):
        self.__head_matter = None
        self.size_cache_invalid()

    def size_cache_invalid(self):
        self.__mright = self.__mleft - 1.0

# public
    def find_next_selected_matter(self, start = None):
        found = None

        if start:
            if self.__head_matter:
                found = __do_search_selected_matter(self.__head_matter, self.__mode, self.__head_matter)
        else:
            info = __plane_matter_info(self, start)

            if info and __unsafe_matter_unmasked(info, self.__mode):
                found = __do_search_selected_matter(info.next, self.__mode, self.__head_matter)

        return found
    
    def thumbnail_matter(self): return None

    def add_selected(self, m):
        if self.can_select_multiple():
            info = __plane_matter_info(self, m)

            if info and not info.selected:
                if __unsafe_matter_unmasked(info, self.__mode) and self.can_select(m):
                    __unsafe_add_selected(self, m, info)
    
    def set_selected(self, m):
        info = __plane_matter_info(self, m)

        if info and not info.selected:
            if __unsafe_matter_unmasked(info, self.__mode) and self.can_select(m):
                __unsafe_set_selected(self, m, info)
    
    def no_selected(self):
        if self.__head_matter:
            child = self.__head_matter

            self.begin_update_sequence()

            while True:
                info = child.info

                if info.selected and __unsafe_matter_unmasked(info, self.__mode):
                    self.before_select(child, False)
                    info.selected = False
                    self.after_select(child, False)
                    self.notify_updated()

                child = info.next
                if child == self.__head_matter:
                    break

            self.end_update_sequence()
    
    def count_selected(self):
        n = 0

        if self.__head_matter:
            child = self.__head_matter

            while True:
                info = child.info

                if info.selected and __unsafe_matter_unmasked(info, self.__mode):
                    n += 1

                child = info.next
                if child == self.__head_matter:
                    break

        return n
    
    def is_selected(self, m):
        info = __plane_matter_info(self, m)
        selected = False

        if info and __unsafe_matter_unmasked(self, self.__mode):
            selected = info.selected

        return selected

    def set_background(self, c_hex, a = 1.0):
        self._background = c_hex
        self._bg_alpha = a

    def feed_background(self, sdl_c):
        RGB_FillColor(sdl_c, self.__background, self.__bg_alpha)

    def start_input_text(self, prompt):
        if self.info:
            self.info.master.start_input_text(prompt)

    def log_message(self, message):
        if self.info:
            self.info.log_message(message)

# public
    def on_pointer_pressed(self, button, x, y, clicks, touch):
        handled = False

        if clicks == 1:
            if button == sdl2.SDL_BUTTON_LEFT:
                unmasked_matter = self.find_matter(x, y)

                self.set_caret_owner(unmasked_matter)
                self.no_selected()

                if unmasked_matter and unmasked_matter.low_level_events_allowed():
                    info = unmasked_matter.info
                    local_x = x - info.x
                    local_y = y - info.y
                    handled = unmasked_matter.on_pointer_pressed(button, local_x, local_y)

        return handled

    def on_pointer_released(self, button, x, y, clicks, touch):
        handled = False

        if clicks == 1:
            if button == sdl2.SDL_BUTTON_LEFT:
                unmasked_matter = self.find_matter(x, y)

                if unmasked_matter:
                    info = unmasked_matter.info
                    local_x = x - info.x
                    local_y = y - info.y
                    
                    if unmasked_matter.events_allowed():
                        unmasked_matter.on_tap(local_x, local_y)

                        if unmasked_matter.low_level_events_allowed():
                            unmasked_matter.on_pointer_released(button, local_x, local_y)

                    self.on_tap(unmasked_matter, local_x, local_y)

                    if info.selected:
                        self.on_tap_selected(unmasked_matter, local_x, local_y)

                    handled = info.selected

        return handled

    def on_pointer_move(self, state, x, y, dx, dy, touch):
        handled = False

        if state == 0:
            unmasked_matter = self.find_matter(x, y)

            if unmasked_matter is not self.__hovering_matter:
                self.__say_goodbye_to_hover_matter(state, x, y, dx, dy)

            if unmasked_matter:
                self.__hovering_matter = unmasked_matter
                info = unmasked_matter.info
                local_x = x - info.x
                local_y = y - info.y
                
                if unmasked_matter.events_allowed():
                    unmasked_matter.on_havor(local_x, local_y)

                    if unmasked_matter.low_level_events_allowed():
                        unmasked_matter.on_pointer_move(state, local_x, local_y)
                
                self.on_hover(self.__hovering_matter, local_x, local_y)
                handled = True

        return handled

    def on_scroll(self, horizon, vertical, hprecise, vprecise):
        return False

# public
    # do nothing by default
    def on_focus(self, m, on_off): pass
    def on_tap_selected(self, m, local_x, local_y): pass
    def on_hover(self, m, local_x, local_y): pass
    def on_goodbye(self, m, local_x, local_y): pass
    def on_save(self): pass

    def on_char(self, key, modifiers, repeats, pressed):
        if self.__focused_matter:
            self.__focused_matter.on_char(key, modifiers, repeats, pressed)

    def on_text(self, text, size, entire):
        if self.__focused_matter:
            self.__focused_matter.on_char(text, size, entire)

    def on_editing_text(self, text, pos, span):
        if self.__focused_matter:
            self.__focused_matter.on_editing_text(self, text, pos, span)

    def on_tap(self, m, local_x, local_y):
        if m:
            info = m.info

            if not info.selected:
                if self.can_select(m):
                    __unsafe_set_selected(self, m, info)

                    if m.events_allowed():
                        self.set_caret_owner(m)
                else:
                    self.no_selected()

    def on_elapse(self, count, interval, uptime):
        if self.__head_matter:
            child = self.__head_matter

            while True:
                dwidth, dheight = self.info.master.get_extent()
                info = child.info
                
                if __unsafe_matter_unmasked(info, self.__mode):
                    child.update(count, interval, uptime)

                    if isinstance(child, IMovable):
                        xspd, yspd = child.x_speed(), child.y_speed()
                        hdist, vdist = 0.0, 0.0

                        if xspd != 0.0 or yspd != 0.0:
                            info.x += xspd
                            info.y += yspd

                            cwidth, cheight = child.get_extent(info.x, info.y)
                            
                            if info.x < 0:
                                hdist = info.x
                            elif info.x + cwidth > dwidth:
                                hdist = info.x + cwidth - dwidth

                            if info.y < 0:
                                vdist = info.y
                            elif info.y + cheight > dheight:
                                vdist = info.y + cheight - dheight

                            if hdist != 0.0 or vdist != 0.0:
                                child.on_border(hdist, vdist)
                                xspd = child.x_speed()
                                yspd = child.y_speed()

                                if xspd == 0.0 or yspd == 0.0:
                                    if info.x < 0.0:
                                        info.x = 0.0
                                    elif info.x + cwidth > dwidth:
                                        info.x = dwidth - cwidth

                                    if info.y < 0.0:
                                        info.y = 0.0
                                    elif info.y + cheight > dheight:
                                        info.y = dheight - cheight

                            self.notify_updated()
                child = info.next

                if child == self.__head_matter:
                    break
        
        self.update(count, interval, uptime)
    
# public, do nothing by default
    def can_interactive_move(self, m, local_x, local_y): return False
    def can_select(self, m): return False
    def can_select_multiple(self): return False
    def before_select(self, m, on_or_off): pass
    def after_select(self, m, on_or_off): pass
        
# public
    def get_focused_matter(self):
        if self.matter_unmasked(self.__focused_matter):
            m = self.__focused_matter
        else:
            m = None

        return m
    
    def set_caret_owner(self, m):
        if self.__focused_matter != m:
            if m and m.events_allowed():
                info = __plane_matter_info(self, m)

                if info and __unsafe_matter_unmasked(info, self.__mode):
                    if self.__focused_matter:
                        self.__focused_matter.own_caret(False)
                        self.on_focus(self.__focused_matter, False)
                    
                    self.__focused_matter = m
                    m.own_caret(True)
                    self.on_focus(m, True)
            elif self.__focused_matter:
                self.__focused_matter.own_caret(False)
                self.on_focus(self.__focused_matter, False)
                self.__focused_matter = None
        elif m:
            self.on_focus(m, True)

    def notify_matter_ready(self, m):
        info = __plane_matter_info(self, m)

        if info:
            if info.iasync:
                self.size_cache_invalid()
                self.begin_update_sequence()

                __unsafe_move_async_matter_when_ready(self, m, info)

                self.notify_updated()
                self.on_matter_ready(m)
                self.end_update_sequence()

    def on_matter_ready(self, m): pass

# public
    def begin_update_sequence(self):
        if self.info:
            self.info.master.begin_update_sequence()

    def is_in_update_sequence(self):
        if self.info:
            self.info.master.is_in_update_sequence()
        
    def end_update_sequence(self):
        if self.info:
            self.info.master.end_update_sequence()
        
    def should_update(self):
        if self.info:
            self.info.master.should_update()
        
    def notify_updated(self):
        if self.info:
            self.info.master.notify_updated()

# public
    def snapshot(self, width, height, bgcolor = 0, alpha = 0.0, translation = (0.0, 0.0)):
        saved_bgc, saved_alpha = self.__background, self.__bg_alpha
        x, y = translation

        if x != 0.0:
            width += x

        if y != 0.0:
            height += y

        photograph = game_blank_image(width, height)

        if photograph:
            renderer = sdl2.SDL_CreateSoftwareRenderer(photograph)

            if renderer:
                self.__background = bgcolor
                self.__bg_alpha = alpha

                self.draw(renderer, -x, -y, width, height)
                sdl2.SDL_RenderPresent(renderer)
                sdl2.DestroyRenderer(renderer)

                self.__background = saved_bgc
                self.__bg_alpha = saved_alpha

        return photograph
        
    def save_snapshot(self, pname, width, height, bgcolor = 0, alpha = 0.0, translation = (0.0, 0.0)):
        photograph = self.snapshot(width, height, bgcolor, alpha, translation)
        okay = game_save_image(photograph, pname)

        sdl2.SDL_FreeSurface(photograph)

        return okay

# private
    def __recalculate_matters_extent_when_invalid(self):
        if self.__mright < self.__mleft:
            if self.__head_matter:
                child = self.__head_matter
                self.__mleft, self.__mtop = math.inf, math.inf
                self.__mright, self.__mbottom = -math.inf, -math.inf

                while True:
                    info = child.info

                    if __unsafe_matter_unmasked(info, self.__mode):
                        x, y, w, h = __unsafe_get_matter_bound(child, info)
                        self.__mleft = math.min(self.__mleft, x)
                        self.__mright = math.max(self.__mright, x + w)
                        self.__mtop = math.min(self.__mtop, y)
                        self.__mbottom = math.max(self.__mbottom, y + h)

                    child = info.next
                    if child == self.__head_matter:
                        break
            else:
                self.__mleft, self.__mtop = 0.0, 0.0
                self.__mright, self.__mbottom = 0.0, 0.0

    def __say_goodbye_to_hover_matter(self, state, x, y, dx, dy):
        done = False

        if self.__hovering_matter:
            info = self.__hovering_matter.info
            local_x = x - info.x
            local_y = y - info.y

            if self.__hovering_matter.events_allowed():
                done |= self.__hovering_matter.on_goodbye(local_x, local_y)

                if self.__hovering_matter.low_level_events_allowed():
                    done |= self.__hovering_matter.on_pointer_move(state, local_x, local_y)

                self.on_goodbye(self.__hovering_matter, local_x, local_y)
                self.__hovering_matter = None

        return done

###################################################################################################
class __MatterInfo(IMatterInfo):
    def __init__(self, master, mode):
        super(__MatterInfo, self).__init__(master)
        
        self.mode = mode
        self.x, self.y = 0.0, 0.0
        self.selected = False
        self.iasync = None
        
        self.next, self.prev = None, None

def __bind_matter_owership(master, mode, m):
    info = __MatterInfo(master, mode)

    m.info = info

    return info

def __plane_matter_info(master, m):
    info = None

    if m.info and m.info.master == master:
        info = m.info
    
    return info

def __unsafe_matter_unmasked(info, mode):
    return (info.mode & mode) == info.mode

def __unsafe_get_matter_bound(m, info):
    width, height = m.get_extent(info.x, info.y)

    return info.x, info.y, width, height

def __unsafe_add_selected(master, m, info):
    master.before_select(m, True)
    info.selected = True
    master.after_select(m, True)
    master.notify_updated()

def __unsafe_set_selected(master, m, info):
    master.begin_update_sequence()
    master.no_selected()
    __unsafe_add_selected(master, m, info)
    master.end_update_sequence()

def __matter_anchor_fraction(a):
    fx, fy = 0.0, 0.0

    if a == MatterAnchor.LT: pass
    elif a == MatterAnchor.LC: fy = 0.5
    elif a == MatterAnchor.LB: fy = 1.0
    elif a == MatterAnchor.CT: fx = 0.5          
    elif a == MatterAnchor.CC: fx, fy = 0.5, 0.5
    elif a == MatterAnchor.CB: fx, fy = 0.5, 1.0
    elif a == MatterAnchor.RT: fx = 1.0
    elif a == MatterAnchor.RC: fx, fy = 1.0, 0.5
    elif a == MatterAnchor.RB: fx, fy = 1.0, 1.0

    return fx, fy

def __unsafe_do_moving_via_info(master, info, x, y, absolute):
    moved = False

    if not absolute:
        x += info.x
        y += info.y

    if info.x != x or info.y != y:
        info.x = x
        info.y = y

        master.size_cache_invalid()
        moved = True

    return moved

def __unsafe_move_matter_via_info(master, m, info, x, y, fx, fy, dx, dy, absolute):
    ax, ay = 0.0, 0.0

    if m.ready():
        sx, sy, sw, sh = __unsafe_get_matter_bound(m, info)
        ax = sw * fx
        ay = sh * fy
    else:
        info.iasync = {}
        info.iasync['x0'] = x
        info.iasync['y0'] = y
        info.iasync['fx0'] = fx
        info.iasync['fy0'] = fy
        info.iasync['dx0'] = dx
        info.iasync['dy0'] = dy

    return __unsafe_do_moving_via_info(master, info, x - ax + dx, y - ay + dy, True)

def __unsafe_move_async_matter_when_ready(master, m, info):
    asi = info.iasync
    info.iasync = None

    __unsafe_move_matter_via_info(master, m, info, asi['x0'], asi['y0'], asi['fx0'], asi['fy0'], asi['dx0'], asi['dy0'])

def __do_search_selected_matter(start, mode, terminator):
    found = None
    child = start

    while child != terminator:
        info = child.info

        if info.selected and __unsafe_matter_unmasked(info, mode):
            found = child
            break

        child = info.next

    return found

def __do_resize(master, m, info, scale_x, scale_y, prev_scale_x = 1.0, prev_scale_y = 1.0):
    resizable, resize_anchor = m.resizable()

    if resizable:
        sx, sy, sw, sh = __unsafe_get_matter_bound(m, info)
        fx, fy = __matter_anchor_fraction(resize_anchor)

        m.resize(sw / prev_scale_x * scale_x, sh / prev_scale_y * scale_y)
        nw, nh = m.get_extent(sx, sy)

        nx = sx + (sw - nw) * fx
        ny = sy + (sh - nh) * fy

        __unsafe_do_moving_via_info(master, info, nx, ny, True)

