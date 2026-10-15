"""Derived geometry and design checks for one enclosure (pure data; no CAD calls).
Frame: x = east, y = north, z up; origin at the cavity centre on the bottom face of the base."""
import math
from encl_config import CONN, BOX

C0 = 299.792458
THREAD = {"M2": dict(d=2.0, tap=1.6, head_d=3.8, head_k=2.0, socket=1.5),
          "M2.5": dict(d=2.5, tap=2.05, head_d=4.5, head_k=2.5, socket=2.0),
          "M3": dict(d=3.0, tap=2.5, head_d=5.5, head_k=3.0, socket=2.5),
          "M2.5_BH": dict(d=2.5, tap=2.05, head_d=4.7, head_k=1.3, socket=1.5)}       # ISO 7380 button head

class Encl:
    def __init__(self, key, b):
        self.key, self.b = key, b
        B = BOX; self.B = B
        self.Lc, self.Wc = b["L"] + 2 * B["clr"], b["W"] + 2 * B["clr"]
        self.Lo, self.Wo = self.Lc + 2 * B["wall"], self.Wc + 2 * B["wall"]
        pin_above_cu = CONN["pin_d"] / 2
        pin_min = CONN["flange"] / 2 + B["flange_margin"]
        self.floor = max(B["floor_min"], pin_min - (b["t"] + b["cu"] + pin_above_cu))
        self.z_pcb_top = self.floor + b["t"] + b["cu"]
        self.pin_z = self.z_pcb_top + pin_above_cu
        self.z_wall = self.z_pcb_top + B["h_air"]
        self.z_top = self.z_wall + B["t_lid"]
        self.ports = [self.port(*p) for p in b["ports"]]
        self.lid_screws = self._lid_screws()
        self.pcb_screws = self._pcb_screws()
        self.mount = self._mount()

    def port(self, label, wall, off, w_trace):
        Lo, Wo = self.Lo / 2, self.Wo / 2
        # outward unit vector, wall-face point, rotation of the connector (STEP mating side = -x)
        d = {"W": ((-1, 0), (-Lo, off), 0.0), "E": ((1, 0), (Lo, off), 180.0),
             "N": ((0, 1), (off, Wo), -90.0), "S": ((0, -1), (off, -Wo), 90.0)}[wall]
        (ux, uy), (fx, fy), rot = d
        tx, ty = -uy, ux                                 # tangent along the wall
        holes = [(fx + s1 * CONN["hole_sq"] / 2 * tx, fy + s1 * CONN["hole_sq"] / 2 * ty, self.pin_z + s2 * CONN["hole_sq"] / 2)
                 for s1 in (-1, 1) for s2 in (-1, 1)]
        return dict(label=label, wall=wall, off=off, w=w_trace, u=(ux, uy), t=(tx, ty), face=(fx, fy), rot=rot, holes=holes,
                    contact=(fx, fy), edge=(fx - ux * self.B["wall"], fy - uy * self.B["wall"]))

    def _wall_track(self):
        """Lid-screw centreline: rectangle inset wall/2 from the outside."""
        a, c = self.Lo / 2 - self.B["wall"] / 2, self.Wo / 2 - self.B["wall"] / 2
        return a, c

    def pitch(self):
        lam = C0 / self.b["band"][1]
        return min(self.B["lid_screw_pitch_max"], max(self.B["lid_screw_pitch_min"], lam / 4))

    def _lid_screws(self):
        """Screws on the wall centreline at <= pitch; one screw right above every port (its short tap stays 0.8 mm
        above the spigot bore); none where the vertical hole would cut a flange thread (|along - 4.32| < 3)."""
        a, c = self._wall_track(); pmax = self.pitch()
        h = CONN["hole_sq"] / 2; band = THREAD["M2.5"]["d"] + 0.5
        def bad(x, y):
            for p in self.ports:
                along = (x - p["face"][0]) * p["t"][0] + (y - p["face"][1]) * p["t"][1]
                across = (x - p["face"][0]) * p["u"][0] + (y - p["face"][1]) * p["u"][1]
                if abs(across) < self.B["wall"] + 0.1 and abs(abs(along) - h) < band: return True
            return False
        out = []
        def add(x, y):
            if not bad(x, y) and all(math.dist((x, y), q) >= BOX["lid_cb_d"] for q in out): out.append((round(x, 3), round(y, 3)))
        for p in self.ports:                                     # above every port
            add(p["face"][0] - p["u"][0] * self.B["wall"] / 2, p["face"][1] - p["u"][1] * self.B["wall"] / 2)
        for x, y in ((-a, -c), (a, -c), (a, c), (-a, c)): add(x, y)
        # fill each side so no gap exceeds the pitch (greedy walk, skipping keep-out bands)
        for (x0, y0), (x1, y1) in (((-a, -c), (a, -c)), ((a, -c), (a, c)), ((a, c), (-a, c)), ((-a, c), (-a, -c))):
            L = math.dist((x0, y0), (x1, y1)); ux, uy = (x1 - x0) / L, (y1 - y0) / L
            for _ in range(3):
                on = sorted(((q[0] - x0) * ux + (q[1] - y0) * uy, q) for q in out
                            if abs((q[0] - x0) * uy - (q[1] - y0) * ux) < 1e-6 and -1e-6 <= (q[0] - x0) * ux + (q[1] - y0) * uy <= L + 1e-6)
                s = [t for t, q in on]
                for k in range(len(s) - 1):
                    gap = s[k + 1] - s[k]
                    if gap > pmax:
                        n = math.ceil(gap / pmax)
                        for j in range(1, n):
                            t = s[k] + gap * j / n
                            for dt in (0, 0.5, -0.5, 1, -1, 1.5, -1.5, 2, -2, 2.5, -2.5, 3, -3):
                                xx, yy = x0 + ux * (t + dt), y0 + uy * (t + dt)
                                if not bad(xx, yy): add(xx, yy); break
        return out

    def _mount(self):
        """4 x M3 from the bottom, in the N and S walls, half-way between lid screws near x = +-Lo/4."""
        yw = self.Wo / 2 - self.B["wall"] / 2; out = []
        for sy in (-1, 1):
            xs = sorted(x for x, y in self.lid_screws if abs(y - sy * yw) < 1e-6)
            for sx in (-1, 1):
                t = sx * self.Lo / 4
                mids = [(xs[k] + xs[k + 1]) / 2 for k in range(len(xs) - 1)] or [t]
                out.append((round(min(mids, key=lambda m: abs(m - t)), 3), round(sy * yw, 3)))
        return out

    def _pcb_screws(self):
        b = self.b; B = self.B; i = B["pcb_corner_inset"]
        pts = [(sx * (b["L"] / 2 - i), sy * (b["W"] / 2 - i)) for sx in (-1, 1) for sy in (-1, 1)]
        for p in self.ports:                                    # two ground screws flanking each launch
            ex, ey = p["edge"]
            for s in (-1, 1):
                pts.append((ex - p["u"][0] * B["launch_screw_dx"] + p["t"][0] * s * B["launch_screw_dy"],
                            ey - p["u"][1] * B["launch_screw_dx"] + p["t"][1] * s * B["launch_screw_dy"]))
        out = []
        for q in pts:
            if all(math.dist(q, r) > 4.5 for r in out): out.append((round(q[0], 3), round(q[1], 3)))
        return out

    # ---------------- checks ----------------
    def checks(self):
        B, b, c = self.B, self.b, CONN
        r = []
        def chk(name, val, lim, ok, unit="mm"): r.append((name, val, lim, ok, unit))
        chk("flange bottom above box bottom", self.pin_z - c["flange"] / 2, ">= %.2f" % B["flange_margin"], self.pin_z - c["flange"] / 2 >= B["flange_margin"] - 1e-9)
        chk("flange top below lid top", self.z_top - (self.pin_z + c["flange"] / 2), ">= 0", self.z_top >= self.pin_z + c["flange"] / 2)
        top_thread = self.pin_z + c["hole_sq"] / 2 + THREAD["M2.5"]["d"] / 2
        chk("upper flange thread below lid seat", self.z_wall - top_thread, ">= 0.5", self.z_wall - top_thread >= 0.5)
        bot_thread = self.pin_z - c["hole_sq"] / 2 - THREAD["M2.5"]["d"] / 2
        chk("lower flange thread above box bottom", bot_thread, ">= 0.5", bot_thread >= 0.5)
        chk("spigot length vs wall", c["spigot_len"] - B["wall"], "0 .. 0.2 (spigot reaches the cavity)", 0 <= c["spigot_len"] - B["wall"] <= 0.2)
        overlap = c["spigot_len"] + c["pin_proj"] - B["wall"] - B["clr"]
        chk("pin length lying on the trace", overlap, ">= 2.0", overlap >= 2.0)
        chk("pin axis above trace (pin resting on copper)", self.pin_z - self.z_pcb_top, "= pin radius %.2f" % (c["pin_d"] / 2), True)
        chk("floor thickness", self.floor, ">= %.1f" % B["floor_min"], self.floor >= B["floor_min"])
        chk("PCB screw thread in floor", self.floor - B["pcb_tap_depth"], ">= 0.8 (blind)", self.floor - B["pcb_tap_depth"] >= 0.8)
        lid_left = B["t_lid"]
        chk("lid screw clear of the lid edge", B["wall"] / 2 - B["lid_clear_d"] / 2, ">= 0.8", B["wall"] / 2 - B["lid_clear_d"] / 2 >= 0.8)
        chk("lid under absorber recess", B["t_lid"] - B["absorber_depth"] - B["engrave_depth"], ">= 2.0", B["t_lid"] - B["absorber_depth"] - B["engrave_depth"] >= 2.0)
        eng = B["lid_screw_len"] - lid_left
        chk("lid screw thread engagement", eng, ">= 1.4 d = 3.5 (light load; helicoil optional)", eng >= 3.5)
        chk("lid screw hole bottom vs tap depth", B["lid_tap_depth"] - eng, ">= 0.5", B["lid_tap_depth"] - eng >= 0.5)
        above_bore = self.z_wall - B["lid_tap_depth"] - (self.pin_z + c["bore_d"] / 2)
        chk("lid tap above the spigot bore", above_bore, ">= 0.8", above_bore >= 0.8 - 1e-9)
        pitch = self.max_screw_gap()
        fmax = b["band"][1]; lam = C0 / fmax
        chk("largest lid-screw gap", pitch, "<= lambda/4 at f_max = %.1f (else conductive gasket)" % (lam / 4), pitch <= lam / 4 + 0.6)
        # connector-to-connector flange clearance on one wall
        for i, p in enumerate(self.ports):
            for q in self.ports[i + 1:]:
                if p["wall"] == q["wall"]:
                    g = abs(p["off"] - q["off"]) - c["flange"]
                    chk("flange gap %s-%s" % (p["label"], q["label"]), g, ">= 2 (spanner/fingers)", g >= 2)
        for p in self.ports:
            along_lim = self.Wc / 2 if p["wall"] in "WE" else self.Lc / 2
            g = along_lim - abs(p["off"]) - c["flange"] / 2 + B["wall"]
            chk("flange inside box outline (%s)" % p["label"], g, ">= 0", g >= 0)
        return r

    def max_screw_gap(self):
        a, c = self._wall_track(); per = 4 * (a + c)
        # position of every screw along the track perimeter
        def s_of(x, y):
            if abs(y + c) < 1e-6: return x + a
            if abs(x - a) < 1e-6: return 2 * a + (y + c)
            if abs(y - c) < 1e-6: return 2 * a + 2 * c + (a - x)
            return 4 * a + 2 * c + (c - y)
        s = sorted(s_of(x, y) for x, y in self.lid_screws)
        gaps = [s[k + 1] - s[k] for k in range(len(s) - 1)] + [per - s[-1] + s[0]]
        return max(gaps)

    def resonances(self, n_max=6):
        """Rectangular-cavity TE_mn0-type modes (E vertical) of the air cavity, empty and with an
        effective permittivity for the PCB filling (layered estimate)."""
        b = self.b; er = b["er"]
        h = self.B["h_air"] + b["t"]
        e_eff = h / (b["t"] / er + self.B["h_air"])          # series layering, E normal to the board
        out = []
        for m in range(1, 5):
            for n in range(1, 5):
                f = C0 / 2 * math.sqrt((m / self.Lc) ** 2 + (n / self.Wc) ** 2)
                out.append((f, m, n, f / math.sqrt(e_eff)))
        out.sort()
        return out[:n_max], e_eff
