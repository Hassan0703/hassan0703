"""Refresh the live numbers inside assets/signal.svg (stdlib only).
Numbers are drawn as vector outlines from glyphs.json — no fonts, no readable text."""
import datetime, json, os, re, urllib.request

USER = os.environ.get("GH_USER", "Hassan0703")
HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, "glyphs.json")))
Q = """query($u:String!){user(login:$u){pullRequests(states:MERGED){totalCount}
contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount}}}}}}"""

req = urllib.request.Request("https://api.github.com/graphql",
                             data=json.dumps({"query": Q, "variables": {"u": USER}}).encode(),
                             headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                                      "Content-Type": "application/json"})
u = json.load(urllib.request.urlopen(req))["data"]["user"]
cal = u["contributionsCollection"]["contributionCalendar"]
days = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]
i = len(days) - 1
if days[i] == 0:
    i -= 1
streak = 0
while i >= 0 and days[i] > 0:
    streak, i = streak + 1, i - 1

vals = {"contrib": f'{cal["totalContributions"]:,}', "days": str(sum(1 for d in days if d)),
        "prs": str(u["pullRequests"]["totalCount"]), "streak": str(streak),
        "date": "UPDATED " + datetime.date.today().strftime("%d %b %Y").upper()}


def outline(text, x, y, size, weight, anchor, ls):
    tbl, sc = G["w"][str(weight)], size / G["upm"]
    width = sum(tbl.get(c, ["", 250])[1] * sc + ls * size for c in text)
    cx = x - (width if anchor == "end" else width / 2 if anchor == "middle" else 0)
    out = []
    for c in text:
        d, adv = tbl.get(c, ["", 250])
        toks = re.findall(r"[MLQCZ]|-?\d+(?:\.\d+)?", d)
        buf, k, nums = [], 0, []
        for t in toks:
            if t in "MLQCZ":
                buf.append(t)
            else:
                v = float(t)
                buf.append(f"{cx + v * sc:.1f}" if k % 2 == 0 else f"{y - v * sc:.1f}")
                buf.append(" ")
                k += 1
        out.append("".join(buf))
        cx += adv * sc + ls * size
    return "".join(out).replace(" M", "M").replace(" L", "L").replace(" Q", "Q").replace(" C", "C").replace(" Z", "Z")


p = "assets/signal.svg"
svg = open(p, encoding="utf-8").read()
for key, v in vals.items():
    m = re.search(rf'<path d="[^"]*"([^>]*id="st-{key}"[^>]*data-t="([^"]+)")', svg)
    if not m:
        continue
    x, y, size, weight, anchor, ls = m.group(2).split(",")
    d = outline(v, float(x), float(y), float(size), int(weight), anchor, float(ls))
    svg = svg[:m.start()] + f'<path d="{d}"' + m.group(1) + svg[m.end():]

weeks = [sum(days[k:k + 7]) for k in range(max(0, len(days) - 364), len(days), 7)][-52:]
mx = max(weeks) or 1
x, y, w, h = map(float, re.search(r'id="st-bars" data-geo="([^"]+)"', svg).group(1).split(","))
bw = w / len(weeks)
bars = "".join(f"M{x + n * bw:.1f} {y + h:.1f}h{bw - 3:.1f}v-{max(2, h * v / mx):.1f}h-{bw - 3:.1f}z"
               for n, v in enumerate(weeks))
svg = re.sub(r'(<path id="st-bars" data-geo="[^"]*" d=")[^"]*(")', rf"\g<1>{bars}\g<2>", svg)
open(p, "w", encoding="utf-8").write(svg)
print(vals)
