import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
packed = json.loads((ROOT / "web/data/body-targets.json").read_text())
n = len(packed["index"])
assert n > 300, n
rest = packed["rest"]
assert len(rest) == n * 3
needed = [
    "minCupMinFirm",
    "maxCupMaxFirm",
    "distDecr",
    "distIncr",
    "pointDecr",
    "pointIncr",
    "transDown",
    "transUp",
    "volDown",
    "volUp",
    "nippleSizeDecr",
    "nippleSizeIncr",
    "nipplePointDecr",
    "nipplePointIncr",
    "stomachBellyDecr",
    "stomachBellyIncr",
    "stomachToneDecr",
    "stomachToneIncr",
    "navelDown",
    "navelUp",
    "navelIn",
    "navelOut",
    "buttDecr",
    "buttIncr",
    "pelvisToneDecr",
    "pelvisToneIncr",
    "hipHorizDecr",
    "hipHorizIncr",
    "hipDepthDecr",
    "hipDepthIncr",
]
for name in needed:
    values = packed["targets"][name]
    assert len(values) == n * 3, name


def mean_z(name: str) -> float:
    values = packed["targets"][name]
    return sum(values[i + 2] for i in range(0, len(values), 3)) / n


min_z = (mean_z("minCupMinFirm") + mean_z("minCupMaxFirm")) / 2
max_z = (mean_z("maxCupMinFirm") + mean_z("maxCupMaxFirm")) / 2
assert max_z > min_z + 0.002, (min_z, max_z)

SIZE_T = [0.42, 0.56, 0.7, 0.85, 1]
FIRMNESS = 0.5
AXIS_STEPS = 7
AXES = {
    "dist": ("distDecr", "distIncr"),
    "point": ("pointDecr", "pointIncr"),
    "trans": ("transDown", "transUp"),
    "vol": ("volUp", "volDown"),
    "nipple": ("nippleSizeDecr", "nippleSizeIncr"),
    "nipplePoint": ("nipplePointDecr", "nipplePointIncr"),
    "belly": ("stomachBellyDecr", "stomachBellyIncr"),
    "butt": ("buttDecr", "buttIncr"),
}


def axis_amount(step: int) -> float:
    return (step / (AXIS_STEPS - 1)) * 2 - 1


def mix(size_index: int, axes: dict[str, int] | None = None) -> list[float]:
    size_t = SIZE_T[size_index]
    firm = FIRMNESS
    mixed = [0.0] * (n * 3)
    weights = {
        "minCupMinFirm": (1 - size_t) * (1 - firm),
        "minCupMaxFirm": (1 - size_t) * firm,
        "maxCupMinFirm": size_t * (1 - firm),
        "maxCupMaxFirm": size_t * firm,
    }
    axes = axes or {}
    for name, weight in weights.items():
        src = packed["targets"][name]
        for i, value in enumerate(src):
            mixed[i] += value * weight
    for axis, (decr, incr) in AXES.items():
        amount = axis_amount(axes.get(axis, 3))
        src = packed["targets"][decr if amount < 0 else incr]
        weight = abs(amount)
        if not weight:
            continue
        for i, value in enumerate(src):
            mixed[i] += value * weight
    return mixed


def signed_x(values: list[float]) -> float:
    total = 0.0
    for i in range(n):
        rest_x = rest[i * 3]
        sign = 1 if rest_x >= 0 else -1
        total += values[i * 3] * sign
    return total / n


def mean_y(values: list[float]) -> float:
    return sum(values[i + 1] for i in range(0, len(values), 3)) / n


small = mix(0)
large = mix(4)
assert sum(large[2::3]) / n > sum(small[2::3]) / n + 0.01
assert signed_x(mix(2, {"dist": 6})) > signed_x(mix(2, {"dist": 0}))
assert mean_y(mix(2, {"trans": 6})) > mean_y(mix(2, {"trans": 0}))
assert sum(mix(2, {"belly": 6})[2::3]) > sum(mix(2, {"belly": 0})[2::3])
assert sum(mix(2, {"butt": 6})[2::3]) < sum(mix(2, {"butt": 0})[2::3])
print("ok", n, "verts", "minZ", round(min_z, 4), "maxZ", round(max_z, 4))
