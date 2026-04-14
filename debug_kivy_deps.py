import sys
try:
    import kivy_deps.sdl2 as s
    print('sdl2', s.__file__)
except Exception as e:
    print('sdl2 error', repr(e))
try:
    import kivy_deps.glew as g
    print('glew', g.__file__)
except Exception as e:
    print('glew error', repr(e))
try:
    import kivy_deps.angle as a
    print('angle', a.__file__)
except Exception as e:
    print('angle error', repr(e))
print('sys.path:', sys.path)
