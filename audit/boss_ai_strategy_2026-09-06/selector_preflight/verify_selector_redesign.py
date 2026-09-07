"""Check arithmetic identities used in the selector design review.
This is not a ROM differential test and does not establish an SM83 cycle bound.
Run: python verify_selector_redesign.py
"""
from bisect import bisect_right
from random import Random


def decode(byte: int) -> int:
    if not 0 <= byte <= 255:
        raise ValueError('accuracy must be an unsigned byte')
    return 256 if byte == 255 else byte


def thresholds(m: int, w: int) -> list[int]:
    step, residue = divmod(m, w)
    t, r = 0, w - 1
    out = []
    for _ in range(w):
        t += step
        r += residue
        if r >= w:
            r -= w
            t += 1
        out.append(t)
    return out


def rank8(m: int, w: int) -> list[tuple[int, int]]:
    """Build by threshold events, not by evaluating every HP fraction."""
    if m < w:
        raise ValueError('rank8 requires maxHP >= weight')
    out = []
    block, base, mask = 0, 0, 0
    value_before = 0
    for t in thresholds(m, w):
        b, j = divmod(t, 8)
        while block < b:
            out.append((base, mask))
            block += 1
            base, mask = value_before, 0
        if j == 0:
            base += 1
        else:
            mask |= 1 << (j - 1)
        value_before += 1
    out.append((base, mask))
    assert len(out) == m // 8 + 1
    return out


def valuation_checks() -> int:
    n = 0
    for w in (128, 192):
        for m in range(1, 2049):
            ts = thresholds(m, w)
            blocks = rank8(m, w) if m >= w else None
            for h in range(m + 1):
                expected = w * h // m
                assert bisect_right(ts, h) == expected
                if blocks is not None:
                    b, j = divmod(h, 8)
                    base, mask = blocks[b]
                    assert base + (mask & ((1 << j) - 1)).bit_count() == expected
                n += 1
        for m in (4095, 16384, 32767, 65535):
            ts = thresholds(m, w)
            for h in (0, 1, m // 3, m // 2, m - 1, m):
                assert bisect_right(ts, h) == w * h // m
                n += 1
    return n


def accumulation_checks() -> int:
    rng = Random(842603)
    n = 0
    masses = [decode(x) for x in (0, 1, 127, 128, 254, 255)]
    for _ in range(20000):
        # Arbitrary deterministic active transitions on a finite state space.
        # Inactive transitions are identity. This includes noncommuting maps.
        vs = [rng.randrange(-384, 577) for _ in range(8)]
        a = [rng.randrange(8) for _ in range(8)]
        r = [rng.randrange(8) for _ in range(8)]
        s = rng.randrange(8)
        p, q = rng.choice(masses), rng.choice(masses)
        da, dr = vs[a[s]] - vs[s], vs[r[s]] - vs[s]
        baseline = 65536 * 1024 + 256 * (p * da + q * dr)
        explicit, factored = [], []
        for own_first in (True, False):
            total = 0
            for own_hit, pa in ((False, 256-p), (True, p)):
                for reply_hit, pr in ((False, 256-q), (True, q)):
                    t = s
                    for fn, active in ((a, own_hit), (r, reply_hit)) if own_first else ((r, reply_hit), (a, own_hit)):
                        if active:
                            t = fn[t]
                    total += pa * pr * (1024 + vs[t] - vs[s])
            # For KO-sensitive real transitions, their maps must include the
            # exact start-of-action reachability gate; identity algebra remains.
            end = r[a[s]] if own_first else a[r[s]]
            kappa = vs[end] - vs[s] - da - dr
            assert -1920 <= kappa <= 1920
            calculated = baseline + p*q*kappa
            assert calculated == total
            explicit.append(total)
            factored.append(calculated)
            n += 1
        for weights in ((2, 0), (0, 2), (1, 1)):
            x = sum(k*t for k,t in zip(weights, explicit))
            y = sum(k*t for k,t in zip(weights, factored))
            assert x == y
            weight = rng.choice((1, 8))
            T, M = weight*x, 2*weight
            assert (T >> 16)//M == T//(M*65536)
            n += 1
        # Grouped hit masses may exceed 16 bits.
        group = [(rng.choice((1,8)), rng.choice(masses)) for _ in range(254)]
        H = sum(w*q for w,q in group)
        Q = sum(w*(256-q) for w,q in group)
        wh = sum(w for w,q in group)
        assert H+Q == wh*256
        combined_k = rng.randrange(-3840, 3841)
        grouped = p*H*combined_k
        assert grouped == sum(w*p*q*combined_k for w,q in group)
        # Negative corrections must be sign-extended into the 40-bit ring.
        mask = (1 << 40)-1
        terms = [rng.randrange(-(1<<31)+1, 1<<31) for _ in range(10)]
        acc = 0
        for t in terms:
            acc = (acc + (t & mask)) & mask
        assert acc == sum(terms) & mask
    return n


def base_checks() -> int:
    rng = Random(244)
    n = 0
    for _ in range(10000):
        level, attack, defense = rng.randrange(1,256), rng.randrange(256), rng.randrange(1,256)
        k = (2*level)//5+2
        step, residue = divmod(5*k*attack, 50*defense)
        q = r = 0
        for p in range(0, 256, 5):
            expected = min(((k*p*attack)//defense)//50,997)+2
            assert min(q,997)+2 == expected
            q += step
            r += residue
            if r >= 50*defense:
                r -= 50*defense
                q += 1
            n += 1
    return n


if __name__ == '__main__':
    print('HP valuation comparisons:', valuation_checks())
    print('transition/accumulation comparisons:', accumulation_checks())
    print('five-power-step base comparisons:', base_checks())
    print('PASS. No ROM behavior or timing has been verified by these checks.')
