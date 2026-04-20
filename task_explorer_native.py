import json
import re
import shutil
import sqlite3
import sys
import ctypes
import traceback
import unicodedata
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import customtkinter as ctk

APP_TITLE = "\uc791\uc5c5 \ud050 \ud0d0\uc0c9\uae30"
ROOT_ID = "root"
STATE_FILE = "task-explorer-state.json"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COL = {
    "bg": "#eef7fb",
    "panel": "#ffffff",
    "soft": "#f7fbfd",
    "line": "#d8e8ef",
    "text": "#172033",
    "muted": "#687789",
    "primary": "#227c9d",
    "primary_hover": "#176579",
    "accent": "#e9a23b",
    "accent_soft": "#fff7e8",
    "danger": "#df5f57",
    "danger_soft": "#fff0ee",
    "sidebar": "#f4fbfe",
    "sidebar_soft": "#ffffff",
    "sidebar_line": "#d6e9f1",
    "sidebar_text": "#172033",
    "sidebar_muted": "#6d7f8e",
    "memo": "#fff8ea",
    "folder": "#eef8ff",
    "today": "#e8f7fb",
    "important": "#fff6df",
    "done": "#eef9f1",
    "matrix_a": "#fff0f1",
    "matrix_b": "#fff7e5",
    "matrix_c": "#edf8fc",
    "matrix_d": "#f7fafc",
    "hero": "#ffffff",
    "hero_soft": "#e8f6fb",
    "hero_line": "#d8e8ef",
    "detail_bg": "#f6fcff",
    "detail_panel": "#ffffff",
    "detail_button": "#e8f6fb",
}

THEME_PRESETS = {
    "sky": {
        "label": "\ub9d1\uc740 \ud558\ub298",
        "bg": "#f5fbff", "panel": "#ffffff", "soft": "#fbfdff", "line": "#cfe9fb", "text": "#10243a", "muted": "#5f7487",
        "primary": "#2f9fe8", "primary_hover": "#187fc2", "accent": "#f6b84a", "accent_soft": "#fff8e6",
        "danger": "#e0645d", "danger_soft": "#fff1ef", "sidebar": "#ecf8ff", "sidebar_soft": "#ffffff", "sidebar_line": "#c7e7fb",
        "sidebar_text": "#10243a", "sidebar_muted": "#6c8294", "memo": "#fff9df", "folder": "#eaf7ff", "today": "#e3f5ff",
        "important": "#fff3c8", "done": "#eaf8ef", "matrix_a": "#fff0f3", "matrix_b": "#fff6d9", "matrix_c": "#e6f6ff", "matrix_d": "#f9fcff",
        "hero": "#ffffff", "hero_soft": "#e5f6ff", "hero_line": "#cfe9fb", "detail_bg": "#f4fbff", "detail_panel": "#ffffff", "detail_button": "#e5f6ff",
    },
    "cream": {
        "label": "\ud3ec\uadfc\ud55c \ud06c\ub9bc",
        "bg": "#f8f4ec", "panel": "#fffdf8", "soft": "#fffaf0", "line": "#eadfcb", "text": "#231f1a", "muted": "#7b6e60",
        "primary": "#b06f3a", "primary_hover": "#8f5428", "accent": "#d89b32", "accent_soft": "#fff3d8",
        "danger": "#c95f51", "danger_soft": "#fff0ea", "sidebar": "#fbf3e5", "sidebar_soft": "#fffdf8", "sidebar_line": "#eadfcb",
        "sidebar_text": "#231f1a", "sidebar_muted": "#7b6e60", "memo": "#fff8db", "folder": "#f4ead7", "today": "#fff1df",
        "important": "#ffefc4", "done": "#edf6e9", "matrix_a": "#ffe9e2", "matrix_b": "#fff0c8", "matrix_c": "#f1e8d9", "matrix_d": "#fbf7ef",
        "hero": "#fffdf8", "hero_soft": "#fff3df", "hero_line": "#eadfcb", "detail_bg": "#fff8ec", "detail_panel": "#fffdf8", "detail_button": "#fff0d6",
    },
    "mint": {
        "label": "\uc2e0\uc120\ud55c \ubbfc\ud2b8",
        "bg": "#edf8f3", "panel": "#ffffff", "soft": "#f6fcf9", "line": "#cfe6dd", "text": "#13231e", "muted": "#61766f",
        "primary": "#2f8f7a", "primary_hover": "#226f60", "accent": "#7ca642", "accent_soft": "#f1f8df",
        "danger": "#d36a5f", "danger_soft": "#fff0ee", "sidebar": "#f1fbf7", "sidebar_soft": "#ffffff", "sidebar_line": "#cfe6dd",
        "sidebar_text": "#13231e", "sidebar_muted": "#61766f", "memo": "#fff8e5", "folder": "#e8f7ef", "today": "#e3f6f2",
        "important": "#eff7d5", "done": "#e9f8ee", "matrix_a": "#ffeff0", "matrix_b": "#f3f8d9", "matrix_c": "#e5f6f3", "matrix_d": "#f7fbf9",
        "hero": "#ffffff", "hero_soft": "#e5f7f1", "hero_line": "#cfe6dd", "detail_bg": "#f4fcf9", "detail_panel": "#ffffff", "detail_button": "#e5f7f1",
    },
}

DEFAULT_COL = dict(COL)
THEME_LABEL_TO_KEY = {v["label"]: k for k, v in THEME_PRESETS.items()}

def apply_color_theme(theme_key):
    selected = THEME_PRESETS.get(theme_key) or THEME_PRESETS["sky"]
    COL.clear()
    COL.update(DEFAULT_COL)
    COL.update(selected)
    return selected["label"]

FONT = "Segoe UI Rounded"
READ_FONT = "Malgun Gothic"
TITLE_FONT = (FONT, 25, "bold")
SECTION_FONT = (FONT, 13, "bold")
BODY_FONT = (FONT, 12)
SMALL_FONT = (FONT, 11)
READ_BODY_FONT = (READ_FONT, 12)
READ_TITLE_FONT = (READ_FONT, 15, "bold")
CONTROL_FONT = (READ_FONT, 11)
MAX_CONTENT_WIDTH = 1120
MIN_CONTENT_WIDTH = 420
SCROLL_UNITS = 6
DATE_SECTION_HEIGHT = 190
SIDE_SECTION_HEIGHT = 155
CARD_RENDER_BATCH = 28
SIDE_VISIBLE_LIMIT = 12
VROW_HEIGHT = 86
VROW_HOVER_HEIGHT = 86
VROW_BUFFER = 6

TREE_MARK_RE = re.compile(r"^(?P<prefix>[\s\u2502|]*)(?P<mark>\u251c\u2500\u2500|\u2514\u2500\u2500|\u251c\u2500|\u2514\u2500|\u2523\u2501\u2501|\u2517\u2501\u2501|\u2523\u2501|\u2517\u2501|\|--|\+--|`--|\\--)[ \t]*(?P<title>.*)$")
PLAIN_MARK_RE = re.compile(r"^(?P<indent> *)(?:(?P<check>[-*+]\s+\[[ xX]\])|(?P<bullet>[-*+])|(?P<number>\d+[.)]))\s+(?P<title>.*)$")
META_RE = re.compile(r"\s+\{(?P<meta>[^{}]*)\}\s*$")
ALIAS_RE = re.compile(r"^\[(?P<alias>\uBA54\uBAA8|memo|\uD560\uC77C|\uD560 \uC77C|task)\]\s*", re.IGNORECASE)
MATRIX_INFO = {
    0: ("\uAE09\uD558\uACE0 \uC911\uC694\uD55C \uC77C", "#f5a9af", "#fff1f2"),
    1: ("\uC911\uC694\uD558\uC9C0\uB9CC \uAE09\uD558\uC9C0 \uC54A\uC740 \uC77C", "#f2c05f", "#fff8e6"),
    2: ("\uAE09\uD558\uC9C0\uB9CC \uC911\uC694\uD558\uC9C0 \uC54A\uC740 \uC77C", "#7bbfe5", "#eef9ff"),
    3: ("\uAE09\uD558\uC9C0\uB3C4 \uC911\uC694\uD558\uC9C0\uB3C4 \uC54A\uC740 \uC77C", "#9aa8b5", "#f4f7fa"),
}
ACTIVITY_GROUPS = {
    "queue": ("\uc791\uc5c5 \ud050", "#227c9d", ["taskexplorer", "myqueue"]),
    "browser": ("\ube0c\ub77c\uc6b0\uc800 / \uc6f9", "#4f8bd6", ["chrome", "msedge", "firefox", "whale", "browser"]),
    "dev": ("\uac1c\ubc1c / \ucf54\ub529", "#7667d9", ["code", "devenv", "pycharm", "idea", "cursor", "codex", "terminal", "powershell", "cmd", "python"]),
    "docs": ("\ubb38\uc11c / \uba54\ubaa8", "#e0a23b", ["notepad", "winword", "excel", "powerpnt", "onenote", "notion"]),
    "comm": ("\uc18c\ud1b5", "#41a88a", ["discord", "slack", "teams", "kakaotalk", "telegram", "zoom"]),
    "media": ("\ubbf8\ub514\uc5b4", "#d76f8a", ["spotify", "vlc", "potplayer", "youtube", "photos", "media"]),
    "system": ("\uc2dc\uc2a4\ud15c", "#8aa4b8", ["explorer", "taskmgr", "settings", "control"]),
    "other": ("\uae30\ud0c0", "#9aa8b5", []),
}

def activity_group_for(process_name, window_title="", overrides=None):
    process_raw = (process_name or "").strip()
    process_key = process_raw.lower()
    title_key = (window_title or "").strip().lower()
    haystack = f"{process_key} {title_key}"
    if overrides:
        custom_label = overrides.get(process_key) or overrides.get(process_raw)
        if custom_label:
            for key, (label, color, _keywords) in ACTIVITY_GROUPS.items():
                if custom_label == label:
                    return key, label, color
            palette = ["#227c9d", "#4f8bd6", "#7667d9", "#e0a23b", "#41a88a", "#d76f8a", "#8aa4b8"]
            return "custom-" + re.sub(r"[^a-z0-9]+", "-", custom_label.lower()).strip("-"), custom_label, palette[sum(ord(c) for c in custom_label) % len(palette)]
    for key, (label, color, keywords) in ACTIVITY_GROUPS.items():
        if key == "other":
            continue
        if any(keyword in haystack for keyword in keywords):
            return key, label, color
    return "other", ACTIVITY_GROUPS["other"][0], ACTIVITY_GROUPS["other"][1]


def app_dir():
    if getattr(sys, "frozen", False) and sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / "TaskExplorer"
        path.mkdir(parents=True, exist_ok=True)
        return path
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def write_startup_error(message):
    try:
        log_path = app_dir() / "TaskExplorer-startup-error.log"
        log_path.write_text(message, encoding="utf-8")
        return log_path
    except Exception:
        try:
            fallback = Path.home() / "TaskExplorer-startup-error.log"
            fallback.write_text(message, encoding="utf-8")
            return fallback
        except Exception:
            return None


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def activity_now_iso():
    return datetime.now().isoformat(timespec="microseconds")


def new_id(prefix="task"):
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def parse_priority(value):
    value = str(value or "").strip()
    if not value or value in ("우선순위", "없음", "-"):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def human_time(value):
    if not value:
        return ""
    try:
        return datetime.fromisoformat(str(value)).strftime("%m.%d %H:%M")
    except ValueError:
        return str(value)[:16].replace("T", " ")


def date_key(value):
    return str(value)[:10] if value else "날짜 없음"


def normalize_import_line(line):
    text = unicodedata.normalize("NFC", str(line))
    return text.replace("\ufeff", "").replace("\u200b", "").replace("\xa0", " ").replace("\u3000", "  ")


def tree_prefix_depth(prefix):
    text = prefix.replace("|", "\u2502").replace("\t", "    ")
    depth = 1
    i = 0
    while i < len(text):
        part = text[i:i + 4]
        if part in ("\u2502   ", "    "):
            depth += 1
            i += 4
            continue
        if text[i].isspace():
            i += 1
            continue
        break
    return depth


def parse_meta_tokens(meta, row):
    for raw in re.split(r"[\s,]+", meta.strip()):
        token = raw.strip()
        if not token:
            continue
        key, _, value = token.partition("=")
        key = key.strip().lower()
        value = value.strip()
        if key in ("kind", "type"):
            if value.lower() in ("memo", "\uBA54\uBAA8"):
                row["kind"] = "memo"
            elif value.lower() in ("task", "todo", "\uD560\uC77C", "\uD560 \uC77C"):
                row["kind"] = "task"
            else:
                row["errors"].append(f"Unknown kind: {value}")
        elif key in ("priority", "p", "\uC6B0\uC120", "\uC6B0\uC120\uC21C\uC704"):
            parsed = parse_priority(value)
            if parsed is None and value:
                row["warnings"].append(f"Ignored priority: {value}")
            row["priority"] = parsed
        elif key in ("today", "\uC624\uB298"):
            row["isToday"] = True
        elif key in ("important", "\uC911\uC694", "star"):
            row["isImportant"] = True
        elif key in ("done", "completed", "\uC644\uB8CC"):
            row["completed"] = True
        else:
            row["warnings"].append(f"Unknown metadata: {token}")


def parse_title_metadata(title, row):
    title = str(title or "").strip()
    meta_match = META_RE.search(title)
    if meta_match:
        parse_meta_tokens(meta_match.group("meta"), row)
        title = title[:meta_match.start()].rstrip()
    alias = ALIAS_RE.match(title)
    if alias:
        value = alias.group("alias").lower().replace(" ", "")
        row["kind"] = "memo" if value in ("\uBA54\uBAA8", "memo") else "task"
        title = title[alias.end():].lstrip()
    if "#today" in title or "#\uC624\uB298" in title:
        row["isToday"] = True
        title = re.sub(r"\s*(#today|#\uC624\uB298)\b", "", title).strip()
    if "#important" in title or "#\uC911\uC694" in title:
        row["isImportant"] = True
        title = re.sub(r"\s*(#important|#\uC911\uC694)\b", "", title).strip()
    mark = re.search(r"(?:^|\s)!([0-9]+)(?:\s|$)", title)
    if mark:
        row["priority"] = parse_priority(mark.group(1))
        title = re.sub(r"\s*![0-9]+(?:\s|$)", " ", title).strip()
    row["title"] = title.strip()
    if not row["title"]:
        row["errors"].append("Empty title")


def clean_title(text):
    text = re.sub(r"^[\s\u2502|]*(?:\u251c\u2500\u2500|\u2514\u2500\u2500|\u251c\u2500|\u2514\u2500|\u2523\u2501\u2501|\u2517\u2501\u2501|\u2523\u2501|\u2517\u2501|\|--|\+--|`--|\\--|[-*+]\s*)", "", str(text)).strip()
    return text or "\uC774\uB984 \uC5C6\uC74C"


def parse_tree_text_detailed(raw):
    raw_lines = str(raw or "").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    plain_indents = []
    normalized = []
    in_fence = False
    for line_no, raw_line in enumerate(raw_lines, 1):
        line = normalize_import_line(raw_line).replace("\t", "    ").rstrip()
        if not line.strip():
            continue
        if line.strip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        normalized.append((line_no, line))
        if not TREE_MARK_RE.match(line):
            leading = len(line) - len(line.lstrip(" "))
            if leading > 0:
                plain_indents.append(leading)
    indent_unit = max(1, min(plain_indents) if plain_indents else 2)
    rows = []
    last_row = None
    previous_depth = None
    for line_no, text in normalized:
        memo_match = re.match(r"^[\s\u2502|]*>\s?(?P<memo>.*)$", text)
        if memo_match:
            memo = memo_match.group("memo")
            if last_row:
                last_row["memo"] = (last_row.get("memo", "") + "\n" + memo).strip()
            else:
                rows.append({"line": line_no, "raw": text, "title": "", "depth": 0, "kind": "memo", "memo": "", "priority": None, "isToday": False, "isImportant": False, "completed": False, "warnings": [], "errors": ["Memo line without target"]})
            continue
        row = {"line": line_no, "raw": text, "title": "", "depth": 0, "kind": "task", "memo": "", "priority": None, "isToday": False, "isImportant": False, "completed": False, "warnings": [], "errors": []}
        match = TREE_MARK_RE.match(text)
        if match:
            row["depth"] = tree_prefix_depth(match.group("prefix") or "")
            title = match.group("title")
        else:
            leading = len(text) - len(text.lstrip(" "))
            if leading and leading % indent_unit:
                row["warnings"].append(f"Mixed indent: {leading}/{indent_unit}")
            row["depth"] = leading // indent_unit
            plain = PLAIN_MARK_RE.match(text)
            if plain:
                title = plain.group("title")
                check = plain.group("check")
                if check:
                    row["completed"] = "x" in check.lower()
            else:
                title = text.strip()
        parse_title_metadata(clean_title(title), row)
        if row["kind"] == "memo":
            row["priority"] = None
            row["isToday"] = False
            row["isImportant"] = False
            row["completed"] = False
        if previous_depth is not None and row["depth"] > previous_depth + 1:
            row["warnings"].append(f"Depth jump fixed to {previous_depth + 1}")
            row["depth"] = previous_depth + 1
        rows.append(row)
        last_row = row
        previous_depth = row["depth"]
    return {"rows": rows, "warnings": [w for r in rows for w in r["warnings"]], "errors": [e for r in rows for e in r["errors"]]}


def parse_tree_text(raw):
    return [{"title": row["title"] or "\uC774\uB984 \uC5C6\uC74C", "depth": row["depth"]} for row in parse_tree_text_detailed(raw)["rows"] if not row["errors"]]


def matrix_bucket(node):
    if node.get("isToday") and node.get("isImportant"):
        return 0
    if node.get("isImportant"):
        return 1
    if node.get("isToday"):
        return 2
    return 3


