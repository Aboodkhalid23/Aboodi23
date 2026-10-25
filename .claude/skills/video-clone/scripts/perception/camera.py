"""Global camera motion between consecutive frames, and the motion that is left once the camera is accounted for.

Model: the image of frame k+1 is a similarity transform of frame k about the frame centre,

    p' = s · R(θ) · p + t          (p measured from the centre, in pixels)

estimated robustly from sparse tracks:

    Shi–Tomasi corners → pyramidal Lucas–Kanade → forward–backward consistency check → RANSAC similarity.

The result is reported in *camera* terms, so a plan can say what the camera did:

    dx  camera moves right (+) / left (−), in frame widths        (image content moves the other way)
    dy  camera moves down  (+) / up   (−), in frame widths
    dz  log scale: push in (+) / pull out (−)                      (ln 1.1 ≈ 0.095 = a 10 % push)
    dr  camera roll in radians, + = clockwise roll (image turns counter-clockwise)

`local` is the median residual of all tracked points after removing the global transform, in frame widths: characters
moving, things falling, a hand waving — motion the camera did not cause.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np

MIN_TRACKS = 12          # fewer usable tracks than this → no estimate (black stage, flat colour field)
FB_MAX_ERR = 1.0         # px: a track that does not come back to where it started is dropped
RANSAC_PX = 1.0          # px: inlier threshold for the similarity fit
MIN_INLIER_RATIO = 0.3   # below this the "camera" is really several things moving: the estimate is not trusted
PHOTO_MAX_ERR = 0.06     # a warp that leaves less mean abs error than this (0–1) is always accepted
PHOTO_GAIN = 0.75        # otherwise it must explain at least 25 % of the change between the two frames
BG_MARGIN = 0.06         # the moving subject's region is grown by this share of the width before "the rest" is judged
BG_MIN_SHARE = 0.2       # the rest must be at least this share of the frame to be evidence
BG_SPREAD = 0.15         # background tracks must spread over this share of the frame: a burned-in caption strip is
                         # many corners in a thin band that never moves, not evidence about the world
BG_SAME = 0.0015         # the rest did not change at all (mean abs difference, 0–1): nothing there moved
BG_GAIN = 0.85           # a camera move must explain the rest at least 15 % better than standing still
MIN_BG_TRACKS = 8        # background tracks needed to measure the camera from the background alone

_LK = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))


@dataclass(frozen=True)
class Step:
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0
    dr: float = 0.0
    local: float = 0.0
    ok: bool = False
    tracks: int = 0


def estimate(prev_gray: np.ndarray, gray: np.ndarray, mask: np.ndarray | None = None) -> Step:
    """Camera motion from prev_gray to gray (both single-channel uint8, same size). `mask` (255 = usable) keeps corners
    off static overlays."""
    h, w = gray.shape
    pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=500, qualityLevel=0.01, minDistance=7, blockSize=7, mask=mask)
    if pts is None or len(pts) < MIN_TRACKS:
        return Step()
    nxt, st1, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, pts, None, **_LK)
    back, st2, _ = cv2.calcOpticalFlowPyrLK(gray, prev_gray, nxt, None, **_LK)
    fb = np.linalg.norm((pts - back).reshape(-1, 2), axis=1)
    good = (st1.ravel() == 1) & (st2.ravel() == 1) & (fb < FB_MAX_ERR)
    if good.sum() < MIN_TRACKS:
        return Step(tracks=int(good.sum()))
    centre = np.array([w / 2, h / 2], np.float32)
    p0 = pts.reshape(-1, 2)[good] - centre
    p1 = nxt.reshape(-1, 2)[good] - centre
    M, inl = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=RANSAC_PX,
                                         maxIters=2000, confidence=0.995)
    if M is None or inl is None or inl.mean() < MIN_INLIER_RATIO:
        return Step(tracks=int(good.sum()))
    if not photometric_ok(prev_gray, gray, M, centre):
        return Step(tracks=int(good.sum()))
    # Camera motion is motion against the world. When the tracks that agree sit on one subject, the background decides:
    # its own tracks (searched for separately, so faint detail like sparkles counts), else whether it changed at all.
    region = subject_region(gray.shape, p1[inl.ravel() == 1] + centre)
    if region is not None:
        bg = background_motion(prev_gray, gray, region, centre)
        if bg is not None:
            M = bg
        elif background_says_still(prev_gray, gray, M, centre, region):
            # a subject moved over a plain background, not the camera: that is motion inside the frame
            return Step(local=float(np.median(np.linalg.norm(p1 - p0, axis=1))) / w, ok=True, tracks=int(good.sum()))
    a, b, tx, ty = M[0, 0], M[1, 0], M[0, 2], M[1, 2]
    scale, theta = math.hypot(a, b), math.atan2(b, a)
    residual = np.linalg.norm(p1 - (p0 @ M[:, :2].T + M[:, 2]), axis=1)
    return Step(dx=-tx / w, dy=-ty / w, dz=math.log(scale), dr=-theta, local=float(np.median(residual)) / w,
                ok=True, tracks=int(good.sum()))


def _warp(prev_gray: np.ndarray, M: np.ndarray, centre: np.ndarray) -> np.ndarray:
    h, w = prev_gray.shape
    A = M[:, :2]
    full = np.hstack([A, (M[:, 2] + centre - A @ centre)[:, None]]).astype(np.float32)
    return cv2.warpAffine(prev_gray, full, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def subject_region(shape: tuple[int, int], inliers: np.ndarray) -> np.ndarray | None:
    """Mask of what the agreeing tracks cover (grown a little), or None when they cover most of the frame — then the
    whole frame moved together, and that is the camera."""
    h, w = shape
    if len(inliers) < 3:
        return None
    region = np.zeros((h, w), np.uint8)
    cv2.fillConvexPoly(region, cv2.convexHull(inliers.astype(np.int32)), 255)
    k = max(3, int(BG_MARGIN * w)) | 1
    region = cv2.dilate(region, np.ones((k, k), np.uint8))
    return region if (_inner(shape) & (region == 0)).mean() >= BG_MIN_SHARE else None


def _inner(shape: tuple[int, int]) -> np.ndarray:
    h, w = shape
    m = np.zeros((h, w), bool)
    m[h // 10:h - h // 10, w // 10:w - w // 10] = True   # the warp fills the borders in
    return m


def background_motion(prev_gray: np.ndarray, gray: np.ndarray, region: np.ndarray, centre: np.ndarray) -> np.ndarray | None:
    """The background's own motion, from corners searched for outside the subject with a low threshold (a plain
    background's only detail — sparkles, a horizon, a texture — is weak next to a character's outlines)."""
    bg_mask = np.where(region == 0, 255, 0).astype(np.uint8)
    pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=300, qualityLevel=0.001, minDistance=7, blockSize=7, mask=bg_mask)
    if pts is None or len(pts) < MIN_BG_TRACKS:
        return None
    nxt, st1, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, pts, None, **_LK)
    back, st2, _ = cv2.calcOpticalFlowPyrLK(gray, prev_gray, nxt, None, **_LK)
    good = (st1.ravel() == 1) & (st2.ravel() == 1) & (np.linalg.norm((pts - back).reshape(-1, 2), axis=1) < FB_MAX_ERR)
    if good.sum() < MIN_BG_TRACKS:
        return None
    M, inl = cv2.estimateAffinePartial2D(pts.reshape(-1, 2)[good] - centre, nxt.reshape(-1, 2)[good] - centre, method=cv2.RANSAC,
                                         ransacReprojThreshold=RANSAC_PX, maxIters=2000, confidence=0.995)
    if M is None or inl is None or inl.mean() < 0.5:
        return None
    agree = pts.reshape(-1, 2)[good][inl.ravel() == 1]
    if len(agree) < 3 or cv2.contourArea(cv2.convexHull(agree.astype(np.float32))) < BG_SPREAD * prev_gray.size:
        return None
    return M


def background_says_still(prev_gray: np.ndarray, gray: np.ndarray, M: np.ndarray, centre: np.ndarray, region: np.ndarray) -> bool:
    """No trackable background: if moving the camera explains the rest of the frame no better than not moving it, the
    camera stood still and the subject moved. Without background evidence the simpler answer wins (a head tilt read as
    a 2.5° camera roll on a real film is what this fixes)."""
    bg = _inner(gray.shape) & (region == 0)
    err_still = float(np.mean(cv2.absdiff(prev_gray, gray)[bg])) / 255
    err_warp = float(np.mean(cv2.absdiff(_warp(prev_gray, M, centre), gray)[bg])) / 255
    return err_still < BG_SAME or err_warp > BG_GAIN * err_still


def photometric_ok(prev_gray: np.ndarray, gray: np.ndarray, M: np.ndarray, centre: np.ndarray) -> bool:
    """Verify the fit on the pixels, not only on the tracks: warping the previous frame by the estimated transform must
    explain the current one clearly better than not moving at all. Between two unrelated pictures (a cut the shot list
    missed by a frame, a hard transition) RANSAC still finds *some* similarity; this is where it is caught."""
    h, w = gray.shape
    warped = _warp(prev_gray, M, centre)
    my, mx = h // 10, w // 10   # borders are filled in by the warp
    inner = (slice(my, h - my), slice(mx, w - mx))
    err_warp = float(np.mean(cv2.absdiff(warped[inner], gray[inner]))) / 255
    err_still = float(np.mean(cv2.absdiff(prev_gray[inner], gray[inner]))) / 255
    return err_warp <= max(PHOTO_MAX_ERR, PHOTO_GAIN * err_still)


def hsv_hist(bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256])
    return cv2.normalize(h, h).ravel()


def looks_like_cut(prev_hist: np.ndarray, hist: np.ndarray, prev_gray: np.ndarray, gray: np.ndarray) -> bool:
    """A hard cut: the colour distribution and the pixels both change at once (a fast pan changes pixels, not colours)."""
    corr = cv2.compareHist(prev_hist.astype(np.float32), hist.astype(np.float32), cv2.HISTCMP_CORREL)
    diff = float(np.mean(cv2.absdiff(prev_gray, gray))) / 255
    return corr < 0.6 and diff > 0.12
