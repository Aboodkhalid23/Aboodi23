"""DTW, tension peaks, cut/beat phase and colour distance on signals whose answer is known."""
import numpy as np
import pytest

from perception import distance, look, rhythm, tension

FPS = 24


def test_dtw_identical_is_zero_and_warped_is_small():
    t = np.linspace(0, 1, 120)
    a = np.sin(2 * np.pi * 2 * t)
    assert distance.dtw(a, a)[0] == pytest.approx(0.0, abs=1e-12)
    warped = np.sin(2 * np.pi * 2 * t ** 1.3)          # same shape, different timing
    other = np.cos(2 * np.pi * 5 * t)                  # different shape
    assert distance.dtw(a, warped)[0] < 0.1 < distance.dtw(a, other)[0]


def test_dtw_matches_brute_force():
    rng = np.random.default_rng(1)
    a, b = rng.random(17), rng.random(23)
    D = np.full((18, 24), np.inf)
    D[0, 0] = 0
    for i in range(1, 18):
        for j in range(1, 24):
            D[i, j] = abs(a[i - 1] - b[j - 1]) + min(D[i - 1, j - 1], D[i - 1, j], D[i, j - 1])
    cost, path = distance.dtw(a, b, band=1.0)
    assert sum(abs(a[i] - b[j]) for i, j in path) == pytest.approx(D[-1, -1])
    assert path[0] == (0, 0) and path[-1] == (16, 22)


def test_peak_shape_build_breath_hit():
    """Build for 4 s, drop for 0.5 s (the held breath), hit in 2 frames, hold 1 s, release."""
    n = 10 * FPS
    T = np.full(n, 0.1)
    f_build, f_dip, f_hit = 2 * FPS, 6 * FPS, int(6.5 * FPS)
    T[f_build:f_dip] = np.linspace(0.1, 0.6, f_dip - f_build)
    T[f_dip:f_hit] = 0.15
    T[f_hit:f_hit + FPS] = 1.0
    T[f_hit - 1] = 0.6
    T[f_hit + FPS:] = np.linspace(1.0, 0.1, n - f_hit - FPS)
    peaks = tension.describe_peaks(T, FPS)
    p = max(peaks, key=lambda p: p["height"])
    assert p["t"] == pytest.approx(6.5, abs=0.1)
    assert p["breath_depth"] == pytest.approx(0.45, abs=0.05)
    assert p["breath_s"] == pytest.approx(0.5, abs=0.15)
    assert p["rise_frames"] <= 2
    assert p["build_slope"] > 0.05


def test_cut_phase_on_beat_and_on_the_and():
    beats = list(np.arange(0, 20, 0.5))
    on = rhythm.cut_phase([b for b in beats[2:30:2]], beats, FPS)
    assert on["on_beat_ratio"] == 1.0 and on["phase_R"] > 0.99 and min(on["phase_mean"], 1 - on["phase_mean"]) < 0.01
    off = rhythm.cut_phase([b + 0.25 for b in beats[2:30:2]], beats, FPS)
    assert off["on_beat_ratio"] == 0.0 and off["phase_mean"] == pytest.approx(0.5, abs=0.01)
    early = rhythm.cut_phase([b - 1 / FPS for b in beats[2:30:2]], beats, FPS)
    assert early["mean_offset_frames"] == pytest.approx(-1.0, abs=0.01)


def test_colour_distance_is_ordered():
    def solid(L, a, b):
        px = np.zeros((8, 8, 3), np.float32)
        px[..., 0], px[..., 1], px[..., 2] = L, a, b
        return look.normalise(look.hist(px))
    base = solid(50, 10, 20)
    near, far = solid(55, 10, 20), solid(85, 10, 20)
    assert look.wasserstein(base, base)[0] == 0
    assert 0 < look.wasserstein(base, near)[0] < look.wasserstein(base, far)[0]
    assert look.wasserstein(base, far)[0] == pytest.approx(35, abs=4)


def test_invisible_motion_does_not_make_tension():
    """A 1-pixel camera jitter in an otherwise still film must not read as tension (an optimizer exploited this)."""
    n = 10 * FPS
    rng = np.random.default_rng(0)
    base = {"loudness": -20 + 3 * np.sin(np.arange(n) / 30), "flux": rng.random(n)}
    still = tension.curve({**base, "camera": np.zeros(n)}, FPS)
    jitter = np.zeros(n)
    jitter[5 * FPS:5 * FPS + 6] = 2 / 1920 * FPS            # ±1 px a frame for a quarter second
    jittered = tension.curve({**base, "camera": jitter}, FPS)
    assert np.max(np.abs(jittered - still)) < 0.02
    real = np.zeros(n)
    real[5 * FPS:6 * FPS] = 0.6                              # a real whip pan: 0.6 frame widths per second
    assert np.max(tension.curve({**base, "camera": real}, FPS) - still) > 0.08


def test_histogram_mean_is_in_range():
    h = np.zeros((3, look.BINS))
    h[0, 0] = h[0, -1] = 0.5          # half black, half white → L ≈ 50
    h[1, look.BINS // 2] = 1          # a = just above 0
    h[2, 0] = 1                       # b = most blue
    assert look.mean(h, 0) == pytest.approx(50, abs=0.1)
    assert 0 < look.mean(h, 1) < 8 and look.mean(h, 2) == pytest.approx(-128 + 4, abs=0.1)


def test_no_finding_says_both_hold_still():
    still = lambda amt: {"id": 1, "start": 0.0, "end": 2.0, "move": {"kind": ["static"], "amount": amt}}
    _, _, findings = distance.camera_pair(still({"x": 0.012, "y": 0, "z": 0, "r": 0}), still({"x": 0, "y": -0.012, "z": 0, "r": 0}))
    assert not findings
