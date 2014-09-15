import cocos

from cocos.actions import *

class HelloActions(cocos.layer.ColorLayer):
    def __init__(self):
        super(HelloActions, self).__init__(64, 64, 224, 255)
        label = cocos.text.Label('Hello, World!',
                                 font_name='Times New Roman',
                                 font_size=32,
                                 anchor_x='center',
                                 anchor_y='center')
        label.position = 320, 240
        self.add(label)

        sprite = cocos.sprite.Sprite('grossini.png')
        sprite.position = 320, 240
        sprite.scale = 3
        self.add(sprite, z=1)

        scale = ScaleBy(3, duration=2)

        label.do(Repeat(scale + Reverse(scale)))
        sprite.do(Repeat(Reverse(scale) + scale))

cocos.director.director.init()
hello_layer = HelloActions()

def Blink(times, duration):
    return (
        Hide() + Delay(duration/(times*2)) +
        Show() + Delay(duration/(times*2))
    ) * times


# hello_layer.do(RotateBy(360, duration=10))
# hello_layer.do( Twirl( grid=(16,12), duration=4) )
# hello_layer.do( Lens3D( grid=(32,24), duration=5 ))
# hello_layer.do(Blink(2, 2))
main_scene = cocos.scene.Scene(hello_layer)

cocos.director.director.run(main_scene)
