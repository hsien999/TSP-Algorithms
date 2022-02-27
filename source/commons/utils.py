import numpy as np


def set_axes_radius(ax, origin, radius, is_3d=True):
    if is_3d:
        ax.set_xlim3d([origin[0] - radius, origin[0] + radius])
        ax.set_ylim3d([origin[1] - radius, origin[1] + radius])
        ax.set_zlim3d([origin[2] - radius, origin[2] + radius])
    else:
        ax.set_xlim([origin[0] - radius, origin[0] + radius])
        ax.set_ylim([origin[1] - radius, origin[1] + radius])


def set_axes_equal_3d(ax, scale=0.5):
    """
    Make axes of 3D plot have equal scale so that spheres appear as spheres,
    cubes as cubes, etc..  This is one possible solution to Matplotlib's
    ax.set_aspect('equal') and ax.axis('equal') not working for 3D.
    Input
      ax: a matplotlib axis, e.g., as output from plt.gca().
    """
    limits = np.array([
        ax.get_xlim3d(),
        ax.get_ylim3d(),
        ax.get_zlim3d(),
    ])
    origin = np.mean(limits, axis=1)
    radius = scale * np.max(np.abs(limits[:, 1] - limits[:, 0]))
    set_axes_radius(ax, origin, radius)


def set_axes_equal_2d(ax, scale=0.5):
    """See set_axes_equal_3d()"""
    limits = np.array([
        ax.get_xlim(),
        ax.get_ylim(),
    ])
    origin = np.mean(limits, axis=1)
    radius = scale * np.max(np.abs(limits[:, 1] - limits[:, 0]))
    set_axes_radius(ax, origin, radius, False)


def text_wrap(label, width):
    size = len(label)
    width = min(size, width)
    assert size >= 0 and width >= 0
    new_label = ''
    for st in range(0, size, width):
        if st > 0:
            new_label += '\n'
        ed = min(st + width, size)
        new_label += label[st:ed]
    return new_label
