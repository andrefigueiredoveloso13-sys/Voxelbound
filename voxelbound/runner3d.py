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

    def chunk_coord(self, x, z):
        cx = math.floor(x / self.chunk_size)
        cz = math.floor(z / self.chunk_size)
        return cx, cz

    def chunk_origin(self, cx, cz):
        return cx * self.chunk_size, cz * self.chunk_size

    def _height_at(self, x, z):
        # simple deterministic height function (procedural)
        h = int(math.floor((math.sin(x * 0.12) + math.cos(z * 0.12)) * 2.5 + 3))
        return max(0, min(h, 8))

    def generate_chunk(self, cx, cz, palette):
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
        px, py, pz = player_pos
        pcx, pcz = self.chunk_coord(px, pz)
        needed = set()
        r = self.view_distance
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                needed.add((pcx + dx, pcz + dz))

        # generate missing
        for key in needed:
            if key not in self.chunks:
                self.generate_chunk(key[0], key[1], palette)

        # unload extras
        for existing in list(self.chunks.keys()):
            if existing not in needed:
                self.unload_chunk(existing)


def main():
    app = Ursina()

    Sky()
    directional_light = DirectionalLight(parent=scene, rotation=(45, -45, 45))

    player = FirstPersonController(y=1)

    # palette and UI
    palette = [color.rgb(200, 180, 60), color.light_gray, color.rgb(100, 200, 140), color.rgb(180, 100, 200)]
    info = Text(text='Chunks: -- | Blocks: -- | 1-4 palette | F5 save | F9 load', origin=(0, 8), background=True)

    cm = ChunkManager(chunk_size=16, view_distance=2)

    world_file = os.path.join(os.getcwd(), 'world.json')

    # initial load
    cm.update(player.position, palette)

    current_idx = 0

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
        with open(world_file, 'r') as f:
            data = json.load(f)
        for item in data:
            pos = tuple(item['pos'])
            idx = int(item.get('color_idx', 0))
            ent = Entity(model='cube', color=palette[idx % len(palette)], position=pos, collider='box')
            cm.blocks[pos] = ent
        info.text = f'Loaded {len(data)} blocks from world.json'

    prev_chunk = cm.chunk_coord(player.x, player.z)

    def input(key):
        nonlocal current_idx, prev_chunk
        if key in ('1', '2', '3', '4'):
            idx = int(key) - 1
            if 0 <= idx < len(palette):
                current_idx = idx
                info.text = f'Palette {current_idx+1}'

        if key == 'left mouse down':
            if mouse.world_point is None:
                return
            world_pos = mouse.world_point + mouse.normal * 0.5
            pos = _round_vec(world_pos)
            if pos not in cm.blocks:
                ent = Entity(model='cube', color=palette[current_idx % len(palette)], position=pos, collider='box')
                cm.blocks[pos] = ent

        if key == 'right mouse down':
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
        # update chunks when crossing chunk boundary
        cx, cz = cm.chunk_coord(player.x, player.z)
        if (cx, cz) != prev_chunk:
            cm.update(player.position, palette)
            prev_chunk = (cx, cz)
        info.text = f'Chunks: {len(cm.chunks)} | Blocks: {len(cm.blocks)} | Palette: {current_idx+1}'

    app.run()