class TaskStore:
    def __init__(self):
        self.path = app_dir() / STATE_FILE
        self.state = self.empty()
        self.load()

    def empty(self):
        return {"version": 3, "nextOrder": 1, "nodes": {ROOT_ID: {"id": ROOT_ID, "title": "루트", "parentId": None, "completed": False, "isToday": False, "isImportant": False, "kind": "task", "memo": "", "priority": None, "completedAt": None, "createdAt": now_iso(), "createdOrder": 0, "children": [], "isCustomFolder": False}}, "pathLists": [], "customTabs": []}

    @property
    def nodes(self):
        return self.state.setdefault("nodes", {})

    @property
    def path_lists(self):
        return self.state.setdefault("pathLists", [])

    @property
    def custom_tabs(self):
        return self.state.setdefault("customTabs", [])

    def load(self):
        self.load_error = None
        if self.path.exists():
            try:
                self.state = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.load_error = f"상태 파일을 읽지 못했습니다: {self.path}"
                try:
                    shutil.copy2(self.path, self.path.with_suffix(".broken.json"))
                except Exception:
                    pass
                self.state = self.empty()
        self.ensure()

    def save(self):
        self.ensure(sort=False)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def save_as(self, path):
        self.ensure()
        Path(path).write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_from(self, path):
        self.state = json.loads(Path(path).read_text(encoding="utf-8"))
        self.ensure()
        self.save()

    def ensure(self, sort=True):
        if ROOT_ID not in self.nodes:
            self.state = self.empty(); return
        self.state.setdefault("pathLists", [])
        self.state.setdefault("customTabs", [])
        if not isinstance(self.state.get("nextOrder"), (int, float)):
            self.state["nextOrder"] = 1
        for nid, n in list(self.nodes.items()):
            if not isinstance(n, dict):
                self.nodes.pop(nid, None); continue
            n["id"] = str(n.get("id") or nid)
            n.setdefault("title", "이름 없음")
            n.setdefault("parentId", ROOT_ID if nid != ROOT_ID else None)
            n.setdefault("completed", False); n.setdefault("isToday", False); n.setdefault("isImportant", False)
            n.setdefault("kind", "task"); n.setdefault("memo", ""); n.setdefault("priority", None)
            n.setdefault("completedAt", None); n.setdefault("createdAt", now_iso()); n.setdefault("createdOrder", self.state.get("nextOrder", 1))
            n.setdefault("children", []); n.setdefault("isCustomFolder", False)
            if n.get("kind") not in ("task", "memo") or nid == ROOT_ID: n["kind"] = "task"
            if not isinstance(n["children"], list): n["children"] = []
            if n["kind"] == "memo":
                n["completed"] = False; n["completedAt"] = None; n["isToday"] = False; n["isImportant"] = False; n["priority"] = None
        self.nodes[ROOT_ID]["parentId"] = None
        valid = set(self.nodes)
        for n in self.nodes.values(): n["children"] = [c for c in n.get("children", []) if c in valid and c != n["id"]]
        ref = set()
        for n in self.nodes.values():
            for c in n.get("children", []):
                self.nodes[c]["parentId"] = n["id"]; ref.add(c)
        root_children = self.nodes[ROOT_ID].setdefault("children", [])
        for nid, n in list(self.nodes.items()):
            if nid != ROOT_ID and nid not in ref and n.get("parentId") not in self.nodes:
                n["parentId"] = ROOT_ID; root_children.append(nid)
        self.state["pathLists"] = [x for x in self.path_lists if isinstance(x, dict)]
        for item in self.path_lists:
            item.setdefault("id", new_id("list")); item.setdefault("title", "목록"); item.setdefault("taskIds", [])
            item.setdefault("createdAt", now_iso()); item.setdefault("createdOrder", self.state.get("nextOrder", 1))
            item["taskIds"] = [x for x in item.get("taskIds", []) if x in valid and x != ROOT_ID]
        self.state["customTabs"] = [x for x in self.custom_tabs if isinstance(x, dict) and x.get("id") in valid]
        if sort: self.sort_all()

    def node(self, node_id): return self.nodes.get(node_id)
    def children(self, parent_id):
        p = self.node(parent_id); return [x for x in (p or {}).get("children", []) if x in self.nodes]
    def all_nodes(self): return [n for n in self.nodes.values() if n.get("id") != ROOT_ID]
    def sort_key(self, nid):
        n = self.node(nid) or {}; p = n.get("priority") if isinstance(n.get("priority"), (int, float)) else 999999999
        return (1 if n.get("completed") else 0, p, n.get("createdOrder", 0))
    def sort_children(self, pid):
        p = self.node(pid)
        if p: p["children"] = sorted(self.children(pid), key=self.sort_key)
    def sort_all(self):
        for nid in list(self.nodes): self.sort_children(nid)
    def add_node(self, parent_id, title, kind="task", priority=None, is_today=False):
        parent = self.node(parent_id) or self.node(ROOT_ID); kind = "memo" if kind == "memo" else "task"
        order = int(self.state.get("nextOrder", 1)); self.state["nextOrder"] = order + 1; nid = new_id("task")
        n = {"id": nid, "title": title.strip() or "이름 없음", "parentId": parent["id"], "completed": False, "isToday": bool(is_today) if kind == "task" else False, "isImportant": False, "kind": kind, "memo": "", "priority": priority if kind == "task" else None, "completedAt": None, "createdAt": now_iso(), "createdOrder": order, "children": [], "isCustomFolder": False}
        self.nodes[nid] = n; parent.setdefault("children", []).append(nid); self.sort_children(parent["id"]); return nid

    def add_folder(self, parent_id, title):
        nid = self.add_node(parent_id, title, "task"); n = self.node(nid); n["isCustomFolder"] = True
        self.custom_tabs.append({"id": nid, "title": n["title"], "createdOrder": n["createdOrder"], "createdAt": n["createdAt"]}); return nid

    def folders(self):
        by_id = {n["id"]: n for n in self.all_nodes() if n.get("isCustomFolder")}; out = []; seen = set()
        for item in self.custom_tabs:
            n = by_id.get(item.get("id"))
            if n: out.append(n); seen.add(n["id"])
        out.extend(sorted((n for nid, n in by_id.items() if nid not in seen), key=lambda x: x.get("createdOrder", 0))); return out

    def add_path_list(self, title):
        order = int(self.state.get("nextOrder", 1)); self.state["nextOrder"] = order + 1
        item = {"id": new_id("list"), "title": title.strip() or "목록", "taskIds": [], "createdOrder": order, "createdAt": now_iso()}
        self.path_lists.append(item); return item["id"]

    def path_list(self, list_id):
        return next((x for x in self.path_lists if x.get("id") == list_id), None)

    def delete_subtree(self, nid):
        if nid == ROOT_ID or nid not in self.nodes: return
        gone = []
        def walk(x):
            gone.append(x)
            for c in self.children(x): walk(c)
        walk(nid); parent = self.node(self.node(nid).get("parentId"))
        if parent: parent["children"] = [x for x in parent.get("children", []) if x != nid]
        for x in gone: self.nodes.pop(x, None)
        gs = set(gone)
        for item in self.path_lists: item["taskIds"] = [x for x in item.get("taskIds", []) if x not in gs]
        self.state["customTabs"] = [x for x in self.custom_tabs if x.get("id") not in gs]

    def is_descendant(self, nid, target):
        cur = target
        while cur:
            if cur == nid: return True
            n = self.node(cur); cur = n.get("parentId") if n else None
        return False

    def move_node(self, nid, parent_id):
        if nid == ROOT_ID or nid == parent_id or self.is_descendant(nid, parent_id): return False
        n = self.node(nid); p = self.node(parent_id)
        if not n or not p: return False
        old = self.node(n.get("parentId"))
        if old: old["children"] = [x for x in old.get("children", []) if x != nid]
        n["parentId"] = parent_id; p.setdefault("children", []).append(nid); self.sort_children(parent_id); return True

    def reorder_node(self, nid, target_id, after=False):
        n = self.node(nid); target = self.node(target_id)
        if not n or not target or nid == target_id: return False
        if n.get("parentId") != target.get("parentId"): return False
        parent = self.node(n.get("parentId"))
        if not parent: return False
        children = [x for x in parent.get("children", []) if x != nid]
        if target_id not in children: return False
        idx = children.index(target_id) + (1 if after else 0)
        children.insert(idx, nid)
        parent["children"] = children
        base = int(self.state.get("nextOrder", 1))
        for offset, child_id in enumerate(children):
            child = self.node(child_id)
            if child:
                child["createdOrder"] = base + offset
        self.state["nextOrder"] = base + len(children)
        return True

    def clone_subtree(self, nid, parent_id):
        src = self.node(nid); parent = self.node(parent_id)
        if not src or not parent or nid == ROOT_ID: return None
        order = int(self.state.get("nextOrder", 1)); self.state["nextOrder"] = order + 1; cid = new_id("task")
        clone = dict(src); clone.update({"id": cid, "parentId": parent["id"], "createdAt": now_iso(), "createdOrder": order, "children": [], "isCustomFolder": False})
        if clone.get("completed"): clone["completedAt"] = now_iso()
        self.nodes[cid] = clone; parent.setdefault("children", []).append(cid)
        for child in self.children(nid): self.clone_subtree(child, cid)
        self.sort_children(parent["id"]); return cid

    def set_kind(self, nid, kind, subtree=False):
        ids = []
        def walk(x):
            if x == ROOT_ID: return
            ids.append(x)
            if subtree:
                for c in self.children(x): walk(c)
        walk(nid)
        for x in ids:
            n = self.node(x)
            if not n or n.get("isCustomFolder"): continue
            n["kind"] = "memo" if kind == "memo" else "task"
            if n["kind"] == "memo":
                n["completed"] = False; n["completedAt"] = None; n["isToday"] = False; n["isImportant"] = False; n["priority"] = None


