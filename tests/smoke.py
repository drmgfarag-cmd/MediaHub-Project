
import time, requests

BASE = "http://localhost:8000"

def hit(path, method="get", **kw):
    f = getattr(requests, method)
    r = f(BASE+path, **kw, timeout=5)
    print(path, r.status_code)
    return r

print("Run 5x smoke...")
for i in range(5):
    try:
        hit("/integrations/status")
        hit("/api/subs/policy")
        hit("/api/rd/filters/catalog")
        hit("/api/rss/filters/catalog")
        hit("/api/providers/catalog")
    except Exception as e:
        print("Smoke error:", e)
    time.sleep(0.5)
print("Done")


# Stage B quick hits
try:
    hit("/api/dedupe/policy")
    hit("/api/rd/dedupe/preview")
    hit("/api/library/dedupe/preview")
    hit("/api/rd/limits")
except Exception as e:
    print("StageB smoke error:", e)


# Stage E hits
try:
    hit("/api/rd/add", method="post", json={"links":["http://example.com/test"]})
    hit("/api/rd/unrestrict", method="post", json={"links":["http://example.com/test"]})
    hit("/api/scheduler/jobs", method="post", json={"jobs":[{"type":"online_list","provider":"tmdb","preset":"trending","category":"movies","freq":"daily"}]})
    hit("/api/collections/sync", method="post")
    hit("/api/metadata/edit", method="post", json={"category":"movies","index":0,"fields":{"title":"Edited"}})
    hit("/api/subs/download", method="post", json={"title":"Example"})
    hit("/api/organizer/plan", method="post", json={"category":"movies","items":[{"title":"Example","year":2024}]})
    hit("/api/organizer/trash", method="post", json={"paths":["./data/does_not_exist.txt"]})
except Exception as e:
    print("StageE smoke error:", e)


# Stage F hits
try:
    hit("/api/downloader/decrypt_container", method="post", json={"type":"dlc","content":"http://a.com/1\nhttps://b.com/2"})
    hit("/api/downloader/extract", method="post", json={"archives":["C:/tmp/a.rar","C:/tmp/b.7z"]})
    hit("/api/editor/ops", method="post", json={"op":"find","text":"hello world","pattern":"o"})
    hit("/api/collections/rest_all")
    hit("/api/manifest/diff")
    hit("/api/release/gate", method="post")
except Exception as e:
    print("StageF smoke error:", e)


# Stage G hits
try:
    hit("/api/tools/config")
    hit("/api/downloader/decrypt_container_real", method="post", json={"content":"http://x.com/a"})
    hit("/api/downloader/extract_real", method="post", json={"archives":["C:/a.rar"]})
    hit("/api/downloader/limits/hosts", method="post", json={"per_host":{"example.com":{"max_conn":2,"speed_kbps":0},"*":{"max_conn":4,"speed_kbps":0}}})
    hit("/api/downloader/queue/prioritize", method="post", json={"priorities":{}})
    hit("/api/scheduler/run_job", method="post", json={"job":{"type":"online_list","provider":"tmdb","preset":"trending","category":"movies"}})
    hit("/api/editor/actions")
    hit("/api/collections/merge", method="post", json={"category":"movies","sources":["Top 250","Awards"],"target":"Merged","dedupe_by":"name"})
    hit("/api/guard/ui_spec", method="post")
except Exception as e:
    print("StageG smoke error:", e)


# Stage H hits
try:
    hit("/api/tools/config")
    hit("/api/collections/merge_preview", method="post", json={"category":"movies","sources":["A","B"],"dedupe_by":"name"})
    hit("/api/collections/resolve_conflicts", method="post", json={"category":"movies","target":"Merged","winners":["Title 1","Title 2"]})
    hit("/api/logs/extract")
    hit("/api/logs/containers")
except Exception as e:
    print("StageH smoke error:", e)


# Stage I hits
try:
    hit("/api/rd/exclusions")
    hit("/api/rd/exclusions/parse", method="post", json={"text":"magnet:?xt=urn:btih:ABCDEF0123456789&dn=Movie.2024.2160p.mkv"})
    hit("/api/downloader/queue/items")
    hit("/api/downloader/queue/update", method="post", json={"id":"deadbeef","priority":10})
    hit("/opds/feed")
    hit("/opds/search?q=example")
    hit("/api/comics/ingest", method="post", json={"items":[{"title":"Example Comic","year":2024,"issue":1}]})
except Exception as e:
    print("StageI smoke error:", e)


# Stage J hits
try:
    hit("/api/rd/queue/add", method="post", json={"links":["magnet:?xt=urn:btih:ABCDEF0123456789&dn=Movie.2160p.mkv","http://host/file.mkv"]})
    hit("/api/downloader/queue/reorder", method="post", json={"order":[]})
    r = session.get(BASE+"/opds/feed_paginated?page=1&size=1"); print("OPDS paginated", r.status_code, r.headers.get("X-Page"), r.headers.get("X-Total-Count"))
    hit("/api/guard/assets")
except Exception as e:
    print("StageJ smoke error:", e)


# Stage K hits
try:
    hit("/api/downloader/queue/items")
    hit("/api/guard/ui_spec", method="post")
    hit("/api/guard/assets")
except Exception as e:
    print("StageK smoke error:", e)


# Stage L hits
try:
    hit("/api/downloader/pause_all", method="post")
    hit("/api/downloader/resume_all", method="post")
    hit("/api/downloader/clear_completed", method="post")
    hit("/api/downloader/retry_failed", method="post")
except Exception as e:
    print("StageL smoke error:", e)


# Stage M hits
try:
    hit("/api/linkgrabber/parse", method="post", json={"text":"http://example.com/a.mkv\nhttp://dead/link","pack":"Test"})
    hit("/api/linkgrabber/packs", method="post", json={"pack":{"name":"Test","items":[{"url":"http://x"}]}})
    hit("/api/linkgrabber/packs")
    hit("/api/linkgrabber/add_to_queue", method="post", json={"items":["http://x"]})
    hit("/api/downloader/settings", method="post", json={"speed_limit":0,"global_max_running":2})
except Exception as e:
    print("StageM smoke error:", e)


# Stage N hits
try:
    hit("/api/downloader/item/update", method="post", json={"id":"deadbeef","name":"file.mkv"})
    hit("/api/accounts", method="post", json={"account":{"host":"example.com","user":"demo","status":"free"}})
    hit("/api/accounts")
    hit("/api/captcha")
    hit("/api/reconnect")
except Exception as e:
    print("StageN smoke error:", e)


# Stage Q hits
try:
    hit("/api/scheduler")
    hit("/api/containers/import", method="post", json={"text":"http://example.com/a\nhttp://example.com/b","kind":"rsdf"})
    hit("/api/jd/sync", method="post", json={"url":"https://example.com/404.zip"})
except Exception as e:
    print("StageQ smoke error:", e)


# Stage S hits
try:
    hit("/api/downloader/speed")
except Exception as e:
    print("StageS smoke error:", e)
