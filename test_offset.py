from svgpathtools import parse_path, Line, Path, wsvg
def offset_curve(path, offset_distance, steps=1000):
    """Takes in a Path object, `path`, and a distance,
    `offset_distance`, and outputs an piecewise-linear approximation
    of the 'parallel' offset curve."""
    nls = []
    for seg in path:
        ct = 1
        for k in range(steps):
            t = k / steps
            offset_vector = offset_distance * seg.normal(t)
            nl = Line(seg.point(t), seg.point(t) + offset_vector)
            nls.append(nl)
    connect_the_dots = [Line(nls[k].end, nls[k+1].end) for k in range(len(nls)-1)]
    if path.isclosed():
        connect_the_dots.append(Line(nls[-1].end, nls[0].end))
    offset_path = Path(*connect_the_dots)
    return offset_path

# Examples:
path1 = parse_path("m 288,600 c -52,-28 -42,-61 0,-97 ")
path2 = parse_path("M 151,395 C 407,485 726.17662,160 634,339").translated(300)
path3 = parse_path("m 117,695 c 237,-7 -103,-146 457,0").translated(500+400j)
paths = [path1, path2, path3]

offset_distances = [10*k for k in range(1,51)]
offset_paths = []
for path in paths:
    for distances in offset_distances:
        offset_paths.append(offset_curve(path, distances))

# Let's take a look
wsvg(paths + offset_paths, 'g'*len(paths) + 'r'*len(offset_paths), filename='offset_curves.svg')