class ActivityLog:
    def __init__(self):
        self.path = app_dir() / "activity-log.db"
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                duration_seconds INTEGER DEFAULT 0,
                process_name TEXT NOT NULL,
                window_title TEXT DEFAULT ''
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_process ON sessions(process_name)")
        self.conn.commit()
        self.current_id = None
        self.current_process = None
        self.current_title = None
        self.current_started = None

    def close(self):
        self.close_current()
        self.conn.close()

    def close_current(self):
        if not self.current_id:
            return
        ended = activity_now_iso()
        duration = self.seconds_between(self.current_started, ended)
        self.conn.execute("UPDATE sessions SET ended_at=?, duration_seconds=? WHERE id=?", (ended, duration, self.current_id))
        self.conn.commit()
        self.current_id = None
        self.current_process = None
        self.current_title = None
        self.current_started = None

    def touch_current(self):
        if not self.current_id:
            return
        ended = activity_now_iso()
        duration = self.seconds_between(self.current_started, ended)
        self.conn.execute("UPDATE sessions SET ended_at=?, duration_seconds=? WHERE id=?", (ended, duration, self.current_id))
        self.conn.commit()

    def switch_to(self, process_name, window_title):
        process_name = process_name or "알 수 없음"
        window_title = window_title or ""
        if self.current_id and process_name == self.current_process and window_title == self.current_title:
            self.touch_current()
            return
        self.close_current()
        started = activity_now_iso()
        cur = self.conn.execute(
            "INSERT INTO sessions(started_at, ended_at, duration_seconds, process_name, window_title) VALUES(?,?,?,?,?)",
            (started, started, 0, process_name, window_title),
        )
        self.conn.commit()
        self.current_id = cur.lastrowid
        self.current_process = process_name
        self.current_title = window_title
        self.current_started = started

    def program_summary(self, day_key):
        rows = self.conn.execute(
            """
            SELECT process_name, SUM(duration_seconds) AS total, COUNT(*) AS count
            FROM sessions
            WHERE substr(started_at, 1, 10)=?
            GROUP BY process_name
            ORDER BY total DESC, process_name ASC
            LIMIT 16
            """,
            (day_key,),
        ).fetchall()
        return [(name, int(total or 0), int(count or 0)) for name, total, count in rows]

    def program_title_samples(self, day_key, limit_per_program=3):
        rows = self.conn.execute(
            """
            SELECT process_name, window_title, SUM(duration_seconds) AS total, MAX(started_at) AS last_seen
            FROM sessions
            WHERE substr(started_at, 1, 10)=?
            GROUP BY process_name, window_title
            ORDER BY process_name ASC, last_seen DESC
            """,
            (day_key,),
        ).fetchall()
        grouped = defaultdict(list)
        for name, title, total, _last_seen in rows:
            if len(grouped[name]) < limit_per_program:
                grouped[name].append((title or "\ucc3d \uc81c\ubaa9 \uc5c6\uc74c", int(total or 0)))
        return grouped

    def program_title_details(self, day_key):
        rows = self.conn.execute(
            """
            SELECT process_name, window_title, SUM(duration_seconds) AS total, COUNT(*) AS count, MAX(started_at) AS last_seen
            FROM sessions
            WHERE substr(started_at, 1, 10)=?
            GROUP BY process_name, window_title
            ORDER BY process_name ASC, total DESC, last_seen DESC
            """,
            (day_key,),
        ).fetchall()
        grouped = defaultdict(list)
        for name, title, total, count, last_seen in rows:
            grouped[name].append((title or "\ucc3d \uc81c\ubaa9 \uc5c6\uc74c", int(total or 0), int(count or 0), last_seen or ""))
        return grouped

    def hourly_summary(self, day_key):
        rows = self.conn.execute(
            """
            SELECT substr(started_at, 12, 2) AS hour, process_name, SUM(duration_seconds) AS total
            FROM sessions
            WHERE substr(started_at, 1, 10)=?
            GROUP BY hour, process_name
            ORDER BY hour ASC, total DESC
            """,
            (day_key,),
        ).fetchall()
        grouped = defaultdict(list)
        for hour, name, total in rows:
            grouped[hour or "알수없음"].append((name, int(total or 0)))
        return grouped

    def hourly_sessions(self, day_key):
        rows = self.conn.execute(
            """
            SELECT substr(started_at, 12, 2) AS hour,
                   substr(started_at, 12, 5) AS started,
                   substr(COALESCE(ended_at, started_at), 12, 5) AS ended,
                   process_name,
                   window_title,
                   duration_seconds
            FROM sessions
            WHERE substr(started_at, 1, 10)=?
            ORDER BY started_at ASC
            """,
            (day_key,),
        ).fetchall()
        grouped = defaultdict(list)
        for hour, started, ended, name, title, seconds in rows:
            grouped[hour or "알수없음"].append((started, ended, name, title or "창 제목 없음", int(seconds or 0)))
        return grouped

    def recent_sessions(self, day_key, limit=8):
        rows = self.conn.execute(
            """
            SELECT substr(started_at, 12, 5), substr(COALESCE(ended_at, started_at), 12, 5), process_name, window_title, duration_seconds
            FROM sessions
            WHERE substr(started_at, 1, 10)=?
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (day_key, limit),
        ).fetchall()
        return [(a, b, name, title or "창 제목 없음", int(seconds or 0)) for a, b, name, title, seconds in rows]


    def sessions_for_day(self, day_key):
        rows = self.conn.execute(
            """
            SELECT started_at, COALESCE(ended_at, started_at), duration_seconds, process_name, window_title
            FROM sessions
            WHERE substr(started_at, 1, 10)=?
            ORDER BY started_at ASC, id ASC
            """,
            (day_key,),
        ).fetchall()
        return [(a, b, int(seconds or 0), name, title or "창 제목 없음") for a, b, seconds, name, title in rows]

    def group_summary(self, day_key, overrides=None):
        grouped = defaultdict(lambda: {"seconds": 0, "count": 0, "programs": defaultdict(int), "titles": []})
        for started, ended, seconds, name, title in self.sessions_for_day(day_key):
            key, label, color = activity_group_for(name, title, overrides)
            item = grouped[key]
            item["label"] = label
            item["color"] = color
            item["seconds"] += seconds
            item["count"] += 1
            item["programs"][name] += seconds
            if title and title != "창 제목 없음" and title not in item["titles"]:
                item["titles"].append(title)
        rows = []
        for key, item in grouped.items():
            programs = sorted(item["programs"].items(), key=lambda x: (-x[1], x[0]))[:4]
            rows.append((key, item["label"], item["color"], item["seconds"], item["count"], programs, item["titles"][:3]))
        return sorted(rows, key=lambda x: (-x[3], x[1]))

    def clear_day(self, day_key):
        self.close_current()
        self.conn.execute("DELETE FROM sessions WHERE substr(started_at, 1, 10)=?", (day_key,))
        self.conn.commit()

    def clear_all(self):
        self.close_current()
        self.conn.execute("DELETE FROM sessions")
        self.conn.commit()

    def total_seconds(self, day_key):
        row = self.conn.execute("SELECT SUM(duration_seconds) FROM sessions WHERE substr(started_at, 1, 10)=?", (day_key,)).fetchone()
        return int((row or [0])[0] or 0)

    @staticmethod
    def seconds_between(started, ended):
        try:
            return max(0, int((datetime.fromisoformat(ended) - datetime.fromisoformat(started)).total_seconds()))
        except Exception:
            return 0


def active_window_info(include_title=False):
    if sys.platform != "win32":
        return "지원 안 됨", "Windows에서만 활성 창 기록을 지원합니다."
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "알 수 없음", ""
        title = ""
        if include_title:
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_name = f"pid-{pid.value}"
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if handle:
            try:
                size = ctypes.c_ulong(32768)
                buf = ctypes.create_unicode_buffer(size.value)
                if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                    process_name = Path(buf.value).name
            finally:
                kernel32.CloseHandle(handle)
        return process_name, title
    except Exception:
        return "알 수 없음", ""


def format_duration(seconds):
    seconds = int(seconds or 0)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}시간 {minutes:02d}분"
    if minutes:
        return f"{minutes}분 {secs:02d}초"
    return f"{secs}초"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.store = TaskStore()
        self.ui_state = self.store.state.setdefault("ui", {})
        self.color_theme_key = self.ui_state.get("colorTheme", "sky")
        apply_color_theme(self.color_theme_key)
        self.activity_log = ActivityLog()
        self.withdraw()
        self.title(APP_TITLE); self.minsize(900, 640); self.apply_start_geometry(); self.configure(fg_color=COL["bg"])
        if self.ui_state.get("zoomed"):
            self.after(80, self.safe_zoomed)
        self.current_parent = ROOT_ID; self.selected_id = None; self.view_mode = self.ui_state.get("viewMode", "all"); self.kind_filter = "all"
        self.current_list_id = None; self.current_date = None; self.current_date_mode = None; self.date_filter = "created"; self.drag_source = None; self.drag_start_x = 0; self.drag_start_y = 0; self.drag_last_target = None; self.drag_last_after = False; self.drop_targets = {}; self.folder_ids = []; self.paste_open = False; self.left_panel_open = bool(self.ui_state.get("leftPanelOpen", True)); self.right_panel_open = bool(self.ui_state.get("rightPanelOpen", False)); self.tools_open = False; self.side_section_open = dict(self.ui_state.get("sideSectionOpen", {"lists": True, "folders": True, "files": False})); self.right_section_open = dict(self.ui_state.get("rightSectionOpen", {"views": True, "dates": False, "activity": True, "memo": True}))
        self.activity_running = bool(self.ui_state.get("activityRunning", False))
        self.activity_log_titles = bool(self.ui_state.get("activityLogTitles", True))
        self.activity_view = self.ui_state.get("activityView", "timeline")
        self.activity_group_filter = self.ui_state.get("activityGroupFilter", "all")
        self.activity_expanded_programs = set()
        self.activity_poll_after_id = None
        self.active_scroll = None
        self.fit_after_id = None
        self.pending_main_width = None
        self.auto_left_collapsed = False
        self.auto_right_collapsed = False
        self.side_refresh_after_id = None
        self.card_render_limit = CARD_RENDER_BATCH
        self.children_count_cache = {}
        self.date_side_limit = SIDE_VISIBLE_LIMIT
        self.list_side_limit = SIDE_VISIBLE_LIMIT
        self.folder_side_limit = SIDE_VISIBLE_LIMIT
        self.virtual_ids = []
        self.virtual_rows = []
        self.virtual_row_widgets = []
        self.virtual_scroll_y = 0
        self.virtual_hover_id = None
        self.virtual_hover_job = None
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self.build_sidebar(); self.build_main(); self.build_detail(); self.refresh_initial(); self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind_all("<MouseWheel>", self.fast_mousewheel, add="+")
        self.bind_all("<B1-Motion>", self.drag_motion, add="+")
        self.bind_all("<ButtonRelease-1>", self.finish_drag, add="+")
        self.after(20, self.show_start_window)
        self.after(800, self.refresh_side)
        if self.activity_running:
            self.after(1000, self.poll_activity)

    def report_callback_exception(self, exc, value, tb):
        detail = "".join(traceback.format_exception(exc, value, tb))
        write_startup_error(detail)
        try:
            messagebox.showerror("TaskExplorer 오류", f"실행 중 오류가 발생했습니다.\n\n{detail[:1200]}")
        except Exception:
            pass

    def safe_zoomed(self):
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass

    def show_start_window(self):
        try:
            self.deiconify()
            self.update_idletasks()
            self.lift()
            self.focus_force()
            if sys.platform == "darwin":
                self.attributes("-topmost", True)
                self.after(350, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    def make_btn(self, parent, text, command, color=None, variant="soft", height=36):
        if variant == "nav":
            return ctk.CTkButton(parent, text=text, command=command, fg_color=COL["sidebar_soft"], hover_color="#e8f6fb", text_color=COL["sidebar_text"], height=height, corner_radius=12, font=CONTROL_FONT, border_width=1, border_color=COL["sidebar_line"])
        if variant == "danger":
            return ctk.CTkButton(parent, text=text, command=command, fg_color=COL["danger_soft"], hover_color="#ffe1dc", text_color=COL["danger"], height=height, corner_radius=12, font=CONTROL_FONT)
        if color:
            return ctk.CTkButton(parent, text=text, command=command, fg_color=color, hover_color=COL["primary_hover"], text_color="white", height=height, corner_radius=12, font=CONTROL_FONT)
        return ctk.CTkButton(parent, text=text, command=command, fg_color=COL["soft"], hover_color="#eaf6fa", text_color=COL["text"], height=height, corner_radius=12, font=CONTROL_FONT, border_width=1, border_color=COL["line"])

    def pill(self, parent, text, color=None):
        return ctk.CTkLabel(parent, text=text, font=(FONT, 10, "bold"), text_color="white" if color else COL["muted"], fg_color=color or COL["soft"], corner_radius=10, height=20, padx=10)


    def apply_start_geometry(self):
        raw = str(self.ui_state.get("geometry", "1560x940"))
        match = re.match(r"^(\d+)x(\d+)([+-]\d+)?([+-]\d+)?$", raw)
        screen_w = max(900, self.winfo_screenwidth())
        screen_h = max(640, self.winfo_screenheight())
        if match:
            w = int(match.group(1)); h = int(match.group(2))
        else:
            w, h = 1560, 940
        w = max(900, min(w, screen_w - 40))
        h = max(640, min(h, screen_h - 80))
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def apply_top_tab_layout(self, width=None):
        if not hasattr(self, "topbar"):
            return
        width = width or self.content.winfo_width() or MAX_CONTENT_WIDTH
        buttons = [btn for _mode, btn in getattr(self, "top_tab_order", [])] + [getattr(self, "top_tool_button", None)]
        buttons = [b for b in buttons if b is not None]
        if width < 620:
            cols = 3
        elif width < 860:
            cols = 4
        else:
            cols = 7
        for c in range(8):
            self.topbar.grid_columnconfigure(c, weight=1 if c < cols else 0)
        for i, btn in enumerate(buttons):
            btn.grid(row=i // cols, column=i % cols, sticky="ew", padx=(8 if i % cols == 0 else 3, 8 if i % cols == cols - 1 else 3), pady=(8 if i < cols else 2, 8 if i >= len(buttons) - cols else 2))

    def apply_responsive_panels(self):
        width = self.winfo_width()
        if not width:
            return
        if width < 1040 and self.right_panel_open:
            self.detail.grid_remove()
            if not hasattr(self, "right_handle"):
                self.right_handle = ctk.CTkButton(self, text="< \uc0c1\uc138", command=self.toggle_right_panel, width=58, height=120, corner_radius=16, fg_color=COL["detail_bg"], hover_color=COL["hero_soft"], text_color=COL["primary"], font=CONTROL_FONT, border_width=1, border_color=COL["line"])
            self.right_handle.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=10)
            self.auto_right_collapsed = True
        elif width >= 1120 and self.right_panel_open and self.auto_right_collapsed:
            if hasattr(self, "right_handle"):
                self.right_handle.grid_remove()
            self.detail.grid(row=0, column=2, sticky="nsew", padx=(0, 10), pady=10)
            self.auto_right_collapsed = False
        if width < 940 and self.left_panel_open:
            self.side.grid_remove()
            if not hasattr(self, "left_handle"):
                self.left_handle = ctk.CTkButton(self, text="\ubaa9\ub85d >", command=self.toggle_left_panel, width=58, height=120, corner_radius=16, fg_color=COL["sidebar"], hover_color=COL["hero_soft"], text_color=COL["sidebar_text"], font=CONTROL_FONT, border_width=1, border_color=COL["sidebar_line"])
            self.left_handle.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=10)
            self.auto_left_collapsed = True
        elif width >= 1020 and self.left_panel_open and self.auto_left_collapsed:
            if hasattr(self, "left_handle"):
                self.left_handle.grid_remove()
            self.side.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
            self.auto_left_collapsed = False

    def build_sidebar(self):
        self.side = ctk.CTkScrollableFrame(self, fg_color=COL["sidebar"], corner_radius=18, width=292)
        self.side.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        self.side.grid_columnconfigure(0, weight=1)
        self.register_scroll(self.side)
        ctk.CTkLabel(self.side, text=APP_TITLE, font=(FONT, 27, "bold"), text_color=COL["sidebar_text"], anchor="w").grid(row=0, column=0, sticky="ew", padx=20, pady=(22, 2))
        ctk.CTkButton(self.side, text="\uc811\uae30", command=self.toggle_left_panel, width=58, height=28, corner_radius=12, fg_color=COL["sidebar_soft"], hover_color=COL["hero_soft"], text_color=COL["sidebar_text"], font=CONTROL_FONT, border_width=1, border_color=COL["sidebar_line"]).grid(row=0, column=0, sticky="e", padx=18, pady=(22, 2))
        ctk.CTkLabel(self.side, text="\ud070 \uc77c\uc740 \uc791\uac8c \ucabc\uac1c\uace0, \uc624\ub298 \ubcfc \uc77c\ub9cc \uc120\uba85\ud558\uac8c \uace0\ub974\ub294 \ud0d0\uc0c9\ud615 \uc791\uc5c5 \ud050", font=SMALL_FONT, text_color=COL["sidebar_muted"], anchor="w", justify="left", wraplength=230).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 16))
        self.search = ctk.CTkEntry(self.side, placeholder_text="\uc791\uc5c5 / \uba54\ubaa8 \uac80\uc0c9", height=40, fg_color=COL["sidebar_soft"], border_color=COL["sidebar_line"], text_color=COL["sidebar_text"], placeholder_text_color=COL["sidebar_muted"], font=SMALL_FONT)
        self.search.grid(row=2, column=0, sticky="ew", padx=20)
        self.search.bind("<Return>", lambda _e: self.refresh_cards())
        self.make_btn(self.side, "\uac80\uc0c9", self.refresh_cards, COL["primary"], height=38).grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 8))
        theme_box = ctk.CTkFrame(self.side, fg_color=COL["sidebar_soft"], corner_radius=12, border_width=1, border_color=COL["sidebar_line"])
        theme_box.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))
        theme_box.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(theme_box, text="\uc0c9\uc0c1", font=CONTROL_FONT, text_color=COL["sidebar_muted"]).grid(row=0, column=0, sticky="w", padx=(10, 6), pady=8)
        self.theme_var = ctk.StringVar(value=THEME_PRESETS.get(self.color_theme_key, THEME_PRESETS["sky"])["label"])
        self.theme_menu = ctk.CTkOptionMenu(theme_box, values=[v["label"] for v in THEME_PRESETS.values()], variable=self.theme_var, command=self.set_color_theme, width=160, height=30, font=CONTROL_FONT, fg_color=COL["soft"], button_color=COL["hero_soft"], button_hover_color=COL["line"], text_color=COL["text"])
        self.theme_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)
        self.list_frame = self.collapsible_side_section("\uc800\uc7a5 \ubaa9\ub85d", "lists", 5)
        self.folder_frame = self.collapsible_side_section("\ud504\ub85c\uc81d\ud2b8 \ud3f4\ub354", "folders", 7)
        self.files_frame = self.collapsible_side_section("\ubc31\uc5c5 / \uac00\uc838\uc624\uae30", "files", 9)
        self.files_frame.grid_columnconfigure(0, weight=1)
        for i, (t, c) in enumerate([("\ubc31\uc5c5 \ubd88\ub7ec\uc624\uae30", self.load_json), ("\ubc31\uc5c5 \uc800\uc7a5", self.save_json), ("\uad6c\uc870 \ub0b4\ubcf4\ub0b4\uae30", self.export_txt), ("\ud558\uc704 \uba54\ubaa8\ud654", self.memoize_current)]):
            self.make_btn(self.files_frame, t, c, variant="nav", height=32).grid(row=i, column=0, sticky="ew", padx=8, pady=3)
        if not self.side_section_open["files"]:
            self.files_frame.grid_remove()

    def side_section(self, title, row):
        return self.collapsible_side_section(title, title, row)

    def collapsible_side_section(self, title, key, row):
        header = ctk.CTkButton(self.side, text=("v  " if self.side_section_open.get(key, True) else ">  ") + title, command=lambda k=key: self.toggle_side_section(k), fg_color="transparent", hover_color=COL["hero_soft"], text_color=COL["sidebar_text"], anchor="w", height=32, corner_radius=12, font=SECTION_FONT)
        header.grid(row=row, column=0, sticky="ew", padx=16, pady=(8, 0))
        setattr(self, f"{key}_header", header)
        frame = ctk.CTkScrollableFrame(self.side, fg_color=COL["sidebar_soft"], height=SIDE_SECTION_HEIGHT, corner_radius=12, border_width=1, border_color=COL["sidebar_line"])
        frame.grid(row=row+1, column=0, sticky="ew", padx=20, pady=(6, 10))
        frame.grid_columnconfigure(0, weight=1)
        self.register_scroll(frame)
        if not self.side_section_open.get(key, True):
            frame.grid_remove()
        return frame

    def toggle_side_section(self, key):
        self.side_section_open[key] = not self.side_section_open.get(key, True)
        self.store.state.setdefault("ui", {})["sideSectionOpen"] = dict(self.side_section_open)
        self.store.save()
        frame = {"lists": getattr(self, "list_frame", None), "folders": getattr(self, "folder_frame", None), "files": getattr(self, "files_frame", None)}.get(key)
        header = getattr(self, f"{key}_header", None)
        titles = {"lists": "\uc800\uc7a5 \ubaa9\ub85d", "folders": "\ud504\ub85c\uc81d\ud2b8 \ud3f4\ub354", "files": "\ubc31\uc5c5 / \uac00\uc838\uc624\uae30"}
        if header:
            header.configure(text=("v  " if self.side_section_open[key] else ">  ") + titles.get(key, key))
        if frame:
            frame.grid() if self.side_section_open[key] else frame.grid_remove()

    def build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=COL["bg"], corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.main.grid_columnconfigure(0, weight=1); self.main.grid_rowconfigure(0, weight=1); self.main.bind("<Configure>", self.fit_main_content)
        self.content = ctk.CTkFrame(self.main, fg_color="transparent", width=MAX_CONTENT_WIDTH)
        self.content.grid(row=0, column=0, sticky="nsew"); self.content.grid_propagate(False); self.content.grid_columnconfigure(0, weight=1); self.content.grid_rowconfigure(6, weight=1)
        topbar = ctk.CTkFrame(self.content, fg_color=COL["panel"], corner_radius=18, border_width=1, border_color=COL["line"])
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.topbar = topbar
        self.top_tabs = {}
        self.top_tab_order = []
        for i, (label, mode) in enumerate([("\uc791\uc5c5", "all"), ("\uc624\ub298", "today"), ("\uc911\uc694", "important"), ("\uc6b0\uc120\uc21c\uc704", "matrix"), ("\uae30\ub85d", "activity"), ("\uc644\ub8cc", "done")]):
            btn = ctk.CTkButton(topbar, text=label, command=lambda x=mode: self.set_view(x), height=36, corner_radius=14, font=CONTROL_FONT, border_width=1)
            self.top_tabs[mode] = btn
            self.top_tab_order.append((mode, btn))
        self.top_tool_button = self.make_btn(topbar, "\ub3c4\uad6c", self.toggle_tools, variant="nav", height=34)
        self.apply_top_tab_layout(MAX_CONTENT_WIDTH)
        hero = ctk.CTkFrame(self.content, fg_color=COL["hero"], corner_radius=20, border_width=1, border_color=COL["hero_line"])
        hero.grid(row=1, column=0, sticky="ew", pady=(0, 14)); hero.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hero, text="Focus Workspace", font=(FONT, 12, "bold"), text_color=COL["accent"], anchor="w").grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 0))
        self.path_frame = ctk.CTkFrame(hero, fg_color="transparent"); self.path_frame.grid(row=1, column=0, sticky="ew", padx=22, pady=(2, 0)); self.path_frame.grid_columnconfigure(99, weight=1)
        self.hint = ctk.CTkLabel(hero, text="", font=BODY_FONT, text_color=COL["muted"], anchor="w"); self.hint.grid(row=2, column=0, sticky="ew", padx=22, pady=(4, 18))
        self.summary = ctk.CTkLabel(hero, text="", font=(FONT, 13, "bold"), text_color="white", fg_color=COL["primary"], corner_radius=18, padx=16, pady=7); self.summary.grid(row=1, column=1, sticky="e", padx=22)
        self.add_panel = ctk.CTkFrame(self.content, fg_color=COL["panel"], corner_radius=16, border_width=1, border_color=COL["line"])
        self.add_panel.grid(row=2, column=0, sticky="ew", pady=(0, 12)); self.add_panel.grid_columnconfigure(0, weight=1)
        add = self.add_panel
        self.title_entry = ctk.CTkEntry(add, placeholder_text="\uc0c8 \uc791\uc5c5\uc744 \uc785\ub825\ud558\uc138\uc694", height=46, font=(READ_FONT, 13), border_color=COL["line"], fg_color=COL["soft"])
        self.title_entry.grid(row=0, column=0, sticky="ew", padx=14, pady=14); self.title_entry.bind("<Return>", lambda _e: self.add_task())
        self.kind_var = ctk.StringVar(value="\ud560 \uc77c")
        ctk.CTkOptionMenu(add, values=["\ud560 \uc77c", "\uba54\ubaa8"], variable=self.kind_var, width=92, height=46, font=CONTROL_FONT, fg_color=COL["primary"], button_color=COL["primary_hover"], button_hover_color=COL["primary_hover"]).grid(row=0, column=1, padx=(0, 8))
        self.priority = ctk.CTkEntry(add, placeholder_text="\uc6b0\uc120\uc21c\uc704", width=100, height=46, font=CONTROL_FONT, border_color=COL["line"], fg_color=COL["soft"]); self.priority.grid(row=0, column=2, padx=(0, 8))
        self.today_var = ctk.BooleanVar(value=False); ctk.CTkCheckBox(add, text="\uc624\ub298", variable=self.today_var, width=70).grid(row=0, column=3, padx=(0, 8))
        self.make_btn(add, "\ucd94\uac00", self.add_task, COL["primary"]).grid(row=0, column=4, padx=(0, 12), sticky="ns")
        self.paste = ctk.CTkFrame(self.content, fg_color=COL["panel"], corner_radius=14, border_width=1, border_color=COL["line"]); self.paste.grid_columnconfigure(0, weight=1)
        self.paste_text = ctk.CTkTextbox(self.paste, height=110, font=READ_BODY_FONT); self.paste_text.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        self.make_btn(self.paste, "\ubd99\uc5ec\ub123\uae30 \ucd94\uac00", self.add_pasted_tree, COL["primary"]).grid(row=0, column=1, padx=(0,12), pady=12, sticky="ns")
        self.toolbar = ctk.CTkFrame(self.content, fg_color=COL["panel"], corner_radius=14, border_width=1, border_color=COL["line"])
        self.toolbar.grid(row=3, column=0, sticky="ew", pady=(0, 12)); self.toolbar.grid_columnconfigure((0,1), weight=1)
        tb = self.toolbar
        self.action_group(tb, "\uad6c\uc870", [("\ud604\uc7ac \uad6c\uc870 \ubcf4\uae30", self.show_tree_view), ("\uad6c\uc870 \ubd99\uc5ec\ub123\uae30", self.toggle_paste), ("\uc791\uc5c5 \uad6c\uc870 \ub0b4\ubcf4\ub0b4\uae30", self.export_txt), ("\ud604\uc7ac \ud558\uc704 \uba54\ubaa8\ud654", self.memoize_current)], 0)
        self.action_group(tb, "\uc774\ub3d9", [("\ucc98\uc74c\uc73c\ub85c", self.go_root), ("\uc0c1\uc704\ub85c", self.move_to_parent)], 1)
        if not self.tools_open: self.toolbar.grid_remove()
        self.activity_controls = ctk.CTkFrame(self.content, fg_color=COL["panel"], corner_radius=16, border_width=1, border_color=COL["line"])
        self.activity_controls.grid(row=4, column=0, sticky="ew", pady=(0, 12)); self.activity_controls.grid_columnconfigure(3, weight=1)
        self.activity_status = ctk.CTkLabel(self.activity_controls, text="", text_color=COL["muted"], anchor="w", font=SMALL_FONT); self.activity_status.grid(row=0, column=0, sticky="w", padx=(14, 8), pady=(9, 4))
        self.activity_toggle = self.make_btn(self.activity_controls, "\uae30\ub85d \uc2dc\uc791", self.toggle_activity_logging, COL["primary"], height=32); self.activity_toggle.grid(row=0, column=1, sticky="w", padx=4, pady=(9, 4))
        self.activity_title_var = ctk.BooleanVar(value=self.activity_log_titles)
        ctk.CTkCheckBox(self.activity_controls, text="\ucc3d \uc81c\ubaa9 \uae30\ub85d", variable=self.activity_title_var, command=self.set_activity_title_logging, font=SMALL_FONT, checkbox_width=16, checkbox_height=16, border_color=COL["line"]).grid(row=0, column=2, sticky="w", padx=8, pady=(9, 4))
        view_row = ctk.CTkFrame(self.activity_controls, fg_color="transparent"); view_row.grid(row=1, column=0, columnspan=5, sticky="ew", padx=10, pady=(2, 10)); view_row.grid_columnconfigure((0,1,2,3), weight=1)
        self.make_btn(view_row, "\ud558\ub8e8 \ud750\ub984", lambda: self.set_activity_view("timeline"), variant="nav", height=32).grid(row=0, column=0, sticky="ew", padx=3)
        self.make_btn(view_row, "\ubd84\ub958\ubcc4", lambda: self.set_activity_view("group"), variant="nav", height=32).grid(row=0, column=1, sticky="ew", padx=3)
        self.make_btn(view_row, "\ud504\ub85c\uadf8\ub7a8\ubcc4", lambda: self.set_activity_view("program"), variant="nav", height=32).grid(row=0, column=2, sticky="ew", padx=3)
        self.make_btn(view_row, "\uc2dc\uac04\ubcc4", lambda: self.set_activity_view("hour"), variant="nav", height=32).grid(row=0, column=3, sticky="ew", padx=3)
        self.make_btn(view_row, "\uc624\ub298 \uae30\ub85d \uc9c0\uc6b0\uae30", self.clear_activity_today, variant="danger", height=32).grid(row=0, column=4, sticky="ew", padx=3)
        self.make_btn(view_row, "\uc804\uccb4 \uae30\ub85d \uc9c0\uc6b0\uae30", self.clear_activity_all, variant="danger", height=32).grid(row=0, column=5, sticky="ew", padx=3)
        self.activity_controls.grid_remove(); self.refresh_activity_controls()
        self.cards = tk.Canvas(self.content, bg=COL["bg"], highlightthickness=0, bd=0, relief="flat")
        self.cards.grid(row=6, column=0, sticky="nsew")
        self.cards_scroll = ctk.CTkScrollbar(self.content, orientation="vertical", command=self.virtual_yview); self.cards_scroll.grid(row=6, column=1, sticky="ns", padx=(4, 0))
        self.cards.bind("<Configure>", lambda _e: self.render_activity_board() if self.view_mode == "activity" else self.render_matrix_board() if self.view_mode == "matrix" else self.render_virtual_rows(), add="+")
        self.cards.bind("<MouseWheel>", self.virtual_mousewheel, add="+")

    def refresh_top_tabs(self):
        if not hasattr(self, "top_tabs"):
            return
        for mode, btn in self.top_tabs.items():
            active = self.view_mode == mode
            btn.configure(
                fg_color=COL["primary"] if active else COL["panel"],
                hover_color=COL["primary_hover"] if active else COL["hero_soft"],
                text_color="white" if active else COL["text"],
                border_color=COL["primary"] if active else COL["line"],
            )

    def set_color_theme(self, label):
        key = THEME_LABEL_TO_KEY.get(label, "sky")
        if key == self.color_theme_key:
            return
        self.color_theme_key = key
        self.store.state.setdefault("ui", {})["colorTheme"] = key
        self.store.save()
        apply_color_theme(key)
        self.rebuild_layout()

    def rebuild_layout(self):
        for widget in (getattr(self, "side", None), getattr(self, "main", None), getattr(self, "detail", None), getattr(self, "left_handle", None), getattr(self, "right_handle", None)):
            if widget is not None:
                try:
                    widget.destroy()
                except Exception:
                    pass
        self.configure(fg_color=COL["bg"])
        self.virtual_row_widgets = []
        self.drop_targets = {}
        self.build_sidebar()
        self.build_main()
        self.build_detail()
        self.refresh_workspace()

    def toggle_tools(self):
        self.tools_open = not self.tools_open
        if hasattr(self, "toolbar"):
            self.toolbar.grid() if self.tools_open else self.toolbar.grid_remove()

    def toggle_left_panel(self):
        self.left_panel_open = not self.left_panel_open
        self.store.state.setdefault("ui", {})["leftPanelOpen"] = self.left_panel_open
        self.store.save()
        if self.left_panel_open:
            if hasattr(self, "left_handle"):
                self.left_handle.grid_remove()
            self.side.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        else:
            self.side.grid_remove()
            if not hasattr(self, "left_handle"):
                self.left_handle = ctk.CTkButton(self, text="\ubaa9\ub85d >", command=self.toggle_left_panel, width=58, height=120, corner_radius=16, fg_color=COL["sidebar"], hover_color=COL["hero_soft"], text_color=COL["sidebar_text"], font=CONTROL_FONT, border_width=1, border_color=COL["sidebar_line"])
            self.left_handle.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=10)

    def toggle_right_panel(self):
        self.right_panel_open = not self.right_panel_open
        self.store.state.setdefault("ui", {})["rightPanelOpen"] = self.right_panel_open
        self.store.save()
        if self.right_panel_open:
            if hasattr(self, "right_handle"):
                self.right_handle.grid_remove()
            self.detail.grid(row=0, column=2, sticky="nsew", padx=(0, 10), pady=10)
        else:
            self.detail.grid_remove()
            if not hasattr(self, "right_handle"):
                self.right_handle = ctk.CTkButton(self, text="< \uc0c1\uc138", command=self.toggle_right_panel, width=58, height=120, corner_radius=16, fg_color=COL["detail_bg"], hover_color=COL["hero_soft"], text_color=COL["primary"], font=CONTROL_FONT, border_width=1, border_color=COL["line"])
            self.right_handle.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=10)

    def fit_main_content(self, event=None):
        self.pending_main_width = event.width if event else self.main.winfo_width()
        if self.fit_after_id:
            try: self.after_cancel(self.fit_after_id)
            except Exception: pass
        self.fit_after_id = self.after(70, self.apply_fit_main_content)

    def apply_fit_main_content(self):
        self.fit_after_id = None
        width = self.pending_main_width or self.main.winfo_width()
        target = min(MAX_CONTENT_WIDTH, max(360, width - 8))
        self.content.configure(width=target)
        self.apply_top_tab_layout(target)
        self.apply_responsive_panels()

    def register_scroll(self, frame):
        frame.bind("<Enter>", lambda _e, f=frame: setattr(self, "active_scroll", f), add="+")
        frame.bind("<Leave>", lambda _e, f=frame: setattr(self, "active_scroll", None) if self.active_scroll is f else None, add="+")

    def fast_mousewheel(self, event):
        if event.widget is self.cards:
            return self.virtual_mousewheel(event)
        frame = self.active_scroll
        canvas = getattr(frame, "_parent_canvas", None) if frame else None
        if canvas:
            canvas.yview_scroll(int(-event.delta / 120 * SCROLL_UNITS), "units")
            return "break"
        if hasattr(self, "cards"):
            px, py = self.winfo_pointerx(), self.winfo_pointery()
            x1, y1 = self.cards.winfo_rootx(), self.cards.winfo_rooty()
            x2, y2 = x1 + self.cards.winfo_width(), y1 + self.cards.winfo_height()
            if x1 <= px <= x2 and y1 <= py <= y2:
                return self.virtual_mousewheel(event)
        return None

    def action_group(self, parent, title, actions, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent"); frame.grid(row=0, column=col, sticky="nsew", padx=10, pady=10); frame.grid_columnconfigure((0,1), weight=1)
        ctk.CTkLabel(frame, text=title, font=(FONT, 12, "bold"), text_color=COL["muted"], anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        for i, (text, cmd) in enumerate(actions):
            self.make_btn(frame, text, cmd, variant="danger" if text == "삭제" else "soft", height=32).grid(row=1 + i // 2, column=i % 2, sticky="ew", padx=3, pady=3)

    def build_detail(self):
        self.detail = ctk.CTkFrame(self, fg_color=COL["detail_bg"], corner_radius=18, width=390)
        self.detail.grid(row=0, column=2, sticky="nsew", padx=(0, 10), pady=10)
        self.detail.grid_propagate(False); self.detail.grid_columnconfigure(0, weight=1); self.detail.grid_rowconfigure(8, weight=1)
        ctk.CTkLabel(self.detail, text="\uc791\uc5c5 \uc0c1\ud0dc", font=(FONT, 22, "bold"), text_color=COL["text"], anchor="w").grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 6))
        ctk.CTkButton(self.detail, text="\uc811\uae30", command=self.toggle_right_panel, width=58, height=28, corner_radius=12, fg_color=COL["detail_button"], hover_color=COL["hero_soft"], text_color=COL["primary"], font=CONTROL_FONT, border_width=1, border_color=COL["line"]).grid(row=0, column=0, sticky="e", padx=18, pady=(20, 6))
        self.view_body = self.collapsible_detail_section("\ube60\ub978 \ubcf4\uae30", "views", 1, height=150)
        self.view_body.grid_columnconfigure((0,1), weight=1)
        for i, (t, v) in enumerate([("\uc791\uc5c5", "all"), ("\uc624\ub298", "today"), ("\uc911\uc694", "important"), ("\uc6b0\uc120\uc21c\uc704", "matrix"), ("\uc644\ub8cc", "done")]):
            self.make_btn(self.view_body, t, lambda x=v: self.set_view(x), variant="nav", height=31).grid(row=i//2, column=i%2, sticky="ew", padx=3, pady=3)
        kf = ctk.CTkFrame(self.view_body, fg_color="transparent"); kf.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0)); kf.grid_columnconfigure((0,1,2), weight=1)
        for i, (t, v) in enumerate([("\uc804\uccb4", "all"), ("\ud560 \uc77c", "task"), ("\uba54\ubaa8", "memo")]):
            self.make_btn(kf, t, lambda x=v: self.set_kind(x), variant="nav", height=29).grid(row=0, column=i, sticky="ew", padx=2)
        self.date_body = self.collapsible_detail_section("\ub0a0\uc9dc\ubcc4 \ubcf4\uae30", "dates", 3, height=210)
        date_switch = ctk.CTkFrame(self.date_body, fg_color="transparent"); date_switch.grid(row=0, column=0, sticky="ew", padx=5, pady=(6, 6)); date_switch.grid_columnconfigure((0,1), weight=1)
        self.make_btn(date_switch, "\uc0dd\uc131\ub0a0\uc9dc", lambda: self.set_date_filter("created"), variant="nav", height=30).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.make_btn(date_switch, "\uc644\ub8cc\ub0a0\uc9dc", lambda: self.set_date_filter("done"), variant="nav", height=30).grid(row=0, column=1, sticky="ew", padx=(3, 0))
        self.date_frame = ctk.CTkScrollableFrame(self.date_body, fg_color=COL["detail_panel"], height=150, corner_radius=12, border_width=1, border_color=COL["line"])
        self.date_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5)); self.date_frame.grid_columnconfigure(0, weight=1); self.register_scroll(self.date_frame)
        self.memo_body = self.collapsible_detail_section("\uc120\ud0dd \uc791\uc5c5 \uba54\ubaa8", "memo", 5, height=300)
        self.memo_body.grid_columnconfigure(0, weight=1); self.memo_body.grid_rowconfigure(2, weight=1)
        self.detail_title = ctk.CTkLabel(self.memo_body, text="\uc120\ud0dd \uc5c6\uc74c", font=(FONT, 20, "bold"), text_color=COL["text"], anchor="w", justify="left", wraplength=330)
        self.detail_title.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        self.detail_meta = ctk.CTkLabel(self.memo_body, text="\uc791\uc5c5\uc744 \uc120\ud0dd\ud558\uba74 \uba54\ubaa8\ub97c \uc791\uc131\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.", text_color=COL["muted"], anchor="w", justify="left", wraplength=330, font=SMALL_FONT)
        self.detail_meta.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        self.memo = ctk.CTkTextbox(self.memo_body, fg_color=COL["detail_panel"], corner_radius=16, border_width=1, border_color=COL["line"], font=READ_BODY_FONT)
        self.memo.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        ctk.CTkButton(self.memo_body, text="\uba54\ubaa8 \uc800\uc7a5", command=self.save_memo, fg_color=COL["detail_button"], hover_color=COL["hero_soft"], text_color=COL["primary"], height=38, corner_radius=14, font=SMALL_FONT, border_width=1, border_color=COL["line"]).grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 10))

    def refresh_activity_controls(self):
        if not hasattr(self, "activity_status"):
            return
        self.activity_status.configure(text=("활성 창 기록 중" if self.activity_running else "기록이 중지되어 있습니다"))
        self.activity_toggle.configure(text="기록 중지" if self.activity_running else "기록 시작")

    def set_activity_title_logging(self):
        self.activity_log_titles = bool(self.activity_title_var.get())
        self.store.state.setdefault("ui", {})["activityLogTitles"] = self.activity_log_titles
        self.store.save()

    def set_activity_view(self, mode):
        self.activity_view = mode if mode in ("timeline", "group", "program", "hour") else "timeline"
        self.store.state.setdefault("ui", {})["activityView"] = self.activity_view
        self.store.save()
        if self.view_mode != "activity":
            self.set_view("activity")
        else:
            self.refresh_cards()

    def toggle_activity_logging(self):
        if self.activity_running:
            self.stop_activity_logging()
        else:
            self.start_activity_logging()

    def start_activity_logging(self):
        self.activity_running = True
        self.store.state.setdefault("ui", {})["activityRunning"] = True
        self.store.save()
        self.refresh_activity_controls()
        self.poll_activity()
        if self.view_mode == "activity":
            self.refresh_cards()

    def set_activity_group_filter(self, label):
        self.activity_group_filter = label or "all"
        self.store.state.setdefault("ui", {})["activityGroupFilter"] = self.activity_group_filter
        self.store.save()
        if self.view_mode == "activity":
            self.refresh_cards()

    def stop_activity_logging(self):
        self.activity_running = False
        self.store.state.setdefault("ui", {})["activityRunning"] = False
        self.store.save()
        if self.activity_poll_after_id:
            try:
                self.after_cancel(self.activity_poll_after_id)
            except Exception:
                pass
            self.activity_poll_after_id = None
        self.activity_log.close_current()
        self.refresh_activity_controls()
        if self.view_mode == "activity":
            self.refresh_cards()

    def clear_activity_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if not messagebox.askyesno(APP_TITLE, f"{today} \ud65c\ub3d9 \uae30\ub85d\ub9cc \uc9c0\uc6b8\uae4c\uc694?"):
            return
        was_running = self.activity_running
        if was_running:
            self.stop_activity_logging()
        self.activity_log.clear_day(today)
        if was_running:
            self.start_activity_logging()
        self.refresh_cards()

    def clear_activity_all(self):
        if not messagebox.askyesno(APP_TITLE, "\ubaa8\ub4e0 \ud65c\ub3d9 \uae30\ub85d\uc744 \uc804\ubd80 \uc9c0\uc6b8\uae4c\uc694? \uc791\uc5c5 \ud050 \ub370\uc774\ud130\ub294 \uc9c0\uc6cc\uc9c0\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4."):
            return
        was_running = self.activity_running
        if was_running:
            self.stop_activity_logging()
        self.activity_log.clear_all()
        if was_running:
            self.start_activity_logging()
        self.refresh_cards()

    def poll_activity(self):
        if not self.activity_running:
            return
        process_name, window_title = active_window_info(self.activity_log_titles)
        self.activity_log.switch_to(process_name, window_title if self.activity_log_titles else "")
        if self.view_mode == "activity":
            self.render_activity_board()
            self.refresh_activity_controls()
        self.activity_poll_after_id = self.after(1000, self.poll_activity)


    def set_view(self, mode):
        self.card_render_limit = CARD_RENDER_BATCH
        self.view_mode = mode; self.store.state.setdefault("ui", {})["viewMode"] = mode; self.store.save(); self.current_list_id = None; self.current_date = None; self.current_date_mode = None
        if mode != "all": self.current_parent = ROOT_ID
        self.selected_id = None; self.refresh_workspace()
    def set_kind(self, kind): self.card_render_limit = CARD_RENDER_BATCH; self.kind_filter = kind; self.refresh_cards()
    def set_date_filter(self, mode): self.date_filter = mode; self.current_date = None; self.current_date_mode = None; self.refresh_side()
    def save_refresh(self):
        self.store.save()
        self.refresh_path(); self.refresh_cards(); self.refresh_detail(); self.schedule_side_refresh()

    def schedule_side_refresh(self):
        if self.side_refresh_after_id:
            try: self.after_cancel(self.side_refresh_after_id)
            except Exception: pass
        self.side_refresh_after_id = self.after(180, self.apply_side_refresh)

    def apply_side_refresh(self):
        self.side_refresh_after_id = None
        self.refresh_side()

    def refresh_all(self):
        parent = self.store.node(self.current_parent); self.kind_var.set("메모" if parent and parent.get("kind") == "memo" else "할 일")
        self.card_render_limit = CARD_RENDER_BATCH
        self.refresh_path(); self.refresh_side(); self.refresh_cards(); self.refresh_detail()

    def refresh_initial(self):
        parent = self.store.node(self.current_parent); self.kind_var.set("메모" if parent and parent.get("kind") == "memo" else "할 일")
        self.card_render_limit = CARD_RENDER_BATCH
        self.refresh_path(); self.refresh_cards(); self.refresh_detail()

    def refresh_workspace(self):
        parent = self.store.node(self.current_parent); self.kind_var.set("메모" if parent and parent.get("kind") == "memo" else "할 일")
        self.card_render_limit = CARD_RENDER_BATCH
        self.refresh_path(); self.refresh_cards(); self.refresh_detail()

    def refresh_path(self):
        self.clear_frame(self.path_frame)
        if self.view_mode == "activity":
            ctk.CTkLabel(self.path_frame, text="활동 기록", font=(FONT, 26, "bold"), text_color=COL["text"], anchor="w").grid(row=0, column=0, sticky="ew")
            self.hint.configure(text="활성 창이 바뀔 때마다 프로그램 사용 시간을 별도 DB에 기록합니다.")
            return
        if self.view_mode == "pathList" and self.current_list_id:
            item = self.store.path_list(self.current_list_id)
            ctk.CTkLabel(self.path_frame, text=f"목록 > {item.get('title') if item else '목록 없음'}", font=(FONT, 26, "bold"), text_color=COL["text"], anchor="w").grid(row=0, column=0, sticky="ew")
            self.hint.configure(text="바로가기 목록입니다. 목록에서 제거해도 실제 작업은 남습니다."); return
        if self.current_date:
            ctk.CTkLabel(self.path_frame, text=f"{'작성일' if self.current_date_mode == 'created' else '완료일'} > {self.current_date}", font=(FONT, 26, "bold"), text_color=COL["text"], anchor="w").grid(row=0, column=0, sticky="ew")
            self.hint.configure(text="날짜별 바로가기 보기입니다."); return
        parts=[]; cur=self.store.node(self.current_parent)
        while cur:
            parts.append((cur.get("id"), cur.get("title",""))); pid=cur.get("parentId"); cur=self.store.node(pid) if pid else None
        for i, (nid, title) in enumerate(reversed(parts)):
            ctk.CTkButton(self.path_frame, text=title or "루트", command=lambda x=nid: self.open_node(x), fg_color="transparent", hover_color=COL["hero_soft"], text_color=COL["text"], font=(FONT, 24 if i == len(parts)-1 else 18, "bold"), height=34, corner_radius=10, anchor="w").grid(row=0, column=i*2, sticky="w", padx=(0, 4))
            if i < len(parts)-1:
                ctk.CTkLabel(self.path_frame, text=">", font=(FONT, 18, "bold"), text_color=COL["muted"]).grid(row=0, column=i*2+1, sticky="w", padx=(0, 4))
        self.hint.configure(text="작업을 카드로 정리하고, 오늘/중요/메모를 한 화면에서 관리합니다.")

    def clear_frame(self, frame):
        for w in frame.winfo_children(): w.destroy()

    def refresh_side(self):
        self.clear_frame(self.date_frame); self.clear_frame(self.list_frame); self.clear_frame(self.folder_frame)
        created=defaultdict(int); done=defaultdict(int)
        for n in self.store.all_nodes():
            created[date_key(n.get("createdAt"))]+=1
            if n.get("completedAt"): done[date_key(n.get("completedAt"))]+=1
        r=0
        date_source = created if self.date_filter == "created" else done
        date_mode = self.date_filter
        date_items = sorted(date_source, reverse=True)
        for k in date_items[:self.date_side_limit]: self.side_item(self.date_frame, f"{k} ({date_source[k]})", lambda x=k, m=date_mode: self.open_date(m, x), r); r+=1
        if len(date_items) > self.date_side_limit:
            self.side_item(self.date_frame, f"더 보기 ({len(date_items)-self.date_side_limit})", self.show_more_dates, r); r+=1
        if not date_source: ctk.CTkLabel(self.date_frame, text="표시할 날짜가 없습니다", font=CONTROL_FONT, text_color=COL["sidebar_muted"]).grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        for i,item in enumerate(self.store.path_lists[:self.list_side_limit]): self.side_item(self.list_frame, f"{item.get('title','목록')} ({len(item.get('taskIds',[]))})", lambda x=item.get('id'): self.open_list(x), i)
        if len(self.store.path_lists) > self.list_side_limit:
            self.side_item(self.list_frame, f"더 보기 ({len(self.store.path_lists)-self.list_side_limit})", self.show_more_lists, self.list_side_limit)
        self.list_name = ctk.CTkEntry(self.list_frame, placeholder_text="목록 이름", fg_color=COL["panel"], border_color=COL["sidebar_line"], height=34); self.list_name.grid(row=999, column=0, sticky="ew", pady=(8,3))
        bf=ctk.CTkFrame(self.list_frame, fg_color="transparent"); bf.grid(row=1000,column=0,sticky="ew"); bf.grid_columnconfigure((0,1),weight=1); self.make_btn(bf,"만들기",self.create_list).grid(row=0,column=0,sticky="ew",padx=2); self.make_btn(bf,"삭제",self.delete_list).grid(row=0,column=1,sticky="ew",padx=2)
        self.folder_ids=[]
        folders = self.store.folders()
        for i,n in enumerate(folders[:self.folder_side_limit]): self.folder_ids.append(n["id"]); self.side_item(self.folder_frame, f"{n.get('title','폴더')} ({len(self.store.children(n['id']))})", lambda x=n['id']: self.open_node(x), i)
        if len(folders) > self.folder_side_limit:
            self.side_item(self.folder_frame, f"더 보기 ({len(folders)-self.folder_side_limit})", self.show_more_folders, self.folder_side_limit)
        self.folder_name = ctk.CTkEntry(self.folder_frame, placeholder_text="폴더 이름", fg_color=COL["panel"], border_color=COL["sidebar_line"], height=34); self.folder_name.grid(row=999,column=0,sticky="ew",pady=(8,3))
        fb=ctk.CTkFrame(self.folder_frame, fg_color="transparent"); fb.grid(row=1000,column=0,sticky="ew"); fb.grid_columnconfigure((0,1),weight=1); self.make_btn(fb,"만들기",self.create_folder).grid(row=0,column=0,sticky="ew",padx=2); self.make_btn(fb,"삭제",self.delete_folder).grid(row=0,column=1,sticky="ew",padx=2)

    def side_item(self, parent, text, command, row): self.make_btn(parent, text, command, variant="nav", height=30).grid(row=row, column=0, sticky="ew", padx=8, pady=2)
    def show_more_dates(self): self.date_side_limit += SIDE_VISIBLE_LIMIT; self.refresh_side()
    def show_more_lists(self): self.list_side_limit += SIDE_VISIBLE_LIMIT; self.refresh_side()
    def show_more_folders(self): self.folder_side_limit += SIDE_VISIBLE_LIMIT; self.refresh_side()
    def row_visible(self, n):
        if not n or n.get("id") == ROOT_ID: return False
        if n.get("isCustomFolder"): return False
        if self.kind_filter == "task" and n.get("kind") == "memo": return False
        if self.kind_filter == "memo" and n.get("kind") != "memo": return False
        if self.view_mode == "today" and not n.get("isToday"): return False
        if self.view_mode == "important" and not n.get("isImportant"): return False
        if self.view_mode == "done" and not n.get("completed"): return False
        if self.view_mode in ("today","important","matrix") and n.get("kind") == "memo": return False
        q=self.search.get().strip().lower()
        if q and q not in n.get("title","").lower() and q not in n.get("memo","").lower(): return False
        return True

    def visible_ids(self):
        if self.view_mode == "pathList" and self.current_list_id:
            item=self.store.path_list(self.current_list_id); ids=item.get("taskIds",[]) if item else []; return [x for x in sorted(ids,key=self.store.sort_key) if self.row_visible(self.store.node(x))]
        if self.current_date:
            field="createdAt" if self.current_date_mode=="created" else "completedAt"; ids=[n["id"] for n in self.store.all_nodes() if date_key(n.get(field))==self.current_date]; return [x for x in sorted(ids,key=self.store.sort_key) if self.row_visible(self.store.node(x))]
        if self.view_mode in ("today","important","done") or self.search.get().strip(): return sorted([n["id"] for n in self.store.all_nodes() if self.row_visible(n)], key=self.store.sort_key)
        return [x for x in self.store.children(self.current_parent) if self.row_visible(self.store.node(x))]

    def activity_group_overrides(self):
        return self.store.state.setdefault("ui", {}).setdefault("activityGroupOverrides", {})

    def activity_group_labels(self):
        labels = [label for key, (label, _color, _keywords) in ACTIVITY_GROUPS.items() if key != "other"]
        labels.append(ACTIVITY_GROUPS["other"][0])
        for label in self.activity_group_overrides().values():
            if label and label not in labels:
                labels.append(label)
        return labels

    def show_activity_group_popup(self, process_name):
        process_key = (process_name or "").strip().lower()
        if not process_key:
            return
        win = tk.Toplevel(self)
        win.title("활동 그룹 등록")
        win.transient(self)
        win.grab_set()
        win.configure(bg=COL["bg"])
        win.geometry("360x430")
        frame = tk.Frame(win, bg=COL["bg"])
        frame.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(frame, text=process_name, bg=COL["bg"], fg=COL["text"], font=(READ_FONT, 16, "bold"), anchor="w").pack(fill="x")
        tk.Label(frame, text="이 프로그램을 넣을 그룹을 선택하세요.", bg=COL["bg"], fg=COL["muted"], font=(READ_FONT, 10), anchor="w").pack(fill="x", pady=(4, 12))
        body = tk.Frame(frame, bg=COL["bg"])
        body.pack(fill="both", expand=True)

        def choose(label):
            overrides = self.activity_group_overrides()
            if label == ACTIVITY_GROUPS["other"][0]:
                overrides.pop(process_key, None)
            else:
                overrides[process_key] = label
            self.store.save()
            win.destroy()
            if self.view_mode == "activity":
                self.refresh_cards()

        for label in self.activity_group_labels():
            btn = tk.Button(body, text=label, command=lambda x=label: choose(x), bg="#ffffff", fg=COL["text"], activebackground=COL["hero_soft"], relief="flat", bd=0, font=(READ_FONT, 10, "bold"), anchor="w", padx=12, pady=8)
            btn.pack(fill="x", pady=3)

        tk.Label(frame, text="새 그룹 만들기", bg=COL["bg"], fg=COL["muted"], font=(READ_FONT, 9, "bold"), anchor="w").pack(fill="x", pady=(12, 4))
        new_entry = tk.Entry(frame, font=(READ_FONT, 11), relief="flat", bg="#ffffff", fg=COL["text"])
        new_entry.pack(fill="x", ipady=8)
        tk.Button(frame, text="새 그룹에 등록", command=lambda: choose(new_entry.get().strip()) if new_entry.get().strip() else None, bg=COL["primary"], fg="white", activebackground=COL["primary_hover"], relief="flat", bd=0, font=(READ_FONT, 10, "bold"), padx=12, pady=9).pack(fill="x", pady=(8, 0))

    def apply_context_layout(self):
        if not hasattr(self, "add_panel") or not hasattr(self, "detail"):
            return
        if self.view_mode == "activity":
            self.add_panel.grid_remove()
            self.detail.grid_remove()
            if hasattr(self, "right_handle"):
                self.right_handle.grid_remove()
        elif self.view_mode == "matrix":
            self.add_panel.grid()
            self.detail.grid_remove()
            if hasattr(self, "right_handle"):
                self.right_handle.grid_remove()
        else:
            self.add_panel.grid()
            if self.right_panel_open:
                self.detail.grid(row=0, column=2, sticky="nsew", padx=(0, 10), pady=10)
                if hasattr(self, "right_handle"):
                    self.right_handle.grid_remove()
            else:
                self.detail.grid_remove()
                if not hasattr(self, "right_handle"):
                    self.right_handle = ctk.CTkButton(self, text="< \uc0c1\uc138", command=self.toggle_right_panel, width=58, height=120, corner_radius=16, fg_color=COL["detail_bg"], hover_color=COL["hero_soft"], text_color=COL["primary"], font=CONTROL_FONT, border_width=1, border_color=COL["line"])
                self.right_handle.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=10)

    def refresh_cards(self):
        self.drop_targets={}
        self.refresh_top_tabs()
        self.apply_context_layout()
        if hasattr(self, "activity_controls"):
            self.activity_controls.grid() if self.view_mode == "activity" else self.activity_controls.grid_remove()
        if self.view_mode == "activity":
            self.cards.configure(yscrollcommand=self.cards_scroll.set)
            self.cards_scroll.configure(command=self.cards.yview)
            self.summary.configure(text="\uae30\ub85d \uc911" if self.activity_running else "\uae30\ub85d \uc911\uc9c0")
            self.virtual_ids = []
            self.virtual_scroll_y = 0
            self.children_count_cache = {}
            self.refresh_activity_controls()
            self.render_activity_board()
            return
        self.cards_scroll.configure(command=self.virtual_yview)
        if self.view_mode=="matrix":
            ids = [n["id"] for n in self.store.all_nodes() if self.row_visible(n) and not n.get("completed")]
            counts = defaultdict(int)
            for nid in ids:
                counts[matrix_bucket(self.store.node(nid) or {})] += 1
            self.matrix_ids = sorted(ids, key=lambda nid: (matrix_bucket(self.store.node(nid) or {}), self.store.sort_key(nid)))
            self.summary.configure(text=f"4\ubd84\ud560 {len(ids)}\uac1c")
            self.virtual_ids = []
            self.virtual_scroll_y = 0
            self.virtual_hover_id = None
            self.children_count_cache = {}
            self.render_matrix_board()
            return
        ids=self.visible_ids(); self.summary.configure(text=f"{len(ids)}개 항목")
        self.virtual_ids = ids
        self.virtual_scroll_y = 0
        self.virtual_hover_id = None
        self.children_count_cache = {}
        self.render_virtual_rows()

    def render_matrix_board(self):
        self.cards.delete("matrix"); self.cards.delete("activity"); self.cards.delete("empty")
        for row in self.virtual_row_widgets:
            self.cards.itemconfigure(row["item"], state="hidden"); row["nid"] = None
        ids = getattr(self, "matrix_ids", [])
        width = max(620, self.cards.winfo_width()); height = max(500, self.cards.winfo_height())
        gap = 14; compact = width < 980
        if compact:
            box_w = max(360, width - gap * 2); box_h = 300
            positions = {i: (gap, gap + i * (box_h + gap)) for i in range(4)}; total_h = gap * 5 + box_h * 4
        else:
            box_w = max(330, (width - gap * 3) // 2); box_h = max(290, (height - gap * 3) // 2)
            positions = {0: (gap, gap), 1: (gap * 2 + box_w, gap), 2: (gap, gap * 2 + box_h), 3: (gap * 2 + box_w, gap * 2 + box_h)}; total_h = max(height, gap * 3 + box_h * 2)
        styles = {
            0: ("\uae09\ud558\uace0 \uc911\uc694\ud55c \uc77c", "\uc624\ub298 \ubc14\ub85c \ucc98\ub9ac\ud560 \ud575\uc2ec", "#f3adb4", "#fff2f4"),
            1: ("\uc911\uc694\ud558\uc9c0\ub9cc \uae09\ud558\uc9c0 \uc54a\uc740 \uc77c", "\uafb8\uc900\ud788 \ud0a4\uc6b8 \uacc4\ud68d", "#f0c46b", "#fff8e7"),
            2: ("\uae09\ud558\uc9c0\ub9cc \uc911\uc694\ud558\uc9c0 \uc54a\uc740 \uc77c", "\ube68\ub9ac \uc815\ub9ac\ud560 \uc7a1\uc74c", "#8fc7e8", "#eff9ff"),
            3: ("\ub458 \ub2e4 \uc544\ub2cc \uc77c", "\ub098\uc911\uc5d0 \ubcf4\uac70\ub098 \ube44\uc6b8 \uac83", "#a8b4c2", "#f7fafc"),
        }
        buckets = {i: [] for i in range(4)}
        for nid in ids:
            n = self.store.node(nid) or {}
            if not n.get("completed"): buckets[matrix_bucket(n)].append(nid)
        self.drop_targets = {}
        def next_actions(root_id, limit=3):
            out = []
            def walk(pid):
                if len(out) >= limit: return
                for child_id in self.store.children(pid):
                    child = self.store.node(child_id) or {}
                    if child.get("kind") != "memo" and not child.get("completed") and not child.get("isCustomFolder"):
                        out.append(child_id)
                        if len(out) >= limit: return
                    walk(child_id)
                    if len(out) >= limit: return
            walk(root_id); return out
        def bind_tag(tag, nid, open_it=False):
            self.cards.tag_bind(tag, "<Button-1>", lambda e, item=nid, open_it=open_it: ((self.open_node(item) if open_it else self.select_node(item)), "break")[-1])
            self.cards.tag_bind(tag, "<Double-Button-1>", lambda e, item=nid: (self.open_node(item), "break")[-1])
            self.cards.tag_bind(tag, "<Button-3>", lambda e, item=nid: (self.quick_done(item), "break")[-1])
            self.cards.tag_bind(tag, "<Enter>", lambda e: self.cards.configure(cursor="hand2")); self.cards.tag_bind(tag, "<Leave>", lambda e: self.cards.configure(cursor=""))
        for bucket, (x, y) in positions.items():
            title, subtitle, border, fill = styles[bucket]
            self.cards.create_rectangle(x, y, x + box_w, y + box_h, fill=fill, outline=border, width=2, tags=("matrix",))
            self.cards.create_text(x + 18, y + 14, text=title, anchor="nw", fill=COL["text"], font=(READ_FONT, 13, "bold"), width=box_w - 110, tags=("matrix",))
            self.cards.create_text(x + 18, y + 39, text=subtitle, anchor="nw", fill=COL["muted"], font=(READ_FONT, 9), width=box_w - 110, tags=("matrix",))
            self.cards.create_rectangle(x + box_w - 68, y + 16, x + box_w - 18, y + 42, fill="#ffffff", outline=border, width=1, tags=("matrix",))
            self.cards.create_text(x + box_w - 43, y + 22, text=f"{len(buckets[bucket])}\uac1c", anchor="n", fill=COL["text"], font=(READ_FONT, 9, "bold"), tags=("matrix",))
            cy = y + 72; card_h = 86; max_items = max(1, (box_h - 104) // (card_h + 9)); shown = sorted(buckets[bucket], key=self.store.sort_key)[:max_items]
            for nid in shown:
                n = self.store.node(nid) or {}; item_tag = f"matrix-item-{nid}"
                self.cards.create_rectangle(x + 12, cy, x + box_w - 12, cy + card_h, fill="#ffffff", outline=COL["line"], width=1, tags=("matrix", item_tag))
                self.cards.create_rectangle(x + 22, cy + 12, x + 27, cy + card_h - 12, fill=border, outline=border, tags=("matrix", item_tag))
                self.cards.create_text(x + 40, cy + 10, text=n.get("title", "\uc774\ub984 \uc5c6\uc74c"), anchor="nw", fill=COL["text"], font=(READ_FONT, 10, "bold"), width=max(160, box_w - 100), tags=("matrix", item_tag))
                meta = ["\uba54\ubaa8" if n.get("kind") == "memo" else "\ud560 \uc77c", "\uc6b0\uc120 \uc5c6\uc74c" if n.get("priority") is None else f"\uc6b0\uc120 {n.get('priority')}"]
                child_count = len(self.store.children(nid))
                if child_count: meta.append(f"\ud558\uc704 {child_count}")
                meta.append(human_time(n.get("createdAt")))
                self.cards.create_text(x + 40, cy + 31, text=" \u00b7 ".join(meta), anchor="nw", fill=COL["muted"], font=(READ_FONT, 8), width=max(160, box_w - 100), tags=("matrix", item_tag))
                actions = next_actions(nid, 3)
                if actions:
                    self.cards.create_text(x + 40, cy + 54, text="\ub2e4\uc74c \ud589\ub3d9", anchor="nw", fill=COL["muted"], font=(READ_FONT, 8, "bold"), tags=("matrix", item_tag))
                    ax = x + 96; available = max(90, box_w - 130); step = max(92, available // max(1, len(actions)))
                    for action_id in actions:
                        action = self.store.node(action_id) or {}; a_tag = f"matrix-next-{action_id}-{nid}"
                        self.cards.create_text(ax, cy + 54, text=action.get("title", "\uc774\ub984 \uc5c6\uc74c"), anchor="nw", fill=COL["primary"], font=(READ_FONT, 8, "bold"), width=step - 8, tags=("matrix", a_tag))
                        bind_tag(a_tag, action_id, open_it=True); ax += step
                else:
                    self.cards.create_text(x + 40, cy + 54, text="\ud558\uc704 \ud560 \uc77c\uc774 \uc5c6\uc73c\uba74 \ub354 \ucabc\uac1c\uac70\ub098 \uc644\ub8cc\ud558\uc138\uc694", anchor="nw", fill=COL["muted"], font=(READ_FONT, 8), width=max(160, box_w - 100), tags=("matrix", item_tag))
                bind_tag(item_tag, nid); cy += card_h + 9
            remain = len(buckets[bucket]) - len(shown)
            if remain > 0: self.cards.create_text(x + 18, y + box_h - 26, text=f"\uc678 {remain}\uac1c \ub354 \uc788\uc74c", anchor="nw", fill=COL["muted"], font=(READ_FONT, 8), tags=("matrix",))
            if not buckets[bucket]:
                self.cards.create_rectangle(x + 18, y + 84, x + box_w - 18, y + 128, fill="#ffffff", outline=COL["line"], dash=(3, 2), tags=("matrix",))
                self.cards.create_text(x + box_w // 2, y + 100, text="\ud45c\uc2dc\ud560 \uc791\uc5c5\uc774 \uc5c6\uc2b5\ub2c8\ub2e4", anchor="n", fill=COL["muted"], font=(READ_FONT, 9), tags=("matrix",))
        self.cards.configure(scrollregion=(0, 0, width, total_h)); self.cards_scroll.set(0, min(1, height / max(height, total_h)))

    def render_activity_board(self):
        self.cards.delete("matrix")
        self.cards.delete("activity")
        self.cards.delete("empty")
        self.drop_targets = {}
        for row in self.virtual_row_widgets:
            self.cards.itemconfigure(row["item"], state="hidden")
            row["nid"] = None
        width = max(760, self.cards.winfo_width())
        height = max(560, self.cards.winfo_height())
        today = datetime.now().strftime("%Y-%m-%d")
        total = self.activity_log.total_seconds(today)
        status = "?? ?" if self.activity_running else "?? ??"
        labels = {"timeline": "\ud558\ub8e8 \ud750\ub984", "group": "\ubd84\ub958\ubcc4", "program": "\ud504\ub85c\uadf8\ub7a8\ubcc4", "hour": "\uc2dc\uac04\ubcc4"}
        mode_label = labels.get(self.activity_view, "?? ??")
        group_overrides = self.activity_group_overrides()

        def bind_click(tag, callback):
            self.cards.tag_bind(tag, "<Button-1>", lambda e: (callback(), "break")[-1])
            self.cards.tag_bind(tag, "<Enter>", lambda e: self.cards.configure(cursor="hand2"))
            self.cards.tag_bind(tag, "<Leave>", lambda e: self.cards.configure(cursor=""))

        def toggle_program(name):
            if name in self.activity_expanded_programs:
                self.activity_expanded_programs.remove(name)
            else:
                self.activity_expanded_programs.add(name)
            self.render_activity_board()

        def bind_activity_action(tag, process_name):
            bind_click(tag, lambda p=process_name: self.show_activity_group_popup(p))

        def activity_group_button(row_tag, button_tag, x1, y1, process_name):
            self.cards.create_rectangle(x1, y1, x1 + 94, y1 + 28, fill=COL["hero_soft"], outline=COL["line"], width=1, tags=("activity", row_tag, button_tag), state="hidden")
            self.cards.create_text(x1 + 47, y1 + 8, text="?? ??", anchor="n", fill=COL["primary"], font=(READ_FONT, 8, "bold"), tags=("activity", row_tag, button_tag), state="hidden")
            self.cards.tag_bind(row_tag, "<Enter>", lambda e, t=button_tag: self.cards.itemconfigure(t, state="normal"))
            self.cards.tag_bind(row_tag, "<Leave>", lambda e, t=button_tag: self.cards.itemconfigure(t, state="hidden"))
            bind_activity_action(button_tag, process_name)

        def bind_group_filter(tag, label):
            bind_click(tag, lambda x=label: self.set_activity_group_filter(x))

        def empty_message(y_pos):
            self.cards.create_text(34, y_pos, text="\uc544\uc9c1 \uae30\ub85d\ub41c \ud65c\ub3d9\uc774 \uc5c6\uc2b5\ub2c8\ub2e4. \uc704 \uc870\uc791\uc904\uc5d0\uc11c \uae30\ub85d \uc2dc\uc791\uc744 \ub204\ub974\uc138\uc694.", anchor="nw", fill=COL["muted"], font=(READ_FONT, 12), tags=("activity",))

        def parse_day_seconds(value):
            try:
                dt = datetime.fromisoformat(value)
            except Exception:
                return None
            day_start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            return max(0, min(24 * 3600, int((dt - day_start).total_seconds())))

        def draw_timeline_scale(left, right, top, bottom):
            timeline_w = max(1, right - left)
            for hour in range(0, 25, 3):
                x = left + int(timeline_w * hour / 24)
                self.cards.create_line(x, top, x, bottom, fill="#dceaf1", tags=("activity",))
                self.cards.create_text(x, top - 4, text=f"{hour:02d}", anchor="s", fill=COL["muted"], font=(READ_FONT, 8), tags=("activity",))

        def draw_session_bar(left, right, y_pos, started, ended, seconds, color, label=""):
            s = parse_day_seconds(started)
            e = parse_day_seconds(ended)
            if s is None or e is None:
                return
            e = max(s + max(60, int(seconds or 0)), e)
            e = min(24 * 3600, e)
            timeline_w = max(1, right - left)
            x1 = left + int(timeline_w * s / (24 * 3600))
            x2 = max(x1 + 4, left + int(timeline_w * e / (24 * 3600)))
            self.cards.create_rectangle(x1, y_pos, x2, y_pos + 18, fill=color, outline=color, tags=("activity",))
            if label and x2 - x1 > 82:
                self.cards.create_text(x1 + 5, y_pos + 2, text=label, anchor="nw", fill="white", font=(READ_FONT, 7, "bold"), tags=("activity",))

        self.cards.create_rectangle(12, 12, width - 12, 118, fill="#ffffff", outline=COL["line"], width=1, tags=("activity",))
        self.cards.create_text(34, 30, text="?? ??", anchor="nw", fill=COL["text"], font=(READ_FONT, 18, "bold"), tags=("activity",))
        self.cards.create_text(34, 62, text=f"{today} ? {status} ? ?? ?? {format_duration(total)}", anchor="nw", fill=COL["muted"], font=(READ_FONT, 10), tags=("activity",))
        self.cards.create_text(34, 88, text="\uae30\ubcf8\uc740 \uc804\uccb4 \ud750\ub984\uc744 \ud55c \uc904\ub85c \ubcf4\uace0, \ud544\uc694\ud560 \ub54c \ud504\ub85c\uadf8\ub7a8/\ubd84\ub958\ubcc4\ub85c \ud3bc\uccd0\uc11c \ud655\uc778\ud569\ub2c8\ub2e4.", anchor="nw", fill=COL["muted"], font=(READ_FONT, 9), tags=("activity",))
        self.cards.create_rectangle(width - 170, 36, width - 34, 72, fill=COL["hero_soft"], outline=COL["line"], width=1, tags=("activity",))
        self.cards.create_text(width - 150, 46, text=mode_label, anchor="nw", fill=COL["primary"], font=(READ_FONT, 10, "bold"), tags=("activity",))
        y = 144

        if self.activity_view == "timeline":
            sessions = self.activity_log.sessions_for_day(today)
            if not sessions:
                empty_message(y)
            else:
                left = 112
                right = width - 34
                top = y + 36
                self.cards.create_text(34, y, text="?? ?? ??", anchor="nw", fill=COL["text"], font=(READ_FONT, 13, "bold"), tags=("activity",))
                self.cards.create_text(34, y + 26, text="??", anchor="nw", fill=COL["text"], font=(READ_FONT, 9, "bold"), tags=("activity",))
                self.cards.create_rectangle(left, top, right, top + 18, fill="#ffffff", outline=COL["line"], tags=("activity",))
                draw_timeline_scale(left, right, top - 18, top + 22)
                for started, ended, seconds, name, title in sessions:
                    _key, _label, color = activity_group_for(name, title, group_overrides)
                    draw_session_bar(left, right, top, started, ended, seconds, color, name.replace(".exe", ""))

                y = top + 52
                lanes = []
                seen = set()
                for started, ended, seconds, name, title in sessions:
                    key, label, color = activity_group_for(name, title, group_overrides)
                    if key not in seen:
                        seen.add(key)
                        lanes.append((key, label, color))
                self.cards.create_text(34, y, text="\ubd84\ub958\ubcc4 \ud750\ub984", anchor="nw", fill=COL["text"], font=(READ_FONT, 12, "bold"), tags=("activity",))
                y += 34
                lane_y = {}
                for idx, (key, label, color) in enumerate(lanes):
                    yy = y + idx * 34
                    lane_y[key] = yy
                    self.cards.create_text(34, yy + 3, text=label, anchor="nw", fill=COL["text"], font=(READ_FONT, 9, "bold"), width=70, tags=("activity",))
                    self.cards.create_rectangle(left, yy, right, yy + 18, fill="#ffffff", outline=COL["line"], tags=("activity",))
                for started, ended, seconds, name, title in sessions:
                    key, label, color = activity_group_for(name, title, group_overrides)
                    draw_session_bar(left, right, lane_y.get(key, y), started, ended, seconds, color)

                y += max(1, len(lanes)) * 34 + 22
                self.cards.create_text(34, y, text="?? ??", anchor="nw", fill=COL["text"], font=(READ_FONT, 12, "bold"), tags=("activity",))
                y += 30
                recent_sessions = sessions[-8:]
                if len(sessions) > 8:
                    self.cards.create_text(width - 230, y - 28, text=f"?? 8?? ?? ? ?? {len(sessions)}?", anchor="nw", fill=COL["muted"], font=(READ_FONT, 8), tags=("activity",))
                for started, ended, seconds, name, title in recent_sessions:
                    key, label, color = activity_group_for(name, title, group_overrides)
                    self.cards.create_rectangle(34, y, width - 24, y + 40, fill="#ffffff", outline=COL["line"], tags=("activity",))
                    self.cards.create_rectangle(44, y + 9, 50, y + 31, fill=color, outline=color, tags=("activity",))
                    self.cards.create_text(60, y + 8, text=f"{started[11:16]}-{ended[11:16]}  {label}", anchor="nw", fill=COL["text"], font=(READ_FONT, 9, "bold"), tags=("activity",))
                    self.cards.create_text(250, y + 8, text=f"{name} ? {title}", anchor="nw", fill=COL["muted"], font=(READ_FONT, 9), width=max(240, width - 430), tags=("activity",))
                    self.cards.create_text(width - 122, y + 8, text=format_duration(seconds), anchor="nw", fill=COL["muted"], font=(READ_FONT, 8), tags=("activity",))
                    y += 46

        elif self.activity_view == "group":
            rows = self.activity_log.group_summary(today, group_overrides)
            if not rows:
                empty_message(y)
            filter_labels = ["all"]
            for row in rows:
                if row[1] not in filter_labels:
                    filter_labels.append(row[1])
            chip_x = 34
            for idx, label in enumerate(filter_labels):
                text = "??" if label == "all" else label
                active = self.activity_group_filter == label or (label == "all" and self.activity_group_filter == "all")
                tag = f"activity-filter-{idx}"
                chip_w = max(70, min(150, 18 + len(text) * 10))
                self.cards.create_rectangle(chip_x, y, chip_x + chip_w, y + 30, fill=COL["primary"] if active else "#ffffff", outline=COL["line"], width=1, tags=("activity", tag))
                self.cards.create_text(chip_x + chip_w // 2, y + 8, text=text, anchor="n", fill="white" if active else COL["primary"], font=(READ_FONT, 8, "bold"), tags=("activity", tag))
                bind_group_filter(tag, label)
                chip_x += chip_w + 8
                if chip_x > width - 180:
                    chip_x = 34
                    y += 36
            y += 46
            if self.activity_group_filter != "all":
                rows = [row for row in rows if row[1] == self.activity_group_filter]
            max_total = max([row[3] for row in rows] or [1])
            if not rows:
                self.cards.create_text(34, y, text="\uc774 \uadf8\ub8f9\uc5d0 \ud45c\uc2dc\ud560 \ud65c\ub3d9\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.", anchor="nw", fill=COL["muted"], font=(READ_FONT, 12), tags=("activity",))
            for key, label, color, seconds, count, programs, titles in rows:
                row_h = 72 + min(3, len(programs)) * 18
                self.cards.create_rectangle(24, y, width - 24, y + row_h - 10, fill="#ffffff", outline=COL["line"], tags=("activity",))
                self.cards.create_rectangle(38, y + 14, 46, y + row_h - 24, fill=color, outline=color, tags=("activity",))
                self.cards.create_text(58, y + 12, text=label, anchor="nw", fill=COL["text"], font=(READ_FONT, 12, "bold"), tags=("activity",))
                self.cards.create_text(width - 200, y + 12, text=f"{format_duration(seconds)} ? {count}?", anchor="nw", fill=COL["muted"], font=(READ_FONT, 9), tags=("activity",))
                bar_w = int((width - 330) * (seconds / max_total)) if max_total else 0
                self.cards.create_rectangle(58, y + 38, 58 + max(4, bar_w), y + 43, fill=color, outline=color, tags=("activity",))
                sy = y + 52
                for pname, pseconds in programs:
                    self.cards.create_text(64, sy, text=f"- {pname} ? {format_duration(pseconds)}", anchor="nw", fill=COL["muted"], font=(READ_FONT, 9), tags=("activity",))
                    sy += 18
                if titles:
                    self.cards.create_text(310, y + 52, text=" / ".join(titles), anchor="nw", fill=COL["muted"], font=(READ_FONT, 8), width=max(220, width - 520), tags=("activity",))
                y += row_h

        elif self.activity_view == "program":
            rows = self.activity_log.program_summary(today)
            title_samples = self.activity_log.program_title_details(today)
            if not rows:
                empty_message(y)
            max_total = max([sec for _, sec, _ in rows] or [1])
            for idx, (name, seconds, count) in enumerate(rows):
                titles = title_samples.get(name, [])
                is_open = name in self.activity_expanded_programs
                visible_titles = titles if is_open else titles[:3]
                key, group_label, group_color = activity_group_for(name, titles[0][0] if titles else "", group_overrides)
                row_h = 72 + len(visible_titles) * 24 + (20 if (not is_open and len(titles) > 3) else 0)
                y0 = y
                row_tag = f"activity-program-row-{idx}"
                button_tag = f"activity-program-group-{idx}"
                self.cards.create_rectangle(24, y0, width - 24, y0 + row_h - 10, fill="#ffffff", outline=COL["line"], width=1, tags=("activity", row_tag))
                self.cards.create_rectangle(36, y0 + 14, 42, y0 + row_h - 24, fill=group_color, outline=group_color, tags=("activity", row_tag))
                self.cards.create_text(54, y0 + 12, text=("? " if is_open else "? ") + name, anchor="nw", fill=COL["text"], font=(READ_FONT, 12, "bold"), tags=("activity", row_tag))
                self.cards.create_text(230, y0 + 14, text=group_label, anchor="nw", fill=group_color, font=(READ_FONT, 9, "bold"), tags=("activity", row_tag))
                self.cards.create_text(width - 190, y0 + 12, text=f"{format_duration(seconds)} ? {count}?", anchor="nw", fill=COL["muted"], font=(READ_FONT, 9), tags=("activity", row_tag))
                bar_w = int((width - 350) * (seconds / max_total)) if max_total else 0
                self.cards.create_rectangle(54, y0 + 38, 54 + max(4, bar_w), y0 + 43, fill=group_color, outline=group_color, tags=("activity", row_tag))
                self.cards.create_text(54, y0 + 50, text="\ud074\ub9ad\ud558\uba74 \uc774 \ud504\ub85c\uadf8\ub7a8\uc5d0\uc11c \uc5f4\ub9b0 \ucc3d \uc81c\ubaa9\uc744 \ud3bc\uccd0\ubd05\ub2c8\ub2e4.", anchor="nw", fill=COL["muted"], font=(READ_FONT, 8), tags=("activity", row_tag))
                bind_click(row_tag, lambda n=name: toggle_program(n))
                activity_group_button(row_tag, button_tag, width - 300, y0 + 42, name)
                sy = y0 + 72
                for title, title_seconds, title_count, last_seen in visible_titles:
                    self.cards.create_text(66, sy, text=f"- {title}", anchor="nw", fill=COL["muted"], font=(READ_FONT, 9), width=max(260, width - 370), tags=("activity", row_tag))
                    self.cards.create_text(width - 190, sy, text=f"{format_duration(title_seconds)} ? {title_count}?", anchor="nw", fill=COL["muted"], font=(READ_FONT, 8), tags=("activity", row_tag))
                    sy += 24
                if not is_open and len(titles) > 3:
                    self.cards.create_text(66, sy, text=f"? {len(titles) - 3}? ? ??", anchor="nw", fill=COL["primary"], font=(READ_FONT, 8, "bold"), tags=("activity", row_tag))
                y += row_h
        else:
            grouped = self.activity_log.hourly_sessions(today)
            if not grouped:
                empty_message(y)
            for hour in sorted(grouped):
                self.cards.create_text(34, y, text=f"{hour}?", anchor="nw", fill=COL["text"], font=(READ_FONT, 12, "bold"), tags=("activity",))
                y += 28
                for idx, (started, ended, name, title, seconds) in enumerate(grouped[hour][:10]):
                    key, label, color = activity_group_for(name, title, group_overrides)
                    row_tag = f"activity-hour-row-{hour}-{idx}"
                    button_tag = f"activity-hour-group-{hour}-{idx}"
                    self.cards.create_rectangle(44, y, width - 34, y + 46, fill="#ffffff", outline=COL["line"], width=1, tags=("activity", row_tag))
                    self.cards.create_rectangle(54, y + 10, 60, y + 36, fill=color, outline=color, tags=("activity", row_tag))
                    self.cards.create_text(70, y + 7, text=f"{started}-{ended}  {name} ? {label}", anchor="nw", fill=COL["text"], font=(READ_FONT, 10, "bold"), tags=("activity", row_tag))
                    self.cards.create_text(70, y + 26, text=title, anchor="nw", fill=COL["muted"], font=(READ_FONT, 9), width=max(240, width - 360), tags=("activity", row_tag))
                    self.cards.create_text(width - 160, y + 10, text=format_duration(seconds), anchor="nw", fill=COL["muted"], font=(READ_FONT, 9), tags=("activity", row_tag))
                    activity_group_button(row_tag, button_tag, width - 260, y + 10, name)
                    y += 52
                y += 12
        self.cards.configure(scrollregion=(0, 0, width, max(height, y + 60)))
        self.cards_scroll.set(0, min(1, height / max(height, y + 60)))

    def render_virtual_rows(self):
        if self.view_mode == "activity":
            self.render_activity_board()
            return
        if self.view_mode == "matrix":
            self.render_matrix_board()
            return
        self.cards.delete("matrix")
        self.cards.delete("activity")
        self.cards.delete("empty")
        total = len(self.virtual_ids)
        width = max(1, self.cards.winfo_width())
        height = max(1, self.cards.winfo_height())
        max_y = max(0, self.virtual_total_height() - height)
        self.virtual_scroll_y = max(0, min(max_y, self.virtual_scroll_y))
        if not total:
            for row in self.virtual_row_widgets:
                self.cards.itemconfigure(row["item"], state="hidden")
            self.cards.create_text(width//2, 80, text="아직 표시할 작업이 없습니다", fill=COL["text"], font=(FONT, 18, "bold"), tags=("empty",))
            self.cards.create_text(width//2, 112, text="위 입력창에서 작업을 만들고 하위 작업으로 쪼개보세요.", fill=COL["muted"], font=BODY_FONT, tags=("empty",))
            self.sync_virtual_scrollbar()
            return
        self.ensure_virtual_row_pool()
        start = max(0, self.virtual_scroll_y // VROW_HEIGHT)
        offset = -(self.virtual_scroll_y % VROW_HEIGHT)
        needed = self.virtual_visible_count()
        self.drop_targets = {}
        for pool_index, row in enumerate(self.virtual_row_widgets):
            data_index = start + pool_index
            if pool_index >= needed or data_index >= total:
                self.cards.itemconfigure(row["item"], state="hidden")
                row["nid"] = None
                continue
            nid = self.virtual_ids[data_index]
            y = offset + pool_index * VROW_HEIGHT
            row["nid"] = nid
            self.update_virtual_row(row, nid)
            self.cards.coords(row["item"], 8, y + 4)
            self.cards.itemconfigure(row["item"], width=max(100, width - 18), height=78, state="normal")
            self.drop_targets[row["frame"]] = nid
        self.cards.configure(scrollregion=(0, 0, width, self.virtual_total_height()))
        self.sync_virtual_scrollbar()

    def update_virtual_row(self, row, nid):
        n = self.store.node(nid)
        if not n:
            return
        is_memo = n.get("kind") == "memo"
        is_folder = n.get("isCustomFolder")
        is_done = n.get("completed")
        bg = COL["folder"] if is_folder else COL["memo"] if is_memo else COL["done"] if is_done else "#ffffff"
        accent = "#6f9fca" if is_folder else "#d69a33" if is_memo else "#65ad74" if is_done else "#8fb0bf"
        if n.get("isToday"):
            accent = COL["primary"]
        if n.get("isImportant"):
            accent = COL["accent"]
        badge_text = "\ud504\ub85c\uc81d\ud2b8" if is_folder else "\uba54\ubaa8" if is_memo else "\uc791\uc5c5"
        row["frame"].configure(fg_color=bg, height=78, border_color=COL["line"], border_width=1)
        row["accent"].configure(fg_color=accent, height=58)
        row["title"].configure(text=("\uc644\ub8cc  " if is_done else "") + n.get("title", "\uc774\ub984 \uc5c6\uc74c"), fg_color="transparent")
        child_count = len(self.store.children(nid))
        meta = ["\uba54\ubaa8" if is_memo else "\ud560 \uc77c"]
        meta.append("\uc6b0\uc120 \uc5c6\uc74c" if n.get("priority") is None else f"\uc6b0\uc120 {n.get('priority')}")
        if child_count:
            meta.append(f"\ud558\uc704 {child_count}")
        meta.append(human_time(n.get("createdAt")))
        row["meta"].configure(text=" \u00b7 ".join(meta), fg_color="transparent")
        states = []
        if n.get("isToday"):
            states.append("\uc624\ub298")
        if n.get("isImportant"):
            states.append("\uc911\uc694")
        row["badge"].configure(text=" \u00b7 ".join(states) if states else badge_text, fg_color="#eaf6fa" if not is_memo else "#fff1d8", text_color=accent)
        if row.get("panel"):
            row["panel"].place_forget()
        row["badge"].place(relx=1.0, x=-124, y=28)

    def ensure_virtual_row_pool(self):
        needed = self.virtual_visible_count()
        while len(self.virtual_row_widgets) < needed:
            row = self.create_virtual_row()
            self.virtual_row_widgets.append(row)

    def create_virtual_row(self):
        frame = ctk.CTkFrame(self.cards, fg_color="#ffffff", height=78, corner_radius=20, border_width=1, border_color=COL["line"])
        accent = ctk.CTkFrame(frame, fg_color="#8fb0bf", width=5, height=58, corner_radius=5)
        accent.place(x=15, y=10)
        title = ctk.CTkLabel(frame, text="", fg_color="transparent", text_color=COL["text"], anchor="w", font=(READ_FONT, 16, "bold"), height=24)
        title.place(x=38, y=13, relwidth=0.64)
        meta = ctk.CTkLabel(frame, text="", fg_color="transparent", text_color=COL["muted"], anchor="w", font=(READ_FONT, 10), height=19)
        meta.place(x=38, y=48, relwidth=0.64)
        badge = ctk.CTkLabel(frame, text="", fg_color="#eaf6fa", text_color=COL["primary"], font=(READ_FONT, 9, "bold"), corner_radius=12, width=92, height=22)
        badge.place(relx=1.0, x=-124, y=28)
        item = self.cards.create_window(0, 0, anchor="nw", window=frame, width=1, height=78)
        row = {"frame": frame, "accent": accent, "title": title, "meta": meta, "badge": badge, "item": item, "nid": None, "panel": None, "hover_job": None}

        def bind(w):
            widgets = [w]
            for attr in ("_canvas", "_label", "_text_label"):
                child = getattr(w, attr, None)
                if child is not None and child not in widgets:
                    widgets.append(child)
            for target in widgets:
                target.bind("<Enter>", lambda e, r=row: self.schedule_virtual_hover(r), add="+")
                target.bind("<Leave>", lambda e, r=row: self.schedule_virtual_close(r), add="+")
                target.bind("<ButtonPress-1>", lambda e, r=row: self.start_drag(r["nid"], e) if r["nid"] else None, add="+")
                target.bind("<ButtonRelease-1>", lambda e, r=row: self.finish_drag(e) if r["nid"] else None, add="+")
                target.bind("<Button-3>", lambda e, r=row: self.quick_done(r["nid"]) if r["nid"] else None, add="+")
        for w in (frame, title, meta, badge):
            bind(w)
        return row

    def schedule_virtual_hover(self, row):
        if not row["nid"] or self.drag_source:
            return
        if row["hover_job"] or (row.get("panel") and row["panel"].winfo_manager()):
            return
        row["hover_job"] = row["frame"].after(110, lambda r=row: self.open_virtual_panel(r))

    def schedule_virtual_close(self, row):
        if row["hover_job"]:
            try:
                row["frame"].after_cancel(row["hover_job"])
            except Exception:
                pass
            row["hover_job"] = None
        row["frame"].after(120, lambda r=row: self.close_virtual_panel(r))

    def open_virtual_panel(self, row):
        row["hover_job"] = None
        nid = row["nid"]
        n = self.store.node(nid)
        if not n:
            return
        if row.get("panel"):
            row["panel"].destroy()
            row["panel"] = None
        wrap = tk.Frame(row["frame"], bg="#ffffff", bd=0, highlightthickness=0)
        panel = ctk.CTkFrame(wrap, fg_color="#ffffff", corner_radius=14, border_width=1, border_color=COL["line"])
        panel.place(x=0, y=0, relwidth=1, relheight=1)
        row["panel"] = wrap
        def keep(_e=None): self.schedule_virtual_hover(row)
        def leave(_e=None): self.schedule_virtual_close(row)
        def button(text, command, row_idx, col, danger=False, disabled=False):
            b = ctk.CTkButton(panel, text=text, command=command, height=28, corner_radius=12, font=(READ_FONT, 10, "bold"), fg_color=COL["danger_soft"] if danger else "#eef8fc", hover_color="#ffe0dc" if danger else "#dff1f8", text_color=COL["danger"] if danger else COL["text"], border_width=1, border_color="#f0c4c4" if danger else COL["line"], state="disabled" if disabled else "normal")
            b.grid(row=row_idx, column=col, sticky="ew", padx=2, pady=(4 if row_idx == 0 else 1, 1 if row_idx == 0 else 4)); b.bind("<Enter>", keep, add="+"); b.bind("<Leave>", leave, add="+"); return b
        is_memo = n.get("kind") == "memo"; is_folder = n.get("isCustomFolder")
        button("\uc624\ub298", lambda x=nid: self.set_node_today(x, not bool((self.store.node(x) or {}).get("isToday"))), 0, 0, disabled=is_memo or is_folder)
        button("\uc911\uc694", lambda x=nid: self.set_selected_and_toggle_important(x), 0, 1, disabled=is_memo or is_folder)
        button("\uc644\ub8cc", lambda x=nid: self.quick_done(x), 0, 2, disabled=is_memo or is_folder)
        button("\uba54\ubaa8", lambda x=nid: self.focus_memo_node(x), 0, 3)
        button("\uc6b0\uc120\uc21c\uc704", lambda x=nid: self.prompt_node_priority(x), 1, 0, disabled=is_memo or is_folder)
        button("\uc218\uc815", lambda x=nid: self.rename_node(x), 1, 1)
        button("\ubcf5\uc0ac", lambda x=nid: self.copy_node_to_current(x), 1, 2)
        button("\uc0ad\uc81c", lambda x=nid: self.delete_node(x), 1, 3, danger=True)
        for i in range(4): panel.grid_columnconfigure(i, weight=1)
        row["frame"].configure(border_color=COL["primary"], border_width=2)
        row["badge"].place_forget()
        frame_width = max(1, row["frame"].winfo_width())
        panel_width = max(330, min(460, frame_width - 28))
        wrap.configure(width=panel_width, height=70)
        wrap.place(relx=1.0, x=-12, y=4, anchor="ne", width=panel_width, height=70)
        wrap.lift(); panel.lift()
        wrap.bind("<Enter>", keep, add="+"); wrap.bind("<Leave>", leave, add="+"); panel.bind("<Enter>", keep, add="+"); panel.bind("<Leave>", leave, add="+")

    def close_virtual_panel(self, row):
        f = row["frame"]
        px, py = f.winfo_pointerx(), f.winfo_pointery()
        x1, y1 = f.winfo_rootx(), f.winfo_rooty()
        x2, y2 = x1 + f.winfo_width(), y1 + f.winfo_height()
        if x1 <= px <= x2 and y1 <= py <= y2:
            return
        if row.get("panel"):
            row["panel"].place_forget()
        row["frame"].configure(height=78, border_color=COL["line"], border_width=1)
        self.cards.itemconfigure(row["item"], height=78)
        row["badge"].place(relx=1.0, x=-124, y=28)

    def virtual_total_height(self):
        return len(getattr(self, "virtual_ids", [])) * VROW_HEIGHT

    def virtual_visible_count(self):
        height = max(1, self.cards.winfo_height()) if hasattr(self, "cards") else 1
        return max(1, min(len(getattr(self, "virtual_ids", [])) or 1, height // VROW_HEIGHT + VROW_BUFFER))

    def sync_virtual_scrollbar(self):
        total_h = max(1, self.virtual_total_height())
        view_h = max(1, self.cards.winfo_height())
        if total_h <= view_h:
            self.cards_scroll.set(0, 1)
            return
        first = max(0, min(1, self.virtual_scroll_y / total_h))
        last = max(first, min(1, (self.virtual_scroll_y + view_h) / total_h))
        self.cards_scroll.set(first, last)

    def virtual_yview(self, *args):
        total_h = self.virtual_total_height()
        view_h = max(1, self.cards.winfo_height())
        max_y = max(0, total_h - view_h)
        if not args:
            return
        if args[0] == "moveto" and len(args) > 1:
            self.virtual_scroll_y = int(float(args[1]) * max_y)
        elif args[0] == "scroll" and len(args) > 2:
            amount = int(args[1])
            unit = args[2]
            step = VROW_HEIGHT * 5 if unit == "units" else int(view_h * 0.9)
            self.virtual_scroll_y += amount * step
        self.virtual_scroll_y = max(0, min(max_y, self.virtual_scroll_y))
        self.render_virtual_rows()

    def virtual_mousewheel(self, event):
        if self.view_mode == "activity":
            self.cards.yview_scroll(int(-event.delta / 120 * SCROLL_UNITS), "units")
            return "break"
        total_h = self.virtual_total_height()
        view_h = max(1, self.cards.winfo_height())
        max_y = max(0, total_h - view_h)
        steps = -1 if event.delta > 0 else 1
        if abs(event.delta) >= 120:
            steps = int(-event.delta / 120)
        self.virtual_scroll_y = max(0, min(max_y, self.virtual_scroll_y + steps * VROW_HEIGHT * 5))
        self.render_virtual_rows()
        return "break"

    def render_more_card(self, shown, total):
        box = ctk.CTkFrame(self.cards, fg_color=COL["panel"], corner_radius=18, border_width=1, border_color=COL["line"])
        box.grid(row=shown, column=0, sticky="ew", padx=8, pady=8)
        box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(box, text=f"{shown}/{total}개 표시 중", font=(READ_FONT, 12, "bold"), text_color=COL["muted"]).grid(row=0, column=0, sticky="w", padx=18, pady=14)
        self.make_btn(box, "더 보기", self.load_more_cards, COL["primary"], height=34).grid(row=0, column=1, sticky="e", padx=18, pady=10)

    def load_more_cards(self):
        self.card_render_limit += CARD_RENDER_BATCH
        self.refresh_cards()

    def render_light_card(self, parent, nid, row):
        n = self.store.node(nid)
        is_memo = n.get("kind") == "memo"
        is_done = n.get("completed")
        bg = COL["memo"] if is_memo else COL["done"] if is_done else "#ffffff"
        accent = "#d69a33" if is_memo else "#65ad74" if is_done else "#8fb0bf"
        if n.get("isToday"): accent = COL["primary"]
        if n.get("isImportant"): accent = COL["accent"]
        card = tk.Frame(parent, bg=bg, height=56, highlightthickness=1, highlightbackground=COL["line"], bd=0)
        card.node_id = nid
        card.grid(row=row, column=0, sticky="ew", padx=8, pady=3)
        card.grid_propagate(False)
        self.drop_targets[card] = nid
        tk.Frame(card, bg=accent, width=4, height=42).place(x=12, y=7)
        title = ("완료  " if is_done else "") + n.get("title", "이름 없음")
        title_label = tk.Label(card, text=title, bg=bg, fg=COL["text"], anchor="w", font=(READ_FONT, 12, "bold"))
        title_label.place(x=28, y=8, relwidth=0.66, height=20)
        child_count = len(self.store.children(nid))
        meta = ["\uba54\ubaa8" if n.get("kind") == "memo" else "\ud560 \uc77c"]
        meta.append("\uc6b0\uc120 \uc5c6\uc74c" if n.get("priority") is None else f"\uc6b0\uc120 {n.get('priority')}")
        if child_count:
            meta.append(f"\ud558\uc704 {child_count}")
        meta.append(human_time(n.get("createdAt")))
        meta_label = tk.Label(card, text=" · ".join(meta), bg=bg, fg=COL["muted"], anchor="w", font=(READ_FONT, 9))
        meta_label.place(x=28, y=30, relwidth=0.66, height=18)
        state = []
        if n.get("isToday"): state.append("오늘")
        if n.get("isImportant"): state.append("중요")
        badge = tk.Label(card, text=" · ".join(state) or ("메모" if is_memo else "작업"), bg="#eaf6fa", fg=COL["primary"], font=(READ_FONT, 9, "bold"), padx=10)
        badge.place(relx=1.0, x=-120, y=17, width=92, height=22)
        hover_job = {"id": None}
        panel = {"w": None}
        def open_panel(_e=None):
            hover_job["id"] = None
            if panel["w"] is None:
                p = tk.Frame(card, bg="#ffffff", highlightthickness=1, highlightbackground=COL["line"])
                panel["w"] = p
                specs = [
                    ("위쪽", lambda: self.move_node_to_parent(nid)),
                    ("★" if n.get("isImportant") else "☆", lambda: self.set_selected_and_toggle_important(nid)),
                    ("메모화" if not is_memo else "할 일화", lambda: self.toggle_kind_node(nid)),
                    ("다음 행동", lambda: self.mark_next_action(nid)),
                    ("메모", lambda: self.focus_memo_node(nid)),
                    ("복사", lambda: self.copy_node_to_current(nid)),
                    ("수정", lambda: self.rename_node(nid)),
                    ("완료", lambda: self.quick_done(nid)),
                    ("삭제", lambda: self.delete_node(nid)),
                ]
                for i, (text, cmd) in enumerate(specs):
                    tk.Button(p, text=text, command=cmd, font=(READ_FONT, 8), relief="flat", bg="#f4f8fb", fg=COL["danger"] if text == "삭제" else COL["text"]).grid(row=0, column=i, padx=1, pady=2)
                pr = tk.Entry(p, font=(READ_FONT, 8), width=7, relief="solid", bd=1)
                pr.insert(0, "" if n.get("priority") is None else str(n.get("priority")))
                pr.grid(row=1, column=0, columnspan=2, sticky="w", padx=2, pady=2)
                pr.bind("<Return>", lambda e: self.set_node_priority(nid, pr.get()), add="+")
                today = tk.BooleanVar(value=bool(n.get("isToday")))
                tk.Checkbutton(p, text="오늘할일", variable=today, command=lambda: self.set_node_today(nid, today.get()), bg="#ffffff", font=(READ_FONT, 8)).grid(row=1, column=2, columnspan=2, sticky="w")
                tk.Button(p, text="목록에서 제거", command=lambda: self.remove_node_from_current_list(nid), font=(READ_FONT, 8), relief="flat", bg="#f4f8fb").grid(row=1, column=4, columnspan=2, sticky="w", padx=2)
                for child in p.winfo_children():
                    child.bind("<Enter>", open_panel, add="+")
                    child.bind("<Leave>", schedule_close, add="+")
            card.configure(height=104)
            badge.place_forget()
            panel["w"].place(x=28, y=52, relwidth=0.94, height=58)
            card.configure(highlightbackground=COL["primary"])
        def schedule_open(_e=None):
            if hover_job["id"] or (panel["w"] and panel["w"].winfo_manager()):
                return
            hover_job["id"] = card.after(170, open_panel)
        def close_panel(_e=None):
            px, py = card.winfo_pointerx(), card.winfo_pointery()
            x1, y1 = card.winfo_rootx(), card.winfo_rooty()
            x2, y2 = x1 + card.winfo_width(), y1 + card.winfo_height()
            if x1 <= px <= x2 and y1 <= py <= y2:
                return
            if panel["w"]: panel["w"].place_forget()
            card.configure(height=56, highlightbackground="#d7e3ec")
            badge.place(relx=1.0, x=-120, y=17, width=92, height=22)
        def schedule_close(_e=None):
            if hover_job["id"]:
                try: card.after_cancel(hover_job["id"])
                except Exception: pass
                hover_job["id"] = None
            card.after(90, close_panel)
        def bind_row(w):
            w.bind("<Enter>", schedule_open, add="+")
            w.bind("<Leave>", schedule_close, add="+")
            w.bind("<ButtonPress-1>", lambda e,x=nid:self.start_drag(x), add="+")
            w.bind("<ButtonRelease-1>", lambda e,x=nid:self.release_card(e,x), add="+")
            w.bind("<Button-3>", lambda e,x=nid:self.quick_done(x), add="+")
        for w in (card, title_label, meta_label, badge):
            bind_row(w)

    def render_empty_state(self):
        self.cards.delete("empty")
        width = max(1, self.cards.winfo_width())
        self.cards.create_text(width//2, 80, text="\uc544\uc9c1 \ud45c\uc2dc\ud560 \uc791\uc5c5\uc774 \uc5c6\uc2b5\ub2c8\ub2e4", fill=COL["text"], font=(FONT, 18, "bold"), tags=("empty",))
        self.cards.create_text(width//2, 112, text="\uc704 \uc785\ub825\ucc3d\uc5d0\uc11c \ud070 \uc791\uc5c5\uc744 \ud558\ub098 \ub9cc\ub4e4\uace0, \ub354\ube14\ud074\ub9ad\ud574\uc11c \ud558\uc704 \uc791\uc5c5\uc73c\ub85c \ucabc\uac1c\ubcf4\uc138\uc694.", fill=COL["muted"], font=BODY_FONT, tags=("empty",))

    def render_matrix(self):
        groups={"최우선 실행":[],"중요한 계획":[],"빠른 처리":[],"나중에 검토":[]}
        for n in self.store.all_nodes():
            if not self.row_visible(n) or n.get("completed"): continue
            if n.get("isToday") and n.get("isImportant"): groups["최우선 실행"].append(n["id"])
            elif n.get("isImportant"): groups["중요한 계획"].append(n["id"])
            elif n.get("isToday"): groups["빠른 처리"].append(n["id"])
            else: groups["나중에 검토"].append(n["id"])
        self.summary.configure(text=f"우선순위 맵 {sum(len(v) for v in groups.values())}개")
        colors=[COL["matrix_a"], COL["matrix_b"], COL["matrix_c"], COL["matrix_d"]]
        for i,(title,ids) in enumerate(groups.items()):
            sec=ctk.CTkFrame(self.cards,fg_color=colors[i],corner_radius=20,border_width=1,border_color=COL["line"]); sec.grid(row=i//2,column=i%2,sticky="nsew",padx=8,pady=8); self.cards.grid_columnconfigure(i%2,weight=1)
            ctk.CTkLabel(sec,text=f"{title}  {len(ids)}",font=(FONT,16,"bold"),text_color=COL["text"],anchor="w").grid(row=0,column=0,sticky="ew",padx=14,pady=(14,6)); sec.grid_columnconfigure(0,weight=1)
            for r,nid in enumerate(sorted(ids,key=self.store.sort_key)[:30],start=1): self.render_card(sec,nid,r,compact=True)

    def render_card(self,parent,nid,row,compact=False):
        n=self.store.node(nid)
        is_memo = n.get("kind") == "memo"
        is_folder = n.get("isCustomFolder")
        is_done = n.get("completed")
        is_today = n.get("isToday")
        is_important = n.get("isImportant")
        bg = "#ffffff"
        if is_folder: bg = COL["folder"]
        elif is_memo: bg = COL["memo"]
        elif is_done: bg = COL["done"]
        elif is_today and is_important: bg = "#fff4e8"
        elif is_today: bg = COL["today"]
        elif is_important: bg = COL["important"]
        border = COL["line"]
        accent_color = "#8fb0bf"
        if is_folder: accent_color = "#6f9fca"; border = "#c9e2ef"
        elif is_memo: accent_color = "#d69a33"; border = "#efdcae"
        elif is_done: accent_color = "#65ad74"; border = "#cfebd5"
        elif is_today and is_important: accent_color = "#d98944"; border = "#eccda6"
        elif is_today: accent_color = COL["primary"]; border = "#c6e6ee"
        elif is_important: accent_color = COL["accent"]; border = "#ead9ad"
        card_height = 76 if not compact else 62
        hover_height = 128 if not compact else 112
        card=ctk.CTkFrame(parent,fg_color=bg,height=card_height,corner_radius=14,border_width=1,border_color=border)
        card.node_id = nid
        card.grid(row=row,column=0,sticky="ew",padx=6,pady=5)
        card.grid_propagate(False)
        self.drop_targets[card]=nid
        accent = ctk.CTkFrame(card, fg_color=accent_color, width=5, height=card_height-18, corner_radius=10)
        accent.place(x=12, y=9)
        title_prefix = "완료  " if is_done else ""
        title = title_prefix + n.get("title","이름 없음")
        lab=ctk.CTkLabel(card,text=title,font=(READ_FONT,15 if not compact else 13,"bold"),text_color=COL["text"],anchor="w",height=24)
        lab.place(x=30, y=11)
        meta=[]
        meta.append("\uc6b0\uc120 \uc5c6\uc74c" if n.get("priority") is None else f"\uc6b0\uc120 {n.get('priority')}")
        child_count = len(self.store.children(nid))
        if child_count:
            meta.append(f"\ud558\uc704 {child_count}")
        meta.append(human_time(n.get("createdAt")))
        meta_label = ctk.CTkLabel(card,text=" · ".join([x for x in meta if x]),font=(READ_FONT, 10),text_color=COL["muted"],anchor="w",height=18)
        meta_label.place(x=30, y=40 if not compact else 36)
        badge = ctk.CTkFrame(card, fg_color="transparent", width=210, height=34)
        badge.place(x=880, y=(card_height-34)//2)
        badge.grid_columnconfigure((0,1,2), weight=0)
        kind_text="프로젝트" if is_folder else "메모" if is_memo else "작업"
        self.pill(badge, kind_text, accent_color).grid(row=0, column=0, sticky="e", padx=(0,4))
        if is_today: self.pill(badge, "오늘", COL["primary"]).grid(row=0, column=1, sticky="e", padx=4)
        if is_important: self.pill(badge, "중요", COL["accent"]).grid(row=0, column=2, sticky="e", padx=4)
        action_widgets = []
        action_ref = {"frame": None}
        def ensure_actions():
            if action_ref["frame"] is not None:
                return action_ref["frame"]
            actions = ctk.CTkFrame(card, fg_color="#ffffff", width=690, height=66, corner_radius=12, border_width=1, border_color=COL["line"])
            action_ref["frame"] = actions
            def card_btn(text, command, width=58, danger=False, disabled=False):
                btn = ctk.CTkButton(
                    actions, text=text, command=command, width=width, height=26, corner_radius=10,
                    font=(READ_FONT, 10), fg_color=COL["danger_soft"] if danger else "#f4f8fb",
                    hover_color="#ffe1dc" if danger else "#e3f1f7",
                    text_color=COL["danger"] if danger else COL["text"],
                    border_width=1, border_color="#f1c7cc" if danger else COL["line"],
                    state="disabled" if disabled else "normal"
                )
                action_widgets.append(btn)
                return btn
            move_btn = card_btn("위쪽", lambda x=nid: self.move_node_to_parent(x), 52, disabled=(n.get("parentId") == ROOT_ID))
            star_btn = card_btn("★" if is_important else "☆", lambda x=nid: self.set_selected_and_toggle_important(x), 38, disabled=is_memo)
            kind_btn = card_btn("할 일화" if is_memo else "메모화", lambda x=nid: self.toggle_kind_node(x), 62)
            next_btn = card_btn("다음 행동", lambda x=nid: self.mark_next_action(x), 70)
            memo_btn = card_btn("메모", lambda x=nid: self.focus_memo_node(x), 52)
            copy_btn = card_btn("복사", lambda x=nid: self.copy_node_to_current(x), 52)
            rename_btn = card_btn("수정", lambda x=nid: self.rename_node(x), 52)
            done_btn = card_btn("완료", lambda x=nid: self.quick_done(x), 52, disabled=is_memo or is_folder)
            del_btn = card_btn("삭제", lambda x=nid: self.delete_node(x), 52, danger=True)
            priority_entry = ctk.CTkEntry(actions, placeholder_text="우선순위", width=76, height=26, font=(READ_FONT, 10), fg_color="#f8fbfd", border_color=COL["line"])
            priority_entry.insert(0, "" if n.get("priority") is None else str(n.get("priority")))
            if is_memo:
                priority_entry.configure(state="disabled")
            priority_entry.bind("<Return>", lambda e,x=nid,w=priority_entry: self.set_node_priority(x, w.get()), add="+")
            priority_entry.bind("<FocusOut>", lambda e,x=nid,w=priority_entry: self.set_node_priority(x, w.get(), silent=True), add="+")
            today_var = ctk.BooleanVar(value=bool(is_today))
            today_check = ctk.CTkCheckBox(actions, text="오늘할일", variable=today_var, command=lambda x=nid,v=today_var: self.set_node_today(x, v.get()), width=84, height=24, font=(READ_FONT, 10), text_color=COL["text"], checkbox_width=16, checkbox_height=16, border_color=COL["line"])
            if is_memo:
                today_check.configure(state="disabled")
            remove_btn = card_btn("목록에서 제거", lambda x=nid: self.remove_node_from_current_list(x), 90, disabled=(self.view_mode != "pathList" or not self.current_list_id))
            first_row = [move_btn, star_btn, kind_btn, next_btn, memo_btn, copy_btn, rename_btn, done_btn, del_btn]
            for col, widget in enumerate(first_row):
                widget.grid(row=0, column=col, padx=(6 if col == 0 else 2, 2), pady=(5, 2))
            priority_entry.grid(row=1, column=0, columnspan=2, sticky="w", padx=(6, 2), pady=(0, 5))
            today_check.grid(row=1, column=2, columnspan=2, sticky="w", padx=2, pady=(0, 5))
            remove_btn.grid(row=1, column=4, columnspan=2, sticky="w", padx=2, pady=(0, 5))
            action_widgets.extend([priority_entry, today_check])
            for w in (actions, *action_widgets):
                bind_deep(w, "<Enter>", schedule_show)
                bind_deep(w, "<Leave>", schedule_hide)
            return actions
        def _old_card_btn_unused(text, command, width=58, danger=False, disabled=False):
            btn = ctk.CTkButton(
                card, text=text, command=command, width=width, height=26, corner_radius=10,
                font=(READ_FONT, 10), fg_color=COL["danger_soft"] if danger else "#f4f8fb",
                hover_color="#ffdfe2" if danger else "#e3edf4",
                text_color=COL["danger"] if danger else COL["text"],
                border_width=1, border_color="#f1c7cc" if danger else COL["line"],
                state="disabled" if disabled else "normal"
            )
            action_widgets.append(btn)
            return btn
        hover_job = {"id": None}
        hide_job = {"id": None}
        layout_job = {"id": None}
        def layout_card(_e=None):
            width = max(card.winfo_width(), 360)
            actions = action_ref["frame"]
            action_width = max(330, width - 64)
            if actions:
                actions.configure(width=action_width)
            reserve = 36 if actions and actions.winfo_manager() else 250
            lab.configure(width=max(160, width - reserve - 42))
            meta_label.configure(width=max(160, width - reserve - 42))
            if actions and actions.winfo_manager():
                card.configure(height=hover_height)
                accent.configure(height=hover_height-18)
                actions.place(x=30, y=56 if not compact else 48)
            else:
                card.configure(height=card_height)
                accent.configure(height=card_height-18)
                badge.place(x=max(38, width - 230), y=(card_height-34)//2)
        def show_actions(_e=None):
            hover_job["id"] = None
            if hide_job["id"]:
                try: card.after_cancel(hide_job["id"])
                except Exception: pass
                hide_job["id"] = None
            actions = ensure_actions()
            card.configure(border_color=COL["primary"])
            badge.place_forget()
            width = max(card.winfo_width(), 360)
            action_width = max(330, width - 64)
            actions.configure(width=action_width)
            card.configure(height=hover_height)
            accent.configure(height=hover_height-18)
            actions.place(x=30, y=56 if not compact else 48)
            actions.lift()
            layout_card()
        def hide_actions(_e=None):
            hide_job["id"] = None
            px, py = card.winfo_pointerx(), card.winfo_pointery()
            x1, y1 = card.winfo_rootx(), card.winfo_rooty()
            x2, y2 = x1 + card.winfo_width(), y1 + card.winfo_height()
            if not (x1 <= px <= x2 and y1 <= py <= y2):
                actions = action_ref["frame"]
                if actions:
                    actions.place_forget()
                card.configure(border_color=border)
                layout_card()
        def schedule_show(_e=None):
            if hide_job["id"]:
                try: card.after_cancel(hide_job["id"])
                except Exception: pass
                hide_job["id"] = None
            actions = action_ref["frame"]
            if hover_job["id"] or (actions and actions.winfo_manager()):
                return
            hover_job["id"] = card.after(170, show_actions)
        def schedule_hide(_e=None):
            if hover_job["id"]:
                try: card.after_cancel(hover_job["id"])
                except Exception: pass
                hover_job["id"] = None
            if hide_job["id"]:
                try: card.after_cancel(hide_job["id"])
                except Exception: pass
            hide_job["id"] = card.after(90, hide_actions)
        def schedule_layout(_e=None):
            if layout_job["id"]:
                try: card.after_cancel(layout_job["id"])
                except Exception: pass
            layout_job["id"] = card.after(50, lambda: (layout_job.update({"id": None}), layout_card()))
        def bind_deep(widget, sequence, callback):
            for target in (widget, getattr(widget, "_canvas", None), getattr(widget, "_text_label", None)):
                if target:
                    target.bind(sequence, callback, add="+")
        for w in (card, lab, meta_label, badge):
            bind_deep(w, "<Enter>", schedule_show)
            bind_deep(w, "<Leave>", schedule_hide)
        for w in (card, lab, meta_label, badge):
            bind_deep(w, "<Double-Button-1>", lambda e,x=nid:self.open_node(x))
            bind_deep(w, "<Button-3>", lambda e,x=nid:self.quick_done(x))
            bind_deep(w, "<ButtonPress-1>", lambda e,x=nid:self.start_drag(x))
            bind_deep(w, "<ButtonRelease-1>", lambda e,x=nid:self.release_card(e,x))
        card.bind("<Configure>", schedule_layout, add="+")
        card.after(1, layout_card)

    def select_node(self,nid):
        self.selected_id=nid
        if self.view_mode not in ("activity", "matrix") and not self.right_panel_open:
            self.right_panel_open = True
            self.store.state.setdefault("ui", {})["rightPanelOpen"] = True
            self.store.save()
            self.apply_context_layout()
        self.refresh_detail()
    def selected(self,warn=True):
        n=self.store.node(self.selected_id) if self.selected_id else None
        if warn and not n: messagebox.showinfo(APP_TITLE,"작업을 선택하세요.")
        return n
    def open_node(self,nid):
        if self.store.node(nid):
            self.current_parent=nid; self.current_list_id=None; self.current_date=None; self.current_date_mode=None; self.view_mode="all"; self.selected_id=nid
            self.right_panel_open = True
            self.right_section_open["memo"] = True
            if hasattr(self, "detail"):
                self.detail.grid(row=0, column=2, sticky="nsew", padx=(0, 10), pady=10)
            if hasattr(self, "memo_body"):
                self.memo_body.grid()
            if hasattr(self, "memo_detail_header"):
                self.memo_detail_header.configure(text="접기  선택 작업 메모")
            self.refresh_workspace()
    def open_selected(self):
        n=self.selected();
        if n: self.open_node(n["id"])
    def collapsible_detail_section(self, title, key, row, height=180):
        header = ctk.CTkButton(self.detail, text=("v  " if self.right_section_open.get(key, True) else ">  ") + title, command=lambda k=key: self.toggle_detail_section(k), fg_color="transparent", hover_color=COL["hero_soft"], text_color=COL["text"], anchor="w", height=32, corner_radius=12, font=SECTION_FONT)
        header.grid(row=row, column=0, sticky="ew", padx=16, pady=(8, 0))
        setattr(self, f"{key}_detail_header", header)
        body = ctk.CTkFrame(self.detail, fg_color="transparent", height=height)
        body.grid(row=row+1, column=0, sticky="nsew", padx=14, pady=(6, 8))
        body.grid_propagate(False); body.grid_columnconfigure(0, weight=1)
        if not self.right_section_open.get(key, True): body.grid_remove()
        return body

    def toggle_detail_section(self, key):
        self.right_section_open[key] = not self.right_section_open.get(key, True)
        self.store.state.setdefault("ui", {})["rightSectionOpen"] = dict(self.right_section_open)
        self.store.save()
        body = {"views": getattr(self, "view_body", None), "dates": getattr(self, "date_body", None), "memo": getattr(self, "memo_body", None)}.get(key)
        header = getattr(self, f"{key}_detail_header", None)
        titles = {"views": "\ube60\ub978 \ubcf4\uae30", "dates": "\ub0a0\uc9dc\ubcc4 \ubcf4\uae30", "activity": "\ud65c\ub3d9 \uae30\ub85d", "memo": "\uc120\ud0dd \uc791\uc5c5 \uba54\ubaa8"}
        if header:
            header.configure(text=("v  " if self.right_section_open[key] else ">  ") + titles.get(key, key))
        if body:
            body.grid() if self.right_section_open[key] else body.grid_remove()

    def refresh_detail(self):
        n = self.store.node(self.selected_id) if self.selected_id else None
        self.memo.delete("1.0", "end")
        if not n:
            self.detail_title.configure(text="\uc120\ud0dd \uc5c6\uc74c")
            self.detail_meta.configure(text="\uc67c\ucabd \ubaa9\ub85d\uc5d0\uc11c \uc791\uc5c5\uc744 \uc120\ud0dd\ud558\uba74 \uc0c1\ud0dc, \uc791\uc131\uc77c, \uba54\ubaa8\ub97c \ud655\uc778\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.")
            return
        self.detail_title.configure(text=n.get("title", "\uc774\ub984 \uc5c6\uc74c"))
        meta = ["\ud3f4\ub354" if n.get("isCustomFolder") else "\uba54\ubaa8" if n.get("kind") == "memo" else "\ud560 \uc77c", f"\ud558\uc704 {len(self.store.children(n['id']))}"]
        meta.append("\uc6b0\uc120 \uc5c6\uc74c" if n.get("priority") is None else f"\uc6b0\uc120 {n.get('priority')}")
        if n.get("isToday"): meta.append("\uc624\ub298")
        if n.get("isImportant"): meta.append("\uc911\uc694")
        if n.get("completed"): meta.append("\uc644\ub8cc")
        meta.append(f"\uc791\uc131 {human_time(n.get('createdAt'))}")
        if n.get("completedAt"): meta.append(f"\uc644\ub8cc {human_time(n.get('completedAt'))}")
        self.detail_meta.configure(text=" \u00b7 ".join(meta))
        self.memo.insert("1.0", n.get("memo", ""))

    def add_task(self):
        title = self.title_entry.get().strip()
        if not title:
            return
        self.store.add_node(self.current_parent, title, "memo" if self.kind_var.get() == "\uba54\ubaa8" else "task", parse_priority(self.priority.get()), self.today_var.get())
        self.title_entry.delete(0, "end")
        self.priority.delete(0, "end")
        self.today_var.set(False)
        self.save_refresh()

    def go_root(self): self.current_parent=ROOT_ID; self.current_list_id=None; self.current_date=None; self.current_date_mode=None; self.view_mode="all"; self.selected_id=None; self.refresh_workspace()
    def rename_selected(self):
        n=self.selected();
        if n:
            title=simpledialog.askstring(APP_TITLE,"수정",initialvalue=n.get("title",""))
            if title: n["title"]=title.strip() or "이름 없음"; [x.update({"title":n["title"]}) for x in self.store.custom_tabs if x.get("id")==n["id"]]; self.save_refresh()
    def delete_selected(self):
        n=self.selected();
        if n and messagebox.askyesno(APP_TITLE,f"'{n.get('title')}'와 하위를 삭제할까요?"): self.store.delete_subtree(n["id"]); self.selected_id=None; self.save_refresh()
    def copy_selected(self):
        n=self.selected();
        if n: self.selected_id=self.store.clone_subtree(n["id"],self.current_parent); self.save_refresh()
    def quick_done(self,nid): self.selected_id=nid; self.toggle_done()
    def set_selected_and_toggle_today(self,nid): self.selected_id=nid; self.toggle_today()
    def set_selected_and_toggle_important(self,nid): self.selected_id=nid; self.toggle_important()
    def rename_node(self,nid):
        n=self.store.node(nid)
        if not n: return
        title=simpledialog.askstring(APP_TITLE,"수정",initialvalue=n.get("title",""))
        if title is None: return
        n["title"]=title.strip() or "이름 없음"
        for x in self.store.custom_tabs:
            if x.get("id")==n["id"]: x["title"]=n["title"]
        self.selected_id=nid; self.save_refresh()
    def delete_node(self,nid):
        n=self.store.node(nid)
        if n and messagebox.askyesno(APP_TITLE,f"'{n.get('title')}'와 하위를 삭제할까요?"):
            self.store.delete_subtree(nid); self.selected_id=None; self.save_refresh()
    def copy_node_to_current(self,nid):
        if self.store.node(nid):
            self.selected_id=self.store.clone_subtree(nid,self.current_parent); self.save_refresh()
    def move_node_to_parent(self,nid):
        n=self.store.node(nid); parent=self.store.node(n.get("parentId")) if n else None; grand=self.store.node(parent.get("parentId")) if parent else None
        if n and grand and self.store.move_node(nid,grand["id"]):
            self.selected_id=nid; self.save_refresh()
    def toggle_kind_node(self,nid):
        n=self.store.node(nid)
        if n and not n.get("isCustomFolder"):
            self.store.set_kind(nid,"task" if n.get("kind")=="memo" else "memo",False); self.selected_id=nid; self.save_refresh()
    def mark_next_action(self,nid):
        n=self.store.node(nid)
        if n and not n.get("isCustomFolder"):
            n["kind"]="task"; n["completed"]=False; n["completedAt"]=None; n["isToday"]=True; self.selected_id=nid; self.save_refresh()
    def focus_memo_node(self,nid):
        if self.store.node(nid):
            self.selected_id=nid; self.refresh_detail()
    def set_node_priority(self,nid,value,silent=False):
        n=self.store.node(nid)
        if not n or n.get("kind")=="memo" or n.get("isCustomFolder"): return
        parsed=parse_priority(value)
        if str(value or "").strip() and parsed is None:
            if not silent: messagebox.showwarning(APP_TITLE,"우선순위는 숫자로 입력하세요.")
            return
        if n.get("priority") != parsed:
            n["priority"]=parsed; self.selected_id=nid; self.save_refresh()
    def prompt_node_priority(self,nid):
        n=self.store.node(nid)
        if not n or n.get("kind")=="memo" or n.get("isCustomFolder"): return
        current="" if n.get("priority") is None else str(n.get("priority"))
        value=simpledialog.askstring(APP_TITLE,"우선순위 숫자를 입력하세요. 비우면 우선순위 없음입니다.",initialvalue=current)
        if value is None: return
        self.set_node_priority(nid,value)
    def set_node_today(self,nid,value):
        n=self.store.node(nid)
        if n and n.get("kind")!="memo" and not n.get("isCustomFolder"):
            n["isToday"]=bool(value); self.selected_id=nid; self.save_refresh()
    def remove_node_from_current_list(self,nid):
        item=self.store.path_list(self.current_list_id) if self.current_list_id else None
        if item:
            item["taskIds"]=[x for x in item.get("taskIds",[]) if x!=nid]
            self.selected_id=None; self.save_refresh()
    def toggle_done(self):
        n=self.selected();
        if n and n.get("kind")!="memo" and not n.get("isCustomFolder"): n["completed"]=not n.get("completed"); n["completedAt"]=now_iso() if n["completed"] else None; self.save_refresh()
    def toggle_today(self):
        n=self.selected();
        if n and n.get("kind")!="memo" and not n.get("isCustomFolder"): n["isToday"]=not n.get("isToday"); self.save_refresh()
    def toggle_important(self):
        n=self.selected();
        if n and n.get("kind")!="memo" and not n.get("isCustomFolder"): n["isImportant"]=not n.get("isImportant"); self.save_refresh()
    def memoize_selected(self):
        n=self.selected();
        if n: self.store.set_kind(n["id"],"memo",True); self.save_refresh()
    def taskify_selected(self):
        n=self.selected();
        if n: self.store.set_kind(n["id"],"task",False); self.save_refresh()
    def next_action(self):
        n=self.selected();
        if n and not n.get("isCustomFolder"): n["kind"]="task"; n["completed"]=False; n["completedAt"]=None; n["isToday"]=True; self.save_refresh()
    def move_to_parent(self):
        n=self.selected(); parent=self.store.node(n.get("parentId")) if n else None; grand=self.store.node(parent.get("parentId")) if parent else None
        if n and grand and self.store.move_node(n["id"],grand["id"]): self.save_refresh()
    def save_memo(self):
        n=self.selected();
        if n: n["memo"]=self.memo.get("1.0","end").rstrip("\n"); self.save_refresh()
    def memoize_current(self):
        if self.current_parent==ROOT_ID: messagebox.showwarning(APP_TITLE,"루트 전체 메모화는 막았습니다."); return
        n=self.store.node(self.current_parent)
        if n and messagebox.askyesno(APP_TITLE,f"'{n.get('title')}'와 하위를 전부 메모화할까요?"): self.store.set_kind(self.current_parent,"memo",True); self.save_refresh()
    def toggle_paste(self):
        if self.paste_open: self.paste.grid_forget(); self.paste_open=False
        else: self.paste.grid(row=4,column=0,sticky="ew",pady=(0,8)); self.paste_open=True
    def add_pasted_tree(self):
        parsed = parse_tree_text_detailed(self.paste_text.get("1.0", "end"))
        rows = parsed["rows"]
        if not rows:
            messagebox.showinfo(APP_TITLE, "\uAC00\uC838\uC62C \uD56D\uBAA9\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.")
            return
        if parsed["errors"]:
            messagebox.showerror(APP_TITLE, "\uBD99\uC5EC\uB123\uAE30 \uC624\uB958\uAC00 \uC788\uC5B4 \uCD94\uAC00\uD558\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uC6D0\uBB38\uC740 \uC720\uC9C0\uB429\uB2C8\uB2E4.\n\n" + "\n".join(parsed["errors"][:8]))
            return
        if parsed["warnings"]:
            msg = "\uACBD\uACE0\uAC00 \uC788\uC9C0\uB9CC \uC790\uB3D9 \uBCF4\uC815\uD574\uC11C \uCD94\uAC00\uD560\uAE4C\uC694?\n\n" + "\n".join(parsed["warnings"][:8])
            if not messagebox.askyesno(APP_TITLE, msg):
                return
        parents = {}
        for item in rows:
            d = max(0, item["depth"])
            pid = parents.get(d - 1, self.current_parent)
            nid = self.store.add_node(pid, item["title"], item.get("kind", "task"), item.get("priority"), item.get("isToday"))
            n = self.store.node(nid)
            if n:
                n["memo"] = item.get("memo", "")
                if n.get("kind") != "memo":
                    n["isImportant"] = bool(item.get("isImportant"))
                    if item.get("completed"):
                        n["completed"] = True
                        n["completedAt"] = now_iso()
            parents[d] = nid
            for key in list(parents):
                if key > d:
                    parents.pop(key, None)
        self.paste_text.delete("1.0", "end")
        self.save_refresh()
    def create_list(self):
        title=self.list_name.get().strip()
        if title: self.store.add_path_list(title); self.save_refresh()
    def open_list(self,lid): self.card_render_limit=CARD_RENDER_BATCH; self.current_list_id=lid; self.current_date=None; self.current_date_mode=None; self.view_mode="pathList"; self.selected_id=None; self.refresh_workspace()
    def delete_list(self):
        if not self.current_list_id: messagebox.showinfo(APP_TITLE,"삭제할 목록을 먼저 여세요."); return
        if messagebox.askyesno(APP_TITLE,"현재 목록을 삭제할까요? 실제 작업은 삭제되지 않습니다."):
            self.store.state["pathLists"]=[x for x in self.store.path_lists if x.get("id")!=self.current_list_id]; self.current_list_id=None; self.view_mode="all"; self.save_refresh()
    def add_to_list(self):
        n=self.selected();
        if not n: return
        if not self.store.path_lists: messagebox.showinfo(APP_TITLE,"먼저 왼쪽에서 목록을 만드세요."); return
        item=self.store.path_lists[0] if not self.current_list_id else self.store.path_list(self.current_list_id)
        if item and n["id"] not in item.setdefault("taskIds",[]): item["taskIds"].append(n["id"]); self.save_refresh()
    def remove_from_list(self):
        n=self.selected(); item=self.store.path_list(self.current_list_id) if self.current_list_id else None
        if n and item: item["taskIds"]=[x for x in item.get("taskIds",[]) if x!=n["id"]]; self.selected_id=None; self.save_refresh()
    def create_folder(self):
        title=self.folder_name.get().strip()
        if title: self.store.add_folder(self.current_parent,title); self.save_refresh()
    def delete_folder(self):
        n=self.selected()
        if n and n.get("isCustomFolder") and messagebox.askyesno(APP_TITLE,"선택한 폴더와 안의 작업을 삭제할까요?"): self.store.delete_subtree(n["id"]); self.selected_id=None; self.save_refresh()
    def open_date(self,mode,key): self.card_render_limit=CARD_RENDER_BATCH; self.current_date_mode=mode; self.current_date=key; self.current_list_id=None; self.view_mode="date"; self.selected_id=None; self.refresh_workspace()
    def start_drag(self,nid,event=None):
        self.drag_source=nid
        self.drag_last_target=None
        self.drag_last_after=False
        if event:
            self.drag_start_x=event.x_root; self.drag_start_y=event.y_root

    def target_from_event(self,event):
        w=self.winfo_containing(event.x_root,event.y_root); target=None; target_widget=None; after=False
        while w:
            if w in self.drop_targets:
                target=self.drop_targets[w]; target_widget=w
                after = event.y_root > target_widget.winfo_rooty() + target_widget.winfo_height() / 2
                break
            w=getattr(w,"master",None)
        if target:
            return target, target_widget, after
        if self.view_mode != "matrix" and getattr(self, "virtual_ids", None):
            local_y = event.y_root - self.cards.winfo_rooty()
            data_y = self.virtual_scroll_y + local_y
            idx = int(data_y // VROW_HEIGHT)
            if 0 <= idx < len(self.virtual_ids):
                target = self.virtual_ids[idx]
                after = (data_y % VROW_HEIGHT) > (VROW_HEIGHT / 2)
                return target, None, after
        return None, None, False

    def clear_drag_indicator(self):
        self.cards.delete("drag_indicator")
        for row in getattr(self, "virtual_row_widgets", []):
            if row.get("nid"):
                row["frame"].configure(border_color="#d9e9f1", border_width=1)

    def drag_motion(self,event):
        if not self.drag_source:
            return
        moved = abs(event.x_root - self.drag_start_x) + abs(event.y_root - self.drag_start_y) >= 8
        if not moved:
            return
        target, target_widget, after = self.target_from_event(event)
        self.drag_last_target=target
        self.drag_last_after=after
        self.cards.delete("drag_indicator")
        for row in getattr(self, "virtual_row_widgets", []):
            if row.get("nid"):
                row["frame"].configure(border_color="#d9e9f1", border_width=1)
        if not target or target == self.drag_source:
            return
        src_node = self.store.node(self.drag_source); target_node = self.store.node(target)
        same_parent = src_node and target_node and src_node.get("parentId") == target_node.get("parentId")
        width=max(1,self.cards.winfo_width())
        if same_parent:
            if target_widget:
                y = target_widget.winfo_rooty() - self.cards.winfo_rooty() + (target_widget.winfo_height() if after else 0)
            else:
                idx = self.virtual_ids.index(target) if target in self.virtual_ids else 0
                y = idx * VROW_HEIGHT - self.virtual_scroll_y + (VROW_HEIGHT if after else 0)
            self.cards.create_line(18, y, width-24, y, fill=COL["primary"], width=3, tags=("drag_indicator",))
            self.cards.create_text(width-120, max(12,y-18), text="위/아래 순서 변경", anchor="nw", fill=COL["primary"], font=(READ_FONT, 9, "bold"), tags=("drag_indicator",))
        else:
            for row in getattr(self, "virtual_row_widgets", []):
                if row.get("nid") == target:
                    row["frame"].configure(border_color=COL["primary"], border_width=2)
                    break
            self.cards.create_text(width-150, 10, text="작업 안으로 이동", anchor="nw", fill=COL["primary"], font=(READ_FONT, 10, "bold"), tags=("drag_indicator",))

    def finish_drag(self,event):
        if not self.drag_source:
            return
        src=self.drag_source; self.drag_source=None
        moved = abs(event.x_root - self.drag_start_x) + abs(event.y_root - self.drag_start_y) >= 8
        target, target_widget, after = self.target_from_event(event)
        self.clear_drag_indicator()
        if not moved:
            self.open_node(src)
            return "break"
        if target and target != src:
            src_node = self.store.node(src); target_node = self.store.node(target)
            if src_node and target_node and src_node.get("parentId") == target_node.get("parentId"):
                if self.store.reorder_node(src, target, after=after): self.save_refresh(); return "break"
            if self.store.move_node(src,target): self.save_refresh(); return "break"
        return "break"

    def release_card(self,event,nid):
        return self.finish_drag(event)

    def drop_drag(self,event):
        return self.finish_drag(event)

    def load_json(self):
        path=filedialog.askopenfilename(filetypes=[("JSON","*.json"),("All","*.*")])
        if path:
            try: self.store.load_from(path); self.go_root()
            except Exception as e: messagebox.showerror(APP_TITLE,f"불러오기 실패: {e}")
    def save_json(self):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")])
        if path: self.store.save_as(path)
    def show_tree_view(self):
        root = self.store.node(self.current_parent) or self.store.node(ROOT_ID)
        root_id = root.get("id", ROOT_ID)
        win = ctk.CTkToplevel(self)
        win.title("\ud604\uc7ac \uc791\uc5c5 \ud2b8\ub9ac")
        win.geometry("980x720")
        win.minsize(760, 500)
        win.configure(fg_color=COL["bg"])
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(1, weight=1)

        title_text = root.get("title", "\ub8e8\ud2b8") if root_id != ROOT_ID else "\ub8e8\ud2b8"
        header = ctk.CTkFrame(win, fg_color=COL["panel"], corner_radius=22, border_width=1, border_color=COL["line"])
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="\ud604\uc7ac \uc791\uc5c5 \ud2b8\ub9ac", font=(FONT, 24, "bold"), text_color=COL["text"], anchor="w").grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 2))
        ctk.CTkLabel(header, text=f"{title_text} \uc544\ub798\uc758 \ud558\uc704 \uc791\uc5c5\uc744 \uc2e4\uc81c \ud2b8\ub9ac \ub178\ub4dc\ub85c \ubcf4\uc5ec\uc90d\ub2c8\ub2e4. \ud074\ub9ad\ud558\uba74 \uc120\ud0dd, \ub354\ube14\ud074\ub9ad\ud558\uba74 \ud574\ub2f9 \uc791\uc5c5\uc73c\ub85c \uc774\ub3d9\ud569\ub2c8\ub2e4.", font=SMALL_FONT, text_color=COL["muted"], anchor="w").grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 16))

        body = ctk.CTkFrame(win, fg_color=COL["panel"], corner_radius=22, border_width=1, border_color=COL["line"])
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        style = ttk.Style(win)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TaskTree.Treeview", background=COL["panel"], fieldbackground=COL["panel"], foreground=COL["text"], rowheight=34, font=(READ_FONT, 12), borderwidth=0, relief="flat")
        style.configure("TaskTree.Treeview.Heading", font=(READ_FONT, 11, "bold"), foreground=COL["muted"], background=COL["soft"], relief="flat")
        style.map("TaskTree.Treeview", background=[("selected", COL["hero_soft"])], foreground=[("selected", COL["text"])])

        tree = ttk.Treeview(body, style="TaskTree.Treeview", columns=("done", "kind", "priority", "flags", "children", "created"), show="tree headings", selectmode="browse")
        for col, text in (("#0", "\uc791\uc5c5"), ("done", "\uc644\ub8cc"), ("kind", "\uc885\ub958"), ("priority", "\uc6b0\uc120"), ("flags", "\ud45c\uc2dc"), ("children", "\ud558\uc704"), ("created", "\uc791\uc131")):
            tree.heading(col, text=text)
        tree.column("#0", width=420, minwidth=240, stretch=True)
        tree.column("done", width=62, minwidth=56, stretch=False, anchor="center")
        tree.column("kind", width=84, minwidth=70, stretch=False, anchor="center")
        tree.column("priority", width=72, minwidth=58, stretch=False, anchor="center")
        tree.column("flags", width=128, minwidth=86, stretch=False, anchor="center")
        tree.column("children", width=64, minwidth=54, stretch=False, anchor="center")
        tree.column("created", width=116, minwidth=96, stretch=False, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=(12, 0))
        ybar = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(body, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        ybar.grid(row=0, column=1, sticky="ns", pady=(12, 0))
        xbar.grid(row=1, column=0, sticky="ew", padx=(12, 0), pady=(0, 12))

        tree.tag_configure("task", background=COL["panel"], foreground=COL["text"])
        tree.tag_configure("memo", background=COL["memo"], foreground=COL["text"])
        tree.tag_configure("folder", background=COL["folder"], foreground=COL["text"])
        tree.tag_configure("today", background=COL["today"], foreground=COL["text"])
        tree.tag_configure("important", background=COL["important"], foreground=COL["text"])
        tree.tag_configure("done", background=COL["done"], foreground=COL["muted"])

        def clean(value):
            value = str(value or "\uc774\ub984 \uc5c6\uc74c").replace("\r", " ").replace("\n", " ").strip()
            return value or "\uc774\ub984 \uc5c6\uc74c"
        def values_for(n):
            flags = []
            if n.get("isToday"):
                flags.append("\uc624\ub298")
            if n.get("isImportant"):
                flags.append("\uc911\uc694")
            kind = "\uba54\ubaa8" if n.get("kind") == "memo" else "\ud3f4\ub354" if n.get("isCustomFolder") else "\ud560 \uc77c"
            return ("\u2611" if n.get("completed") else "\u2610", kind, "-" if n.get("priority") is None else str(n.get("priority")), " \u00b7 ".join(flags), str(len(self.store.children(n.get("id")))), human_time(n.get("createdAt")))
        def tags_for(n):
            if n.get("completed"):
                return ("done",)
            if n.get("kind") == "memo":
                return ("memo",)
            if n.get("isCustomFolder"):
                return ("folder",)
            if n.get("isImportant"):
                return ("important",)
            if n.get("isToday"):
                return ("today",)
            return ("task",)
        def insert_node(parent_iid, nid, opened=False):
            n = self.store.node(nid) or {}
            tree.insert(parent_iid, "end", iid=nid, text=clean(n.get("title")), values=values_for(n), tags=tags_for(n), open=opened)
            for child_id in self.store.children(nid):
                insert_node(nid, child_id, False)
        def rebuild_tree():
            tree.delete(*tree.get_children(""))
            if self.store.children(root_id):
                for child_id in self.store.children(root_id):
                    insert_node("", child_id, False)
                first = self.store.children(root_id)[0]
                tree.selection_set(first)
                tree.focus(first)
                select_tree_item()
            else:
                tree.insert("", "end", iid=root_id, text="\ud558\uc704 \uc791\uc5c5\uc774 \uc5c6\uc2b5\ub2c8\ub2e4", values=("", "", "", "", "", ""), tags=("task",), open=True)

        def refresh_tree_item(nid):
            n = self.store.node(nid)
            if n and tree.exists(nid):
                tree.item(nid, text=clean(n.get("title")), values=values_for(n), tags=tags_for(n))
        def current_tree_id():
            focused = tree.focus()
            return focused if focused in self.store.nodes else None
        def select_tree_item(_event=None):
            nid = current_tree_id()
            if nid:
                self.select_node(nid)
        def open_tree_item(_event=None):
            nid = current_tree_id()
            if nid:
                self.open_node(nid)
                win.destroy()
        def toggle_tree_done(_event=None):
            nid = current_tree_id()
            n = self.store.node(nid) if nid else None
            if not n or nid == ROOT_ID or n.get("kind") == "memo" or n.get("isCustomFolder"):
                return "break"
            n["completed"] = not n.get("completed")
            n["completedAt"] = now_iso() if n["completed"] else None
            self.store.save()
            refresh_tree_item(nid)
            self.refresh_cards()
            return "break"
        def tree_click(event):
            row = tree.identify_row(event.y)
            col = tree.identify_column(event.x)
            if row:
                tree.selection_set(row)
                tree.focus(row)
                select_tree_item()
                if tree.identify("region", event.x, event.y) == "cell" and col == "#1":
                    return toggle_tree_done()
            return None

        tree.bind("<<TreeviewSelect>>", select_tree_item, add="+")
        tree.bind("<Button-1>", tree_click, add="+")
        tree.bind("<Double-Button-1>", open_tree_item, add="+")
        tree.bind("<space>", toggle_tree_done, add="+")
        tree.bind("<Return>", open_tree_item, add="+")
        rebuild_tree()

        footer = ctk.CTkFrame(win, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))
        footer.grid_columnconfigure(0, weight=1)
        self.make_btn(footer, "\uc120\ud0dd \uc791\uc5c5\uc73c\ub85c \uc774\ub3d9", open_tree_item, COL["primary"], height=38).grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.make_btn(footer, "\uc644\ub8cc \uccb4\ud06c", toggle_tree_done, variant="nav", height=38).grid(row=0, column=2, sticky="e", padx=(8, 0))
        self.make_btn(footer, "\ub2eb\uae30", win.destroy, variant="nav", height=38).grid(row=0, column=3, sticky="e", padx=(8, 0))
        win.transient(self)
        win.focus_force()
        tree.focus_set()

    def export_txt(self):
        restore = messagebox.askyesnocancel(APP_TITLE, "\uBA54\uBAA8/\uC6B0\uC120\uC21C\uC704/\uC624\uB298/\uC911\uC694/\uC644\uB8CC\uB97C \uD3EC\uD568\uD55C \uBCF5\uC6D0 \uAC00\uB2A5 TXT\uB85C \uB0B4\uBCF4\uB0BC\uAE4C\uC694?\n\n\uC608: \uBCF5\uC6D0 \uAC00\uB2A5 TXT\n\uC544\uB2C8\uC624: \uC81C\uBAA9\uB9CC \uC788\uB294 \uAC04\uB2E8 TXT")
        if restore is None:
            return
        path=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text","*.txt")])
        if not path: return
        lines=[]
        def meta_for(n):
            if not restore:
                return ""
            parts = [f"kind={n.get('kind','task')}"]
            if n.get("priority") is not None: parts.append(f"priority={n.get('priority')}")
            if n.get("isToday"): parts.append("today")
            if n.get("isImportant"): parts.append("important")
            if n.get("completed"): parts.append("done")
            return " {" + " ".join(parts) + "}"
        def walk(pid,prefix=""):
            kids=self.store.children(pid)
            for i,cid in enumerate(kids):
                n=self.store.node(cid); last=i==len(kids)-1
                lines.append(f"{prefix}{'\u2514\u2500\u2500' if last else '\u251c\u2500\u2500'} {n.get('title','\uC774\uB984 \uC5C6\uC74C')}{meta_for(n)}")
                if restore and n.get("memo"):
                    memo_prefix = prefix + ("    " if last else "\u2502   ")
                    for memo_line in str(n.get("memo", "")).splitlines():
                        lines.append(f"{memo_prefix}> {memo_line}")
                walk(cid,prefix+("    " if last else "\u2502   "))
        walk(self.current_parent); Path(path).write_text("\n".join(lines),encoding="utf-8")
    def save_window_state(self):
        ui = self.store.state.setdefault("ui", {})
        ui["zoomed"] = self.state() == "zoomed"
        if not ui["zoomed"]:
            ui["geometry"] = self.geometry()

    def on_close(self):
        if self.activity_poll_after_id:
            try: self.after_cancel(self.activity_poll_after_id)
            except Exception: pass
            self.activity_poll_after_id = None
        self.activity_log.close_current()
        self.activity_log.conn.close()
        self.save_window_state(); self.store.save(); self.destroy()

def main():
    try:
        App().mainloop()
    except Exception:
        detail = traceback.format_exc()
        log_path = write_startup_error(detail)
        try:
            root = tk.Tk()
            root.withdraw()
            suffix = f"\n\n로그: {log_path}" if log_path else ""
            messagebox.showerror("TaskExplorer 시작 실패", f"앱을 시작하지 못했습니다.{suffix}\n\n{detail[:1200]}")
            root.destroy()
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
