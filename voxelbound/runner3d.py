from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController


def _round_vec(v):
    return (round(v[0]), round(v[1]), round(v[2]))


def main():
    app = Ursina()

    Sky()
    # simple ground grid
    for x in range(-10, 11):
        for z in range(-10, 11):
            Entity(model='cube', color=color.rgb(100, 160, 100), scale=1, position=(x, -1, z), collider='box')

    player = FirstPersonController(y=1)

    # place some demo blocks
    for x in range(-3, 4):
        for z in range(-3, 4):
            if (x + z) % 2 == 0:
                Entity(model='cube', color=color.light_gray, position=(x, 0, z), collider='box')

    def input(key):
        # place block in front of player
        if key == 'left mouse down':
            hit_info = mouse.hovered_entity
            if hit_info:
                world_pos = mouse.world_point + mouse.normal * 0.5
                pos = _round_vec(world_pos)
                Entity(model='cube', color=color.color(0, 0.7, 0.7), position=pos, collider='box')

        # remove block
        if key == 'right mouse down':
            if mouse.hovered_entity and mouse.hovered_entity.model.name == 'cube':
                destroy(mouse.hovered_entity)

    app.run()
