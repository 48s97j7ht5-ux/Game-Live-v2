import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
packed = json.loads((ROOT / "web/data/chest-targets.json").read_text())
n = len(packed["index"])
assert n > 300, n
rest = packed["rest"]
assert len(rest) == n * 3
for name, values in packed["targets"].items():
    assert len(values) == n * 3, name


def mean_z(name: str) -> float:
    values = packed["targets"][name]
    return sum(values[i + 2] for i in range(0, len(values), 3)) / n


min_z = (mean_z("minCupMinFirm") + mean_z("minCupMaxFirm")) / 2
max_z = (mean_z("maxCupMinFirm") + mean_z("maxCupMaxFirm")) / 2
assert max_z > min_z + 0.002, (min_z, max_z)
assert mean_z("pointIncr") != mean_z("pointDecr")
assert mean_z("distIncr") != mean_z("distDecr")

SIZE_T = [0.42, 0.56, 0.70, 0.85, 1]
FIRMNESS = 0.5
SHAPE_DETAIL = [
    {"pointDecr": 0.7, "volUp": 0.22},
    {"volDown": 0.85, "transDown": 0.42, "pointDecr": 0.18},
    {"pointIncr": 0.9, "distDecr": 0.22, "volUp": 0.12},
    {"distIncr": 0.85, "pointDecr": 0.32},
]


def mix(size_index: int, shape_index: int) -> list[float]:
    size_t = SIZE_T[size_index]
    firm = FIRMNESS
    mixed = [0.0] * (n * 3)
    weights = {
        "minCupMinFirm": (1 - size_t) * (1 - firm),
        "minCupMaxFirm": (1 - size_t) * firm,
        "maxCupMinFirm": size_t * (1 - firm),
        "maxCupMaxFirm": size_t * firm,
    }
    shape_scale = 0.22 + 0.78 * size_t
    for name, amount in SHAPE_DETAIL[shape_index].items():
        weights[name] = amount * shape_scale
    for name, weight in weights.items():
        src = packed["targets"][name]
        for i, value in enumerate(src):
            mixed[i] += value * weight
    return mixed


def mean_component(values: list[float], offset: int) -> float:
    return sum(values[i + offset] for i in range(0, len(values), 3)) / n


def signed_x(values: list[float]) -> float:
    total = 0.0
    for i in range(n):
        rest_x = rest[i * 3]
        sign = 1 if rest_x >= 0 else -1
        total += values[i * 3] * sign
    return total / n


small = mix(0, 1)
large = mix(4, 1)
assert mean_component(large, 2) > mean_component(small, 2) + 0.01
assert signed_x(mix(4, 3)) > signed_x(mix(4, 0))

zs = [rest[i * 3 + 2] for i in range(n)]
front = sorted(zs)[int(n * 0.7)]


def front_dz(values: list[float]) -> float:
    total = 0.0
    count = 0
    for i in range(n):
        if rest[i * 3 + 2] < front:
            continue
        total += values[i * 3 + 2]
        count += 1
    return total / count


for shape_index in range(4):
    assert front_dz(mix(0, shape_index)) > 0.02, shape_index
print("ok", n, "verts", "minZ", round(min_z, 4), "maxZ", round(max_z, 4))
