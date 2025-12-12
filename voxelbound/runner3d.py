from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import json
import os


def _round_vec(v):
    return (round(v[0]), round(v[1]), round(v[2]))


def main():
    app = Ursina()

    Sky()
    # directional light for nicer shading
    directional_light = DirectionalLight(parent=scene, rotation=(45, -45, 45))

    # simple ground grid
    for x in range(-10, 11):
        for z in range(-10, 11):
            Entity(model='cube', color=color.rgb(100, 160, 100), scale=1, position=(x, -1, z), collider='box')

    player = FirstPersonController(y=1)

    # block storage: map pos tuple -> Entity
    blocks = {}

    # palette of block types (color palettes can be extended to textures)
    palette = [color.rgb(200, 180, 60), color.light_gray, color.rgb(100, 200, 140), color.rgb(180, 100, 200)]
    current_idx = 0

    info = Text(text='Block: 1 | Left click: place | Right click: remove | 1-4: palette | F5: save | F9: load',
                origin=(0, 8), background=True)

    def place_block(pos, bidx):
        if pos in blocks:
            return
        e = Entity(model='cube', color=palette[bidx], position=pos, collider='box')
        blocks[pos] = e

    def remove_block_at(pos):
        if pos in blocks:
            destroy(blocks[pos])
            del blocks[pos]

    # place some demo blocks
    for x in range(-3, 4):
        for z in range(-3, 4):
            if (x + z) % 2 == 0:
                place_block((x, 0, z), 1)

    world_file = os.path.join(os.getcwd(), 'world.json')

    def save_world():
        data = []
        for pos, ent in blocks.items():
            data.append({'pos': pos, 'color_idx': palette.index(ent.color) if ent.color in palette else 0})
        with open(world_file, 'w') as f:
            json.dump(data, f)
        info.text = f'Saved {len(data)} blocks to world.json'

    def load_world():
        if not os.path.exists(world_file):
            info.text = 'No world.json to load.'
            return
        # clear existing
        for pos in list(blocks.keys()):
            remove_block_at(pos)
        with open(world_file, 'r') as f:
            data = json.load(f)
        for item in data:
            pos = tuple(item['pos'])
            idx = int(item.get('color_idx', 0))
            place_block(pos, idx)
        info.text = f'Loaded {len(data)} blocks from world.json'

    def input(key):
        nonlocal current_idx
        # change palette
        if key in ('1', '2', '3', '4'):
            idx = int(key) - 1
            if 0 <= idx < len(palette):
                current_idx = idx
                info.text = f'Block: {current_idx+1} | Left click: place | Right click: remove | F5: save | F9: load'

        # place block in front of player
        if key == 'left mouse down':
            if mouse.world_point is None:
                return
            world_pos = mouse.world_point + mouse.normal * 0.5
            pos = _round_vec(world_pos)
            place_block(pos, current_idx)

        # remove block
        if key == 'right mouse down':
            if mouse.world_point is None:
                return
            pos = _round_vec(mouse.world_point - mouse.normal * 0.5)
            remove_block_at(pos)

        # save/load
        if key == 'f5':
            save_world()
        if key == 'f9':
            load_world()

        # toggle light intensity
        if key == 'l':
            directional_light.enabled = not directional_light.enabled
            info.text = f'Light: {"on" if directional_light.enabled else "off"}'

    app.run()
