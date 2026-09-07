"""Exact HP primitive checks, including overkill and same-action revival."""
import random

from tools.boss_ai_fixtures.harness import open_harness, MOVES, TYPES
from tools.boss_ai_fixtures.damage import EFFECTS


def main():
    rng = random.Random(20260908)
    cases = {(maximum, hp, quota)
             for maximum in (1, 2, 127, 128, 192, 255, 256, 999, 32768, 65535)
             for hp in (0, 1, maximum // 2, maximum - 1, maximum)
             for quota in (0, 1, 127, 255, 256, 999, 32768, 65535)}
    for _ in range(2000):
        maximum = rng.randrange(1, 65536)
        cases.add((maximum, rng.randrange(maximum + 1), rng.randrange(65536)))
    with open_harness("pokegold_ai_reference") as h:
        assert h.invoke("OpenSRAM", {"A": 0})
        mem, rf = h.pb.memory, h.pb.register_file
        initial_sp = int(rf.SP)
        mem[0xa000:0xa600] = [0xa5] * 1536

        def run(name, hp, amount, maximum, contribution=0):
            mem[0xa448:0xa44a] = list(hp.to_bytes(2, "big"))
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke(name, {"HL": 0xa448, "A": contribution,
                                   "B": amount >> 8, "C": amount & 255,
                                   "D": maximum >> 8, "E": maximum & 255})
            assert int(rf.SP) == initial_sp
            assert (int(rf.D) << 8 | int(rf.E)) == maximum
            after = bytes(mem[0xa000:0xa600])
            assert before[:0x448] == after[:0x448]
            assert before[0x44a:] == after[0x44a:]
            return int.from_bytes(after[0x448:0x44a], "big"), h.outcome()["bc"]

        for maximum, hp, quota in sorted(cases):
            assert run("BossAI_FastLoseHP", hp, quota, maximum) == (
                max(0, hp - quota), min(hp, quota)), (maximum, hp, quota, "loss")
            assert run("BossAI_FastGainHP", hp, quota, maximum) == (
                min(maximum, hp + quota), min(maximum - hp, quota)), (
                    maximum, hp, quota, "gain")
        # Same-action item damage can reach zero before raw-damage drain.
        hp, _ = run("BossAI_FastLoseHP", 1, 1, 9)
        assert run("BossAI_FastGainHP", hp, 50, 9) == (9, 9)
        self_checks = 0
        for maximum, hp, raw in sorted(cases):
            context = bytearray(51)
            context[47:49] = hp.to_bytes(2, "big")
            context[49:51] = maximum.to_bytes(2, "big")
            mem[0xc900:0xc933] = list(context)
            assert h.invoke("BossAI_ContextDrain", {
                "D": 0xc9, "E": 0, "B": raw >> 8, "C": raw & 255})
            gain = h.outcome()["bc"]
            assert run("BossAI_FastDrainHP", hp, raw, maximum) == (hp + gain, gain)
            for contribution, types in enumerate((("NORMAL", "NORMAL"),
                                                    ("NORMAL", "STEEL"),
                                                    ("STEEL", "STEEL"))):
                mem[0xc909:0xc90b] = [TYPES[t] for t in types]
                assert h.invoke("BossAI_ContextRecoil", {
                    "D": 0xc9, "E": 0, "B": raw >> 8, "C": raw & 255})
                loss = h.outcome()["bc"]
                assert run("BossAI_FastRecoilHP", hp, raw, maximum, contribution) == (
                    hp - loss, loss), (hp, maximum, raw, contribution)
            self_checks += 4
        scripts = {(maximum, hp, target, raw, quota, item, effect, steel)
                   for maximum, hp, target, raw, quota in (
                       (9, 1, 1, 100, 1), (100, 100, 1, 999, 10),
                       (65535, 65534, 65535, 65535, 65535), (1, 1, 1, 0, 1))
                   for item in range(3) for effect in range(3) for steel in range(3)}
        for _ in range(2000):
            maximum = rng.randrange(1, 65536)
            scripts.add((maximum, rng.randrange(1, maximum + 1), rng.randrange(1, 65536),
                         rng.randrange(65536), rng.randrange(65536),
                         rng.randrange(3), rng.randrange(3), rng.randrange(3)))
        for maximum, hp, target, raw, quota, item, effect, steel in sorted(scripts):
            user_ptr, target_ptr = (0xa448, 0xa44a) if raw & 1 else (0xa44a, 0xa448)
            args = (user_ptr.to_bytes(2, "big") + target_ptr.to_bytes(2, "big") +
                    maximum.to_bytes(2, "big") + raw.to_bytes(2, "big") +
                    quota.to_bytes(2, "big") + bytes((steel, item, effect)))
            mem[0xa530:0xa53d] = list(args)
            mem[user_ptr:user_ptr + 2] = list(hp.to_bytes(2, "big"))
            mem[target_ptr:target_ptr + 2] = list(target.to_bytes(2, "big"))
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastDamageScript", {"D": 0xca, "E": 0xfe})
            assert h.outcome()["carry"]
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xcafe
            expected_user, expected_target = hp, target
            if raw:
                expected_target = max(0, target - raw)
                if item == 1:
                    expected_user = max(0, hp - quota)
                elif item == 2:
                    expected_user = min(maximum, hp + quota)
                if effect == 1:
                    expected_user = min(maximum, expected_user + max(1, raw // 2))
                elif effect == 2:
                    recoil = max(1, raw // 4)
                    recoil = 0 if steel == 2 else recoil // 2 if steel == 1 else recoil
                    expected_user = max(0, expected_user - recoil)
            assert int.from_bytes(bytes(mem[user_ptr:user_ptr + 2]), "big") == expected_user
            assert int.from_bytes(bytes(mem[target_ptr:target_ptr + 2]), "big") == expected_target
            assert int.from_bytes(bytes(mem[0xa53d:0xa53f]), "big") == target - expected_target
            after = bytes(mem[0xa000:0xa600])
            assert all(a == b for i, (a, b) in enumerate(zip(before, after))
                       if i not in (0x448, 0x449, 0x44a, 0x44b, 0x53d, 0x53e))
        for offset in (0xa53a, 0xa53b, 0xa53c):
            valid = mem[offset]
            mem[offset] = 3
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastDamageScript", {"D": 0xca, "E": 0xfe})
            assert not h.outcome()["carry"] and bytes(mem[0xa000:0xa600]) == before
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xcafe
            mem[offset] = valid
        quota_checks = 0
        entries = (("RECOVER", "EFFECT_HEAL", None),
                   ("REST", "EFFECT_HEAL", None),
                   ("MORNING_SUN", "EFFECT_MORNING_SUN", 0),
                   ("SYNTHESIS", "EFFECT_SYNTHESIS", 1),
                   ("MOONLIGHT", "EFFECT_MOONLIGHT", 2),
                   ("TACKLE", "EFFECT_NORMAL_HIT", None))
        for move, effect, preferred_time in entries:
            for maximum in (0, 1, 2, 7, 8, 999, 65535):
                for weather in range(4):
                    for time in range(3):
                        for link in (0, 1):
                            h.wr("wTimeOfDay", time)
                            h.wr("wLinkMode", link)
                            if preferred_time is None:
                                denominator = 1 if move == "REST" else 2
                            else:
                                index = 2 - int(not link and time != preferred_time)
                                if weather:
                                    index += 1 if weather == 2 else -1
                                denominator = (8, 4, 2, 1)[index]
                            expected = max(1, maximum // denominator) if maximum else 0
                            supported = move != "TACKLE"
                            if not supported:
                                expected = 0
                            for hp in sorted({0, maximum // 2, maximum}):
                                context = bytearray(51)
                                context[2] = EFFECTS[effect]
                                context[16] = weather
                                context[28] = MOVES[move]
                                context[47:49] = hp.to_bytes(2, "big")
                                context[49:51] = maximum.to_bytes(2, "big")
                                mem[0xc900:0xc933] = list(context)
                                before = bytes(mem[0xa000:0xa600])
                                assert h.invoke("BossAI_FastRecoveryQuota", {"D": 0xc9, "E": 0})
                                assert (h.outcome()["bc"], h.outcome()["carry"]) == (
                                    expected, supported), (move, maximum, weather, time, link, hp)
                                assert int(rf.SP) == initial_sp
                                assert (int(rf.D) << 8 | int(rf.E)) == 0xc900
                                assert bytes(mem[0xc900:0xc933]) == context
                                assert bytes(mem[0xa000:0xa600]) == before
                                assert h.invoke("BossAI_ContextRecovery", {"D": 0xc9, "E": 0})
                                assert (h.outcome()["bc"], h.outcome()["carry"]) == (
                                    min(expected, maximum - hp) if hp else 0, supported)
                                quota_checks += 1
        assert h.invoke("CloseSRAM")
    print(f"PASS: {len(cases) * 2 + 2} native HP transitions; actual amounts, "
          f"{self_checks} drain/recoil and {quota_checks} uncapped recovery/reference checks; "
          f"{len(scripts)} compound damage scripts and 3 tag rejections; "
          "DE/SP and SRAM footprints preserved")


if __name__ == "__main__":
    main()
