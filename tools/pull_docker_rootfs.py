"""Pull a Docker Hub image (amd64) and unpack it as a rootfs, applying whiteouts. No daemon needed.
DOCKER_MIRROR=mirror.gcr.io pulls through Google's anonymous Docker Hub mirror (no 429 rate limit)."""
import hashlib, json, os, shutil, sys, tarfile, urllib.request
repo, tag, dest = sys.argv[1], sys.argv[2], sys.argv[3]
def get(url, tok=None, accept=None):
    h = {}
    if tok: h["Authorization"] = "Bearer " + tok
    if accept: h["Accept"] = accept
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=600)
MIRROR = os.environ.get("DOCKER_MIRROR")
tok = None if MIRROR else json.load(get(f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull"))["token"]
R = f"https://{MIRROR or 'registry-1.docker.io'}/v2/{repo}"
idx = json.load(get(f"{R}/manifests/{tag}", tok, "application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.index.v1+json"))
dig = next(m["digest"] for m in idx["manifests"] if m["platform"]["architecture"] == "amd64")
man = json.load(get(f"{R}/manifests/{dig}", tok, "application/vnd.docker.distribution.manifest.v2+json,application/vnd.oci.image.manifest.v1+json"))
os.makedirs(dest, exist_ok=True)
cache = dest + ".blobs"; os.makedirs(cache, exist_ok=True)
for i, L in enumerate(man["layers"]):
    print(f"layer {i+1}/{len(man['layers'])} {L['size']/1e6:.0f} MB", flush=True)
    blob = os.path.join(cache, L["digest"].split(":")[1])
    for attempt in range(6):
        if os.path.exists(blob) and os.path.getsize(blob) == L["size"]: break
        auth = f'-H "Authorization: Bearer {tok}"' if tok else ""
        os.system(f'curl -fsSL --retry 5 -C - {auth} -o {blob} {R}/blobs/{L["digest"]}')
    assert hashlib.sha256(open(blob, "rb").read()).hexdigest() == L["digest"].split(":")[1], "checksum"
    with tarfile.open(blob, mode="r:*") as t:
        for m in t:
            d, b = os.path.split(m.name)
            if b.startswith(".wh."):
                tgt = os.path.join(dest, d, b[4:])
                if b == ".wh..wh..opq":
                    p = os.path.join(dest, d)
                    for x in os.listdir(p) if os.path.isdir(p) else []:
                        q = os.path.join(p, x); shutil.rmtree(q) if os.path.isdir(q) and not os.path.islink(q) else os.remove(q)
                elif os.path.lexists(tgt):
                    shutil.rmtree(tgt) if os.path.isdir(tgt) and not os.path.islink(tgt) else os.remove(tgt)
                continue
            p = os.path.join(dest, m.name)
            if os.path.lexists(p) and not (m.isdir() and os.path.isdir(p)):
                shutil.rmtree(p) if os.path.isdir(p) and not os.path.islink(p) else os.remove(p)
            t.extract(m, dest, set_attrs=True, numeric_owner=True, filter="fully_trusted") if sys.version_info >= (3, 12) else t.extract(m, dest, set_attrs=True, numeric_owner=True)
print("digest", dig)
