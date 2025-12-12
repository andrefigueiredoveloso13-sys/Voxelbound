from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import json
import os
import math

def _round_vec(v):
    return (round(v[0]), round(v[1]), round(v[2]))


class ChunkManager:
    def __init__(self, chunk_size=16, view_distance=2):
        self.chunk_size = chunk_size
        self.view_distance = view_distance
        self.chunks = {}  # (cx, cz) -> list of positions in that chunk
        self.blocks = {}  # pos tuple -> Entity
        self.generate_queue = []  # queue of (cx, cz) to generate

    def chunk_coord(self, x, z):
        cx = math.floor(x / self.chunk_size)
        cz = math.floor(z / self.chunk_size)
        return cx, cz

    def chunk_origin(self, cx, cz):
        return cx * self.chunk_size, cz * self.chunk_size

    def _height_at(self, x, z):
        # deterministic height function (procedural)
        h = int(math.floor((math.sin(x * 0.12) + math.cos(z * 0.12)) * 2.5 + 3))
        return max(0, min(h, 10))

    def generate_chunk(self, cx, cz, palette):
        # synchronous generation of one chunk
        ox, oz = self.chunk_origin(cx, cz)
        positions = []
        for x in range(ox, ox + self.chunk_size):
            for z in range(oz, oz + self.chunk_size):
                h = self._height_at(x, z)
                for y in range(-1, h + 1):
                    pos = (x, y, z)
                    if pos in self.blocks:
                        continue
                    color_idx = 1 if y >= 0 else 0
                    ent = Entity(model='cube', color=palette[color_idx % len(palette)], position=pos, collider='box')
                    self.blocks[pos] = ent
                    positions.append(pos)
        self.chunks[(cx, cz)] = positions

    def unload_chunk(self, cx, cz):
        key = (cx, cz)
        if key not in self.chunks:
            return
        for pos in self.chunks[key]:
            if pos in self.blocks:
                destroy(self.blocks[pos])
                del self.blocks[pos]
        del self.chunks[key]

    def update(self, player_pos, palette):
        # schedule chunk generation/unload (non-blocking)
        px, py, pz = player_pos
        pcx, pcz = self.chunk_coord(px, pz)
        needed = set()
        r = self.view_distance
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                needed.add((pcx + dx, pcz + dz))

        # queue missing
        for key in needed:
            if key not in self.chunks and key not in self.generate_queue:
                self.generate_queue.append(key)

        # unload extras immediately
        for existing in list(self.chunks.keys()):
            if existing not in needed:
                self.unload_chunk(existing)

    def process_queue(self, palette, per_frame=1):
        # generate up to `per_frame` chunks from queue
        generated = 0
        total = len(self.generate_queue)
        generated_keys = []
        while self.generate_queue and generated < per_frame:
            cx, cz = self.generate_queue.pop(0)
            self.generate_chunk(cx, cz, palette)
            generated_keys.append((cx, cz))
            generated += 1
        return generated_keys, total


class Mob(Entity):
    def __init__(self, position=(0,0,0), target=None, world_blocks=None, health=6, speed=2, **kwargs):
        super().__init__(model='cube', texture=tex_mob, scale=0.9, position=position, collider='box', **kwargs)
        self.target = target
        self.world_blocks = world_blocks
        self.health = health
        self.speed = speed
        self.wander_dir = Vec3(random.uniform(-1,1), 0, random.uniform(-1,1))
        self.wander_timer = 0
        # health bar UI above mob
        self.hp_bar = Entity(parent=self, model='quad', scale=(0.6, 0.06), y=1.1, x=0, color=color.green)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()
        else:
            self.hp_bar.scale_x = max(0, self.health / 6)

    def die(self):
        # spawn a small drop
        drop = Entity(model='cube', color=color.rgb(200,180,60), scale=0.4, position=self.position, collider=None)
        destroy(self.hp_bar)
        destroy(self)

    def update(self):
        # simple AI: wander, if target close chase
        if not self.target:
            return
        dist = distance(self.position, self.target.position)
        if dist < 10:
            # chase
            dir = (self.target.position - self.position)
            dir.y = 0
            if dir.length() > 0.1:
                dir = dir.normalized()
                self.position += dir * self.speed * time.dt
        else:
            # wander
            self.wander_timer -= time.dt
            if self.wander_timer <= 0:
                self.wander_timer = random.uniform(1.0, 3.0)
                self.wander_dir = Vec3(random.uniform(-1,1), 0, random.uniform(-1,1)).normalized()
            self.position += self.wander_dir * (self.speed * 0.4) * time.dt

