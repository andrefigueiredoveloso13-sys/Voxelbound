from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import json
import os
import math
import random


def _round_vec(v):
    return (round(v[0]), round(v[1]), round(v[2]))


class ChunkManager:
    def __init__(self, chunk_size=16, view_distance=2):
        self.chunk_size = chunk_size
        self.view_distance = view_distance
        self.chunks = {}
        self.blocks = {}
        self.generate_queue = []

    def chunk_coord(self, x, z):
        cx = math.floor(x / self.chunk_size)
        cz = math.floor(z / self.chunk_size)
        return cx, cz

    def chunk_origin(self, cx, cz):
        return cx * self.chunk_size, cz * self.chunk_size

    def _height_at(self, x, z):
        return int((math.sin(x * 0.12) + math.cos(z * 0.12)) * 2.5 + 3)

    def generate_chunk(self, cx, cz, palette):
        ox, oz = self.chunk_origin(cx, cz)
        positions = []
        for x in range(ox, ox + self.chunk_size):
            for z in range(oz, oz + self.chunk_size):
                h = max(0, min(self._height_at(x, z), 10))
                for y in range(-1, h + 1):
                    pos = (x, y, z)
                    if pos in self.blocks:
                        continue
                    tex = palette[1] if y >= 0 else palette[0]
                    ent = Entity(model='cube', texture=tex, position=pos, collider='box')
                    ent._palette_index = 1 if y >= 0 else 0
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
        px, py, pz = player_pos
        pcx, pcz = self.chunk_coord(px, pz)
        needed = set()
        r = self.view_distance
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                needed.add((pcx + dx, pcz + dz))
        for key in needed:
            if key not in self.chunks and key not in self.generate_queue:
                self.generate_queue.append(key)
        for existing in list(self.chunks.keys()):
            if existing not in needed:
                self.unload_chunk(*existing)

    def process_queue(self, palette, per_frame=1):
        generated = []
        total = len(self.generate_queue)
        for _ in range(min(per_frame, total)):
            if not self.generate_queue:
                break
            cx, cz = self.generate_queue.pop(0)
            self.generate_chunk(cx, cz, palette)
            generated.append((cx, cz))
        return generated, total


class Mob(Entity):
    def __init__(self, position=(0, 0, 0), target=None, texture=None, **kwargs):
        super().__init__(model='cube', texture=texture, scale=0.9, position=position, collider='box', **kwargs)
        self.target = target

    def update(self):
        if not self.target:
            return
        dir = (self.target.position - self.position)
        dir.y = 0
        if dir.length() > 0.1:
            self.position += dir.normalized() * time.dt * 1.5


def main():
    app = Ursina()

    Sky()
    DirectionalLight(parent=scene, rotation=(45, -45, 45))

    player = FirstPersonController(y=1)

    # load textures
    tex_dirt = load_texture('assets/textures/dirt.png')
    tex_grass = load_texture('assets/textures/grass.png')
    tex_stone = load_texture('assets/textures/stone.png')
    tex_wood = load_texture('assets/textures/wood.png')
    tex_mob = load_texture('assets/textures/mob.png')

    palette = [tex_dirt, tex_grass, tex_stone, tex_wood]

    cm = ChunkManager(chunk_size=16, view_distance=2)
    world_file = os.path.join(os.getcwd(), 'world.json')
    cm.update(player.position, palette)

    info = Text(text='Chunks: -- | Blocks: --', origin=(0, 8), background=True)

    hotbar_parent = Entity(parent=camera.ui)
    for i in range(4):
        Entity(parent=hotbar_parent, model='quad', texture=palette[i], scale=0.08, x=-0.12 + i * 0.08, y=-0.42)

    loading_overlay = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 180), scale=2, enabled=False)
    loading_text = Text(parent=camera.ui, text='LOADING...', scale=2, enabled=False)

    def save_world():
        data = []
        for pos, ent in cm.blocks.items():
            idx = getattr(ent, '_palette_index', 0)
            data.append({'pos': pos, 'color_idx': int(idx)})
        with open(world_file, 'w') as f:
            json.dump(data, f)
        info.text = f'Saved {len(data)} blocks'

    def load_world():
        if not os.path.exists(world_file):
            info.text = 'No world.json'
            return
        for key in list(cm.chunks.keys()):
            cm.unload_chunk(*key)
        cm.generate_queue.clear()
        with open(world_file, 'r') as f:
            data = json.load(f)
        for item in data:
            pos = tuple(item['pos'])
            idx = int(item.get('color_idx', 0))
            ent = Entity(model='cube', texture=palette[idx % len(palette)], position=pos, collider='box')
            ent._palette_index = idx
            cm.blocks[pos] = ent
        info.text = f'Loaded {len(data)} blocks'

    prev_chunk = cm.chunk_coord(player.x, player.z)

    def input(key):
        if key == 'f5':
            save_world()
        if key == 'f9':
            load_world()

    def update():
        nonlocal prev_chunk
        cx, cz = cm.chunk_coord(player.x, player.z)
        if (cx, cz) != prev_chunk:
            cm.update(player.position, palette)
            prev_chunk = (cx, cz)
        generated, total = cm.process_queue(palette, per_frame=1)
        if total > 0:
            loading_overlay.enabled = True
            loading_text.enabled = True
            info.text = f'Loading... remaining: {total}'
        else:
            loading_overlay.enabled = False
            loading_text.enabled = False
            info.text = f'Chunks: {len(cm.chunks)} | Blocks: {len(cm.blocks)}'

    app.run()


if __name__ == '__main__':
    main()
