#!/usr/bin/env python3
"""Populate article link.image fields from publisher OGP share metadata.

No image files are copied into this repository. Only image URLs intentionally
advertised on the corresponding official news pages are referenced. A missing
or inaccessible preview is left empty, not fabricated.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from html.parser import HTMLParser
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_DOMAINS = (
    'disney.co.jp', 'tokyodisneyresort.jp', 'disneyhotels.jp',
    'aniplex.co.jp', 'colyinc.com', 'olc.co.jp'
)


def official_host(host: str) -> bool:
    host = host.lower().rstrip('.')
    return any(host == domain or host.endswith('.' + domain) for domain in OFFICIAL_DOMAINS)


def is_public_https(url: str) -> bool:
    try:
        u = urlsplit(url)
        if u.scheme != 'https' or not u.hostname or u.username or u.password or u.port not in (None, 443):
            return False
        if u.hostname in ('localhost', 'localhost.localdomain') or u.hostname.endswith(('.local','.internal')):
            return False
        try:
            ip = ipaddress.ip_address(u.hostname)
            return ip.is_global
        except ValueError:
            return True
    except (ValueError, TypeError):
        return False


class OfficialRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if not is_public_https(newurl) or not official_host(urlsplit(newurl).hostname or ''):
            return None
        return super().redirect_request(request, fp, code, msg, headers, newurl)


class ImageMetadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = {}
    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'meta':
            return
        a = {k.lower():v for k,v in attrs if k and isinstance(v,str)}
        name = (a.get('property') or a.get('name') or '').lower()
        if name in ('og:image:secure_url','og:image','twitter:image'):
            self.images.setdefault(name, a.get('content', '').strip())


def image_for_article(url: str) -> str | None:
    if not is_public_https(url):
        return None
    u = urlsplit(url)
    if not official_host(u.hostname or ''):
        return None
    path = u.path.lower().rstrip('/')
    if not path or path.endswith('.pdf') or '/news/list' in path:
        return None
    # Strip OpenAI source tagging from outgoing requests, preserve original link in the JSON.
    address = urlunsplit((u.scheme, u.netloc, u.path, '', ''))
    opener = build_opener(OfficialRedirect())
    req = Request(address, headers={
        'User-Agent': 'LiluelRadio/1.0 (article-link-preview; no-image-download)',
        'Accept': 'text/html,application/xhtml+xml'
    })
    try:
        with opener.open(req, timeout=9) as response:
            if 'html' not in response.headers.get('Content-Type', '').lower():
                return None
            data = response.read(600_000)
            charset = response.headers.get_content_charset() or 'utf-8'
            text = data.decode(charset, 'replace')
            page = response.geturl()
    except Exception:
        return None
    parser = ImageMetadata()
    try:
        parser.feed(text)
    except Exception:
        return None
    for key in ('og:image:secure_url','og:image','twitter:image'):
        raw = parser.images.get(key)
        if not raw:
            continue
        image = urljoin(page, raw)
        if is_public_https(image) and not re.search(r'/(?:favicon|noimage|default-logo)(?:[._/]|$)', image, re.I):
            return image
    return None


def enrich_episode(file: Path, overwrite: bool = False) -> tuple[int, int]:
    try:
        episode = json.loads(file.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as e:
        print(f'Skipping unreadable episode: {file}: {e}')
        return 0, 0
    changed = 0
    attempted = 0
    for news in episode.get('news', []):
        link = news.get('link')
        if not isinstance(link, dict) or (link.get('image') and not overwrite):
            continue
        source = link.get('url')
        if not source:
            continue
        attempted += 1
        img = image_for_article(source)
        if img and link.get('image') != img:
            link['image'] = img
            # No image copy or distribution: browser requests it from the original site.
            changed += 1
    if changed:
        file.write_text(json.dumps(episode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return changed, attempted


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--today',action='store_true')
    p.add_argument('--all',action='store_true')
    p.add_argument('--overwrite',action='store_true')
    args = p.parse_args()
    if not (args.today or args.all):
        p.error('specify --today or --all')
    files = sorted((ROOT/'episodes').glob('*-ja.json')) if args.all else [ROOT/'episodes'/f'{datetime.now(ZoneInfo("Asia/Tokyo")).date()}-ja.json']
    total = 0
    for path in files:
        if path.exists():
            count, attempted = enrich_episode(path,args.overwrite)
            total += count
            print(f'{path.name}: {count} official OGP preview(s) added / {attempted} checked')
    print(f'Complete: {total} image URL(s). Images are linked, not downloaded.')

if __name__ == '__main__':
    main()