def main():
    app = Ursina()

    Sky()
    directional_light = DirectionalLight(parent=scene, rotation=(45, -45, 45))

    player = FirstPersonController(y=1)

    # palette and UI
        # palette and UI (map to textures)
        tex_dirt = load_texture('assets/textures/dirt.png')
        tex_grass = load_texture('assets/textures/grass.png')
        tex_stone = load_texture('assets/textures/stone.png')
        tex_wood = load_texture('assets/textures/wood.png')
        tex_mob = load_texture('assets/textures/mob.png')

        palette = [tex_dirt, tex_grass, tex_stone, tex_wood]
    info = Text(text='Chunks: -- | Blocks: -- | 1-4 palette | F5 save | F9 load', origin=(0, 8), background=True)

    cm = ChunkManager(chunk_size=16, view_distance=2)

    world_file = os.path.join(os.getcwd(), 'world.json')

    # initial load (schedule)
    cm.update(player.position, palette)

    current_idx = 0

    # --- UI: hotbar & inventory & loading overlay ---
    hotbar_slots = []
    hotbar_size = 9
    slot_spacing = 0.09
    start_x = -((hotbar_size - 1) * slot_spacing) / 2

    hotbar_parent = Entity(parent=camera.ui)
    for i in range(hotbar_size):
        x = start_x + i * slot_spacing
        slot = Entity(parent=hotbar_parent, model='quad', color=color.rgba(50, 50, 50, 200), scale=(0.085, 0.085), x=x, y=-0.42)
        hotbar_slots.append(slot)

    selector = Entity(parent=hotbar_parent, model='quad', color=color.rgba(255, 255, 255, 50), scale=(0.09, 0.09), x=start_x, y=-0.42)

    # inventory panel (hidden by default)
    inventory_open = False
    inv_cols = 9
    inv_rows = 4
    inv_parent = Entity(parent=camera.ui, enabled=False)
        hotbar_size = 9
    inv_bg = Entity(parent=inv_parent, model='quad', color=color.rgba(20, 20, 20, 220), scale=(0.7, 0.5), y=0)
    inv_slots = []
    inv_spacing = 0.07
    top_x = -((inv_cols - 1) * inv_spacing) / 2
    top_y = 0.12
    for r in range(inv_rows):
        for c in range(inv_cols):
            x = top_x + c * inv_spacing
            y = top_y - r * inv_spacing
            s = Entity(parent=inv_parent, model='quad', color=color.rgba(200, 200, 200, 10), scale=(0.06, 0.06), x=x, y=y)
            inv_slots.append(s)

    # loading overlay
    loading_overlay = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 220), scale=2, enabled=False)
    loading_text = Text(parent=camera.ui, text='LOADING...', scale=2, y=0, enabled=False)

    def save_world():
        data = []
        for pos, ent in cm.blocks.items():
            data.append({'pos': pos, 'color_idx': palette.index(ent.color) if ent.color in palette else 0})
        with open(world_file, 'w') as f:
            json.dump(data, f)
        info.text = f'Saved {len(data)} blocks to world.json'

    def load_world():
        if not os.path.exists(world_file):
            info.text = 'No world.json to load.'
            return
        # clear all chunks/blocks
        for key in list(cm.chunks.keys()):
            cm.unload_chunk(*key)
        cm.generate_queue.clear()
        with open(world_file, 'r') as f:
            data = json.load(f)
        for item in data:
                # find texture index
                tex = getattr(ent, 'texture', None)
                color_idx = 0
                if tex == palette[1]:
                    color_idx = 1
                elif tex == palette[2]:
                    color_idx = 2
                elif tex == palette[3]:
                    color_idx = 3
                data.append({'pos': pos, 'color_idx': color_idx})
            idx = int(item.get('color_idx', 0))
            ent = Entity(model='cube', color=palette[idx % len(palette)], position=pos, collider='box')
            cm.blocks[pos] = ent
        info.text = f'Loaded {len(data)} blocks from world.json'

    prev_chunk = cm.chunk_coord(player.x, player.z)

    def update_hotbar():
        # color hotbar slots from palette (looped)
        for i, slot in enumerate(hotbar_slots):
            col = palette[i % len(palette)] if i < len(palette) else color.gray
            slot.color = col
        selector.x = start_x + current_idx * slot_spacing

    update_hotbar()

    def input(key):
        nonlocal current_idx, prev_chunk, inventory_open
        if key in ('1','2','3','4','5','6','7','8','9'):
            idx = int(key) - 1
            if 0 <= idx < hotbar_size:
                current_idx = idx
                update_hotbar()

        if key == 'i':
            inventory_open = not inventory_open
            inv_parent.enabled = inventory_open

        if key == 'left mouse down' and not inventory_open:
            if mouse.world_point is None:
                return
            world_pos = mouse.world_point + mouse.normal * 0.5
            pos = _round_vec(world_pos)
            if pos not in cm.blocks:
                ent = Entity(model='cube', color=palette[current_idx % len(palette)], position=pos, collider='box')
                cm.blocks[pos] = ent

        if key == 'right mouse down' and not inventory_open:
            if mouse.world_point is None:
                return
            pos = _round_vec(mouse.world_point - mouse.normal * 0.5)
            if pos in cm.blocks:
                destroy(cm.blocks[pos])
                del cm.blocks[pos]

        if key == 'f5':
            save_world()
        if key == 'f9':
            load_world()
        if key == 'l':
            directional_light.enabled = not directional_light.enabled

    def update():
        nonlocal prev_chunk
        # schedule update when crossing chunk boundary
        cx, cz = cm.chunk_coord(player.x, player.z)
        if (cx, cz) != prev_chunk:
            cm.update(player.position, palette)
            prev_chunk = (cx, cz)

        # process a small number of chunks per frame so UI remains responsive
        generated_keys, total = cm.process_queue(palette, per_frame=1)
        # spawn mobs for newly generated chunks
        for (gcx, gcz) in generated_keys:
            # choose a few spawn positions within chunk
            ox, oz = cm.chunk_origin(gcx, gcz)
            for sx in range(ox, ox + cm.chunk_size, max(1, cm.chunk_size // 4)):
                for sz in range(oz, oz + cm.chunk_size, max(1, cm.chunk_size // 4)):
                    # find surface height
                    h = cm._height_at(sx, sz)
                    spawn_pos = (sx + 0.5, h + 1, sz + 0.5)
                    # spawn a mob at spawn_pos
                    mob = Mob(position=spawn_pos, target=player, world_blocks=cm.blocks)
                    # keep reference in blocks dict? mobs are tracked by their own list
                    if not hasattr(cm, 'mobs'):
                        cm.mobs = []
                    cm.mobs.append(mob)
        if total > 0:
            loading_overlay.enabled = True
            loading_text.enabled = True
            info.text = f'Loading chunks... remaining: {total}'
        else:
            loading_overlay.enabled = False
            loading_text.enabled = False
            info.text = f'Chunks: {len(cm.chunks)} | Blocks: {len(cm.blocks)} | Palette: {current_idx+1}'

    app.run()
