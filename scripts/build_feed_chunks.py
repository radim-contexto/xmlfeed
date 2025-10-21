import os, json, re, math, xml.etree.ElementTree as ET

SRC_XML = "universal.xml"              # kořen repa
OUT_DIR = "data"                       # výstupy v repu
CHUNK_DIR = os.path.join(OUT_DIR, "chunks")
CHUNK_SIZE = 1200                      # klidně 1000–2000

def safe_num(v):
    if v is None: return None
    s = str(v).replace(" ", "").replace(",", ".")
    try: return float(s)
    except: return None

def extract_scale(product):
    if not product: return None
    m = re.search(r"\b(\d{1,2}:\d{1,2})\b", product)
    return m.group(1) if m else None

def clean_model(product, manufacturer, scale):
    model = product or ""
    if manufacturer and model.lower().startswith((manufacturer + " ").lower()):
        model = model[len(manufacturer):].strip()
    if scale:
        model = re.sub(r"\b" + re.escape(scale) + r"\b", "", model).strip()
    model = re.sub(r"\s{2,}", " ", model).strip()
    return model

def main():
    os.makedirs(CHUNK_DIR, exist_ok=True)
    tree = ET.parse(SRC_XML)
    root = tree.getroot()  # SHOP
    rows = []

    for item in root.findall("SHOPITEM"):
        def get(tag):
            el = item.find(tag)
            return el.text.strip() if el is not None and el.text else None

        product = get("PRODUCT")
        manufacturer = get("MANUFACTURER") or None
        scale = extract_scale(product)
        if not manufacturer and product:
            manufacturer = product.split(" ")[0]

        row = {
            "PRODUCT": product,
            "MANUFACTURER": manufacturer,
            "modelClean": clean_model(product, manufacturer, scale),
            "scale": scale,
            "PRICE_VAT": safe_num(get("PRICE_VAT") or get("PRICE")),
            "URL": get("URL"),
            "EAN": get("EAN"),
            "CATEGORYTEXT": get("CATEGORYTEXT") or get("CATEGORY") or "",
            "_path": (get("CATEGORYTEXT") or get("CATEGORY") or "")
        }
        rows.append(row)

    total = len(rows)
    chunks = math.ceil(total / CHUNK_SIZE)

    # chunk soubory
    for i in range(chunks):
        part = rows[i*CHUNK_SIZE:(i+1)*CHUNK_SIZE]
        with open(os.path.join(CHUNK_DIR, f"chunk-{i:03}.json"), "w", encoding="utf-8") as f:
            json.dump(part, f, ensure_ascii=False, separators=(",", ":"))

    # index: metainfo + agregace kategorií
    cat_count = {}
    for r in rows:
        p = r["_path"] or ""
        cat_count[p] = cat_count.get(p, 0) + 1
    categories = [{"path": p,
                   "level": len([s for s in p.split("|") if s.strip()]),
                   "count": c} for p, c in sorted(cat_count.items())]

    index = {
        "ok": True,
        "total": total,
        "chunkSize": CHUNK_SIZE,
        "chunks": chunks,
        "basePath": "data/chunks/chunk-XXX.json",
        "categories": categories[:4000]  # pro jistotu strop
    }
    with open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

if __name__ == "__main__":
    main()
    
