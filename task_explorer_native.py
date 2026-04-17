import json
import re
import shutil
import sys
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk

APP_TITLE = "작업 큐 탐색기"
ROOT_ID = "root"
STATE_FILE = "task-explorer-state.json"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COL = {
    "bg": "#f2f6f8",
    "panel": "#ffffff",
    "soft": "#f7fafc",
    "line": "#dbe5ed",
    "text": "#102235",
    "muted": "#6b7b8f",
    "primary": "#176b87",
    "primary_hover": "#10536b",
    "accent": "#f29f67",
    "accent_soft": "#fff3e9",
    "danger": "#c83f49",
    "danger_soft": "#fff0f1",
    "sidebar": "#eef9ff",
    "sidebar_soft": "#f8fdff",
    "sidebar_line": "#d3edf8",
    "sidebar_text": "#143247",
    "sidebar_muted": "#5f7c90",
    "memo": "#fff6dd",
    "folder": "#eaf1ff",
    "today": "#e7f5f2",
    "important": "#fff0d6",
    "done": "#eaf7ea",
    "matrix_a": "#ffe6e7",
    "matrix_b": "#fff0cf",
    "matrix_c": "#dff1ff",
    "matrix_d": "#edf1f5",
    "hero": "#fbf8f3",
    "hero_soft": "#fff3e3",
    "hero_line": "#efd8bf",
    "detail_bg": "#eef8fc",
    "detail_panel": "#f8fdff",
    "detail_button": "#dff1f8",
}

FONT = "Segoe UI Rounded"
READ_FONT = "Malgun Gothic"
TITLE_FONT = (FONT, 26, "bold")
SECTION_FONT = (FONT, 14, "bold")
BODY_FONT = (FONT, 12)
SMALL_FONT = (FONT, 11)
READ_BODY_FONT = (READ_FONT, 12)
READ_TITLE_FONT = (READ_FONT, 15, "bold")


def app_dir():
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


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


def clean_title(text):
    text = re.sub(r"^[\s│]*(?:├──|└──|[-*+]\s*)", "", str(text)).strip()
    return text or "이름 없음"


def parse_tree_text(raw):
    rows = []
    for line in str(raw or "").replace("\r\n", "\n").split("\n"):
        if not line.strip():
            continue
        text = line.rstrip().replace("\t", "    ")
        match = re.match(r"^(?P<prefix>[\s│]*)(?P<mark>├──|└──)\s+(?P<title>.*)$", text)
        if match:
            prefix = match.group("prefix") or ""
            depth = 1
            i = 0
            while i + 3 < len(prefix) and prefix[i:i+4] in ("│   ", "    "):
                depth += 1
                i += 4
            rows.append({"title": clean_title(match.group("title")), "depth": depth})
        else:
            leading = len(text) - len(text.lstrip(" "))
            rows.append({"title": clean_title(text), "depth": leading // 2})
    return rows


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
        if self.path.exists():
            try:
                self.state = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                try:
                    shutil.copy2(self.path, self.path.with_suffix(".broken.json"))
                except Exception:
                    pass
                self.state = self.empty()
        self.ensure()
        self.save()

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


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE); self.geometry("1560x940"); self.minsize(1180, 740); self.configure(fg_color=COL["bg"])
        self.store = TaskStore(); self.current_parent = ROOT_ID; self.selected_id = None; self.view_mode = "all"; self.kind_filter = "all"
        self.current_list_id = None; self.current_date = None; self.current_date_mode = None; self.drag_source = None; self.drop_targets = {}; self.folder_ids = []; self.paste_open = False
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self.build_sidebar(); self.build_main(); self.build_detail(); self.refresh_all(); self.protocol("WM_DELETE_WINDOW", self.on_close)

    def make_btn(self, parent, text, command, color=None, variant="soft", height=36):
        if variant == "nav":
            return ctk.CTkButton(parent, text=text, command=command, fg_color=COL["sidebar_soft"], hover_color="#dff3fb", text_color=COL["sidebar_text"], height=height, corner_radius=12, font=SMALL_FONT, border_width=1, border_color=COL["sidebar_line"])
        if variant == "danger":
            return ctk.CTkButton(parent, text=text, command=command, fg_color=COL["danger_soft"], hover_color="#ffdfe2", text_color=COL["danger"], height=height, corner_radius=12, font=SMALL_FONT)
        if color:
            return ctk.CTkButton(parent, text=text, command=command, fg_color=color, hover_color=COL["primary_hover"], text_color="white", height=height, corner_radius=12, font=SMALL_FONT)
        return ctk.CTkButton(parent, text=text, command=command, fg_color=COL["soft"], hover_color="#e8eef5", text_color=COL["text"], height=height, corner_radius=12, font=SMALL_FONT, border_width=1, border_color=COL["line"])

    def pill(self, parent, text, color=None):
        return ctk.CTkLabel(parent, text=text, font=(FONT, 11, "bold"), text_color="white" if color else COL["muted"], fg_color=color or COL["soft"], corner_radius=16, padx=12, pady=5)

    def build_sidebar(self):
        self.side = ctk.CTkFrame(self, fg_color=COL["sidebar"], corner_radius=0, width=306); self.side.grid(row=0, column=0, sticky="nsew"); self.side.grid_propagate(False); self.side.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.side, text=APP_TITLE, font=(FONT, 28, "bold"), text_color=COL["sidebar_text"], anchor="w").grid(row=0, column=0, sticky="ew", padx=22, pady=(24, 2))
        ctk.CTkLabel(self.side, text="큰 일을 작게 쪼개고 오늘 할 행동만 선명하게 고르는 탐색형 작업 큐", font=SMALL_FONT, text_color=COL["sidebar_muted"], anchor="w", justify="left", wraplength=245).grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 18))
        self.search = ctk.CTkEntry(self.side, placeholder_text="작업 / 메모 검색", height=42, fg_color=COL["sidebar_soft"], border_color=COL["sidebar_line"], text_color=COL["sidebar_text"], placeholder_text_color=COL["sidebar_muted"], font=SMALL_FONT); self.search.grid(row=2, column=0, sticky="ew", padx=22); self.search.bind("<Return>", lambda _e: self.refresh_cards())
        self.make_btn(self.side, "검색", self.refresh_cards, COL["primary"], height=42).grid(row=3, column=0, sticky="ew", padx=22, pady=(8, 20))
        ctk.CTkLabel(self.side, text="작업 보기", font=SECTION_FONT, text_color=COL["sidebar_text"], anchor="w").grid(row=4, column=0, sticky="ew", padx=22)
        modes = [("전체", "all"), ("오늘 할 일", "today"), ("중요", "important"), ("우선순위 맵", "matrix"), ("완료", "done")]
        mf = ctk.CTkFrame(self.side, fg_color="transparent"); mf.grid(row=5, column=0, sticky="ew", padx=22, pady=(8, 18)); mf.grid_columnconfigure((0,1), weight=1)
        for i, (t, v) in enumerate(modes): self.make_btn(mf, t, lambda x=v: self.set_view(x), variant="nav").grid(row=i//2, column=i%2, sticky="ew", padx=3, pady=3)
        ctk.CTkLabel(self.side, text="콘텐츠 필터", font=SECTION_FONT, text_color=COL["sidebar_text"], anchor="w").grid(row=6, column=0, sticky="ew", padx=22)
        kf = ctk.CTkFrame(self.side, fg_color="transparent"); kf.grid(row=7, column=0, sticky="ew", padx=22, pady=(8, 18)); kf.grid_columnconfigure((0,1,2), weight=1)
        for i, (t, v) in enumerate([("전체", "all"), ("할 일", "task"), ("메모", "memo")]): self.make_btn(kf, t, lambda x=v: self.set_kind(x), variant="nav", height=34).grid(row=0, column=i, sticky="ew", padx=3)
        files = ctk.CTkFrame(self.side, fg_color="transparent"); files.grid(row=8, column=0, sticky="ew", padx=22, pady=(0, 18)); files.grid_columnconfigure((0,1), weight=1)
        for i, (t, c) in enumerate([("JSON 불러오기", self.load_json), ("JSON 저장", self.save_json), ("TXT 내보내기", self.export_txt), ("현재 하위 메모화", self.memoize_current)]): self.make_btn(files, t, c, variant="nav", height=34).grid(row=i//2, column=i%2, sticky="ew", padx=3, pady=3)
        self.date_frame = self.side_section("날짜별 보기", 9); self.list_frame = self.side_section("저장 목록", 11); self.folder_frame = self.side_section("프로젝트 폴더", 13)

    def side_section(self, title, row):
        ctk.CTkLabel(self.side, text=title, font=SECTION_FONT, text_color=COL["sidebar_text"], anchor="w").grid(row=row, column=0, sticky="ew", padx=22)
        frame = ctk.CTkScrollableFrame(self.side, fg_color=COL["sidebar_soft"], height=100, corner_radius=16, border_width=1, border_color=COL["sidebar_line"]); frame.grid(row=row+1, column=0, sticky="ew", padx=22, pady=(8, 14)); frame.grid_columnconfigure(0, weight=1); return frame
    def build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=COL["bg"], corner_radius=0); self.main.grid(row=0, column=1, sticky="nsew", padx=22, pady=20); self.main.grid_columnconfigure(0, weight=1); self.main.grid_rowconfigure(5, weight=1)
        hero = ctk.CTkFrame(self.main, fg_color=COL["hero"], corner_radius=24, border_width=1, border_color=COL["hero_line"]); hero.grid(row=0, column=0, sticky="ew", pady=(0, 16)); hero.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hero, text="Focus Workspace", font=(FONT, 12, "bold"), text_color=COL["accent"], anchor="w").grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 0))
        self.path_label = ctk.CTkLabel(hero, text="루트", font=(FONT, 26, "bold"), text_color=COL["text"], anchor="w"); self.path_label.grid(row=1, column=0, sticky="ew", padx=22, pady=(2, 0))
        self.hint = ctk.CTkLabel(hero, text="", font=BODY_FONT, text_color=COL["muted"], anchor="w"); self.hint.grid(row=2, column=0, sticky="ew", padx=22, pady=(4, 18))
        self.summary = ctk.CTkLabel(hero, text="", font=(FONT, 13, "bold"), text_color="white", fg_color=COL["primary"], corner_radius=18, padx=16, pady=7); self.summary.grid(row=1, column=1, sticky="e", padx=22)
        add = ctk.CTkFrame(self.main, fg_color=COL["panel"], corner_radius=22, border_width=1, border_color=COL["line"]); add.grid(row=2, column=0, sticky="ew", pady=(0, 12)); add.grid_columnconfigure(0, weight=1)
        self.title_entry = ctk.CTkEntry(add, placeholder_text="새 작업을 입력하세요", height=46, font=(READ_FONT, 13), border_color=COL["line"], fg_color=COL["soft"]); self.title_entry.grid(row=0, column=0, sticky="ew", padx=14, pady=14); self.title_entry.bind("<Return>", lambda _e: self.add_task())
        self.kind_var = ctk.StringVar(value="할 일"); ctk.CTkOptionMenu(add, values=["할 일", "메모"], variable=self.kind_var, width=92, height=46, font=SMALL_FONT, fg_color=COL["primary"], button_color=COL["primary_hover"], button_hover_color=COL["primary_hover"]).grid(row=0, column=1, padx=(0, 8))
        self.priority = ctk.CTkEntry(add, placeholder_text="우선순위", width=100, height=46, font=SMALL_FONT, border_color=COL["line"], fg_color=COL["soft"]); self.priority.grid(row=0, column=2, padx=(0, 8))
        self.today_var = ctk.BooleanVar(value=False); ctk.CTkCheckBox(add, text="오늘", variable=self.today_var, width=70).grid(row=0, column=3, padx=(0, 8))
        self.make_btn(add, "추가", self.add_task, COL["primary"]).grid(row=0, column=4, padx=(0, 12), sticky="ns")
        self.paste = ctk.CTkFrame(self.main, fg_color=COL["panel"], corner_radius=18, border_width=1, border_color=COL["line"]); self.paste.grid_columnconfigure(0, weight=1)
        self.paste_text = ctk.CTkTextbox(self.paste, height=110, font=READ_BODY_FONT); self.paste_text.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        self.make_btn(self.paste, "붙여넣기 추가", self.add_pasted_tree, COL["primary"]).grid(row=0, column=1, padx=(0,12), pady=12, sticky="ns")
        tb = ctk.CTkFrame(self.main, fg_color=COL["panel"], corner_radius=20, border_width=1, border_color=COL["line"]); tb.grid(row=3, column=0, sticky="ew", pady=(0, 12)); tb.grid_columnconfigure((0,1,2), weight=1)
        self.action_group(tb, "탐색", [("루트", self.go_root), ("열기", self.open_selected), ("위로 이동", self.move_to_parent), ("트리 붙여넣기", self.toggle_paste)], 0)
        self.action_group(tb, "작업", [("수정", self.rename_selected), ("복사", self.copy_selected), ("삭제", self.delete_selected), ("메모화", self.memoize_selected), ("할 일화", self.taskify_selected)], 1)
        self.action_group(tb, "상태", [("완료", self.toggle_done), ("중요", self.toggle_important), ("오늘", self.toggle_today), ("다음 행동", self.next_action), ("목록에 추가", self.add_to_list), ("목록에서 제거", self.remove_from_list)], 2)
        self.cards = ctk.CTkScrollableFrame(self.main, fg_color="transparent"); self.cards.grid(row=5, column=0, sticky="nsew"); self.cards.grid_columnconfigure(0, weight=1)

    def action_group(self, parent, title, actions, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent"); frame.grid(row=0, column=col, sticky="nsew", padx=10, pady=10); frame.grid_columnconfigure((0,1), weight=1)
        ctk.CTkLabel(frame, text=title, font=(FONT, 12, "bold"), text_color=COL["muted"], anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        for i, (text, cmd) in enumerate(actions):
            self.make_btn(frame, text, cmd, variant="danger" if text == "삭제" else "soft", height=32).grid(row=1 + i // 2, column=i % 2, sticky="ew", padx=3, pady=3)

    def build_detail(self):
        self.detail = ctk.CTkFrame(self, fg_color=COL["detail_bg"], corner_radius=0, width=410); self.detail.grid(row=0, column=2, sticky="nsew"); self.detail.grid_propagate(False); self.detail.grid_columnconfigure(0, weight=1); self.detail.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(self.detail, text="작업 상세", font=SECTION_FONT, text_color=COL["muted"], anchor="w").grid(row=0, column=0, sticky="ew", padx=22, pady=(24, 4))
        self.detail_title = ctk.CTkLabel(self.detail, text="선택 없음", font=(FONT, 24, "bold"), text_color=COL["text"], anchor="w", justify="left", wraplength=360); self.detail_title.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 8))
        self.detail_meta = ctk.CTkLabel(self.detail, text="작업을 선택하면 상세가 보입니다.", text_color=COL["muted"], anchor="w", justify="left", wraplength=360, font=SMALL_FONT); self.detail_meta.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 16))
        self.memo = ctk.CTkTextbox(self.detail, fg_color=COL["detail_panel"], corner_radius=18, border_width=1, border_color=COL["line"], font=READ_BODY_FONT); self.memo.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 12))
        ctk.CTkButton(self.detail, text="메모 저장", command=self.save_memo, fg_color=COL["detail_button"], hover_color="#d9edf2", text_color=COL["primary"], height=42, corner_radius=14, font=SMALL_FONT, border_width=1, border_color=COL["line"]).grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 18))

    def set_view(self, mode):
        self.view_mode = mode; self.current_list_id = None; self.current_date = None; self.current_date_mode = None
        if mode != "all": self.current_parent = ROOT_ID
        self.selected_id = None; self.refresh_all()
    def set_kind(self, kind): self.kind_filter = kind; self.refresh_cards()
    def save_refresh(self): self.store.save(); self.refresh_all()

    def refresh_all(self):
        parent = self.store.node(self.current_parent); self.kind_var.set("메모" if parent and parent.get("kind") == "memo" else "할 일")
        self.refresh_path(); self.refresh_side(); self.refresh_cards(); self.refresh_detail()

    def refresh_path(self):
        if self.view_mode == "pathList" and self.current_list_id:
            item = self.store.path_list(self.current_list_id); self.path_label.configure(text=f"목록 > {item.get('title') if item else '목록 없음'}"); self.hint.configure(text="바로가기 목록입니다. 목록에서 제거해도 실제 작업은 남습니다."); return
        if self.current_date:
            self.path_label.configure(text=f"{'작성일' if self.current_date_mode == 'created' else '완료일'} > {self.current_date}"); self.hint.configure(text="날짜별 바로가기 보기입니다."); return
        parts=[]; cur=self.store.node(self.current_parent)
        while cur:
            parts.append(cur.get("title","")); pid=cur.get("parentId"); cur=self.store.node(pid) if pid else None
        self.path_label.configure(text=" > ".join(reversed(parts)) or "루트"); self.hint.configure(text="작업을 카드로 정리하고, 오늘/중요/메모를 한 화면에서 관리합니다.")

    def clear_frame(self, frame):
        for w in frame.winfo_children(): w.destroy()

    def refresh_side(self):
        self.clear_frame(self.date_frame); self.clear_frame(self.list_frame); self.clear_frame(self.folder_frame)
        created=defaultdict(int); done=defaultdict(int)
        for n in self.store.all_nodes():
            created[date_key(n.get("createdAt"))]+=1
            if n.get("completedAt"): done[date_key(n.get("completedAt"))]+=1
        r=0
        for k in sorted(created, reverse=True): self.side_item(self.date_frame, f"작성 {k} ({created[k]})", lambda x=k: self.open_date("created", x), r); r+=1
        for k in sorted(done, reverse=True): self.side_item(self.date_frame, f"완료 {k} ({done[k]})", lambda x=k: self.open_date("done", x), r); r+=1
        for i,item in enumerate(self.store.path_lists): self.side_item(self.list_frame, f"{item.get('title','목록')} ({len(item.get('taskIds',[]))})", lambda x=item.get('id'): self.open_list(x), i)
        self.list_name = ctk.CTkEntry(self.list_frame, placeholder_text="목록 이름", fg_color=COL["panel"], border_color=COL["sidebar_line"], height=34); self.list_name.grid(row=999, column=0, sticky="ew", pady=(8,3))
        bf=ctk.CTkFrame(self.list_frame, fg_color="transparent"); bf.grid(row=1000,column=0,sticky="ew"); bf.grid_columnconfigure((0,1),weight=1); self.make_btn(bf,"만들기",self.create_list).grid(row=0,column=0,sticky="ew",padx=2); self.make_btn(bf,"삭제",self.delete_list).grid(row=0,column=1,sticky="ew",padx=2)
        self.folder_ids=[]
        for i,n in enumerate(self.store.folders()): self.folder_ids.append(n["id"]); self.side_item(self.folder_frame, f"{n.get('title','폴더')} ({len(self.store.children(n['id']))})", lambda x=n['id']: self.open_node(x), i)
        self.folder_name = ctk.CTkEntry(self.folder_frame, placeholder_text="폴더 이름", fg_color=COL["panel"], border_color=COL["sidebar_line"], height=34); self.folder_name.grid(row=999,column=0,sticky="ew",pady=(8,3))
        fb=ctk.CTkFrame(self.folder_frame, fg_color="transparent"); fb.grid(row=1000,column=0,sticky="ew"); fb.grid_columnconfigure((0,1),weight=1); self.make_btn(fb,"만들기",self.create_folder).grid(row=0,column=0,sticky="ew",padx=2); self.make_btn(fb,"삭제",self.delete_folder).grid(row=0,column=1,sticky="ew",padx=2)

    def side_item(self, parent, text, command, row): self.make_btn(parent, text, command, variant="nav", height=32).grid(row=row, column=0, sticky="ew", pady=2)
    def row_visible(self, n):
        if not n or n.get("id") == ROOT_ID: return False
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

    def refresh_cards(self):
        self.clear_frame(self.cards); self.drop_targets={}
        if self.view_mode=="matrix": self.render_matrix(); return
        ids=self.visible_ids(); self.summary.configure(text=f"{len(ids)}개 항목")
        if not ids: self.render_empty_state(); return
        for i,nid in enumerate(ids): self.render_card(self.cards,nid,i)

    def render_empty_state(self):
        box = ctk.CTkFrame(self.cards, fg_color=COL["panel"], corner_radius=26, border_width=1, border_color=COL["line"])
        box.grid(row=0, column=0, sticky="ew", padx=10, pady=42)
        box.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkLabel(box, text="아직 표시할 작업이 없습니다", font=(FONT, 22, "bold"), text_color=COL["text"]).grid(row=0, column=0, columnspan=3, pady=(30, 6))
        ctk.CTkLabel(box, text="위 입력창에서 큰 작업을 하나 만들고, 더블클릭해서 하위 작업으로 쪼개보세요.", font=BODY_FONT, text_color=COL["muted"]).grid(row=1, column=0, columnspan=3, pady=(0, 24))
        features = [("1", "쪼개기", "큰 일을 작은 다음 행동으로 분리"), ("2", "집중", "오늘/중요 표시로 우선순위 정리"), ("3", "기록", "메모와 날짜 보기로 작업 흐름 추적")]
        for i, (num, title, desc) in enumerate(features):
            card = ctk.CTkFrame(box, fg_color=COL["soft"], corner_radius=18, border_width=1, border_color=COL["line"])
            card.grid(row=2, column=i, sticky="nsew", padx=10, pady=(0, 28))
            self.pill(card, num, COL["primary"]).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
            ctk.CTkLabel(card, text=title, font=(READ_FONT, 15, "bold"), text_color=COL["text"], anchor="w").grid(row=1, column=0, sticky="ew", padx=14)
            ctk.CTkLabel(card, text=desc, font=(READ_FONT, 11), text_color=COL["muted"], anchor="w", justify="left", wraplength=210).grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 14))

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
        n=self.store.node(nid); bg=COL["folder"] if n.get("isCustomFolder") else COL["memo"] if n.get("kind")=="memo" else COL["done"] if n.get("completed") else COL["today"] if n.get("isToday") else COL["important"] if n.get("isImportant") else COL["panel"]
        border = COL["primary"] if n.get("isToday") else COL["accent"] if n.get("isImportant") else COL["line"]
        card=ctk.CTkFrame(parent,fg_color=bg,corner_radius=22,border_width=1,border_color=border); card.grid(row=row,column=0,sticky="ew",padx=6,pady=7); card.grid_columnconfigure(1,weight=1); self.drop_targets[card]=nid
        accent = ctk.CTkFrame(card, fg_color=border, width=5, corner_radius=12); accent.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(10, 0), pady=10)
        icon="프로젝트" if n.get("isCustomFolder") else "메모" if n.get("kind")=="memo" else "작업"; title=("완료  " if n.get("completed") else "")+n.get("title","이름 없음")
        head = ctk.CTkFrame(card, fg_color="transparent"); head.grid(row=0, column=1, sticky="ew", padx=14, pady=(12, 2)); head.grid_columnconfigure(0, weight=1)
        lab=ctk.CTkLabel(head,text=title,font=(READ_FONT,16 if not compact else 13,"bold"),text_color=COL["text"],anchor="w"); lab.grid(row=0,column=0,sticky="ew")
        self.pill(head, icon, border).grid(row=0, column=1, sticky="e")
        meta=[]
        if n.get("priority") is not None: meta.append(f"우선 {n.get('priority')}")
        if n.get("isToday"): meta.append("오늘")
        if n.get("isImportant"): meta.append("중요")
        if self.store.children(nid): meta.append(f"하위 {len(self.store.children(nid))}")
        meta.append(human_time(n.get("createdAt")))
        ctk.CTkLabel(card,text=" · ".join([x for x in meta if x]),font=(READ_FONT, 11),text_color=COL["muted"],anchor="w").grid(row=1,column=1,sticky="ew",padx=14,pady=(0,12))
        for w in (card,lab):
            w.bind("<Button-1>",lambda e,x=nid:self.select_node(x)); w.bind("<Double-Button-1>",lambda e,x=nid:self.open_node(x)); w.bind("<Button-3>",lambda e,x=nid:self.quick_done(x)); w.bind("<ButtonPress-1>",lambda e,x=nid:self.start_drag(x)); w.bind("<ButtonRelease-1>",self.drop_drag)

    def select_node(self,nid): self.selected_id=nid; self.refresh_detail()
    def selected(self,warn=True):
        n=self.store.node(self.selected_id) if self.selected_id else None
        if warn and not n: messagebox.showinfo(APP_TITLE,"작업을 선택하세요.")
        return n
    def open_node(self,nid):
        if self.store.node(nid): self.current_parent=nid; self.current_list_id=None; self.current_date=None; self.current_date_mode=None; self.view_mode="all"; self.selected_id=None; self.refresh_all()
    def open_selected(self):
        n=self.selected();
        if n: self.open_node(n["id"])
    def refresh_detail(self):
        n=self.store.node(self.selected_id) if self.selected_id else None; self.memo.delete("1.0","end")
        if not n: self.detail_title.configure(text="선택 없음"); self.detail_meta.configure(text="왼쪽 목록에서 작업을 선택하면 상태, 작성일, 메모를 확인할 수 있습니다."); return
        self.detail_title.configure(text=n.get("title","이름 없음")); meta=["폴더" if n.get("isCustomFolder") else "메모" if n.get("kind")=="memo" else "할 일",f"하위 {len(self.store.children(n['id']))}"]
        if n.get("priority") is not None: meta.append(f"우선 {n.get('priority')}")
        if n.get("isToday"): meta.append("오늘")
        if n.get("isImportant"): meta.append("중요")
        if n.get("completed"): meta.append("완료")
        meta.append(f"작성 {human_time(n.get('createdAt'))}")
        if n.get("completedAt"): meta.append(f"완료 {human_time(n.get('completedAt'))}")
        self.detail_meta.configure(text=" · ".join(meta)); self.memo.insert("1.0",n.get("memo",""))

    def add_task(self):
        title=self.title_entry.get().strip()
        if not title: return
        self.store.add_node(self.current_parent,title,"memo" if self.kind_var.get()=="메모" else "task",parse_priority(self.priority.get()),self.today_var.get()); self.title_entry.delete(0,"end"); self.priority.delete(0,"end"); self.today_var.set(False); self.save_refresh()
    def go_root(self): self.current_parent=ROOT_ID; self.current_list_id=None; self.current_date=None; self.current_date_mode=None; self.view_mode="all"; self.selected_id=None; self.refresh_all()
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
        items=parse_tree_text(self.paste_text.get("1.0","end")); parents={}
        for item in items:
            d=item["depth"]; pid=parents.get(d-1,self.current_parent); nid=self.store.add_node(pid,item["title"],"task"); parents[d]=nid; [parents.pop(x,None) for x in list(parents) if x>d]
        self.paste_text.delete("1.0","end"); self.save_refresh()
    def create_list(self):
        title=self.list_name.get().strip()
        if title: self.store.add_path_list(title); self.save_refresh()
    def open_list(self,lid): self.current_list_id=lid; self.current_date=None; self.current_date_mode=None; self.view_mode="pathList"; self.selected_id=None; self.refresh_all()
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
    def open_date(self,mode,key): self.current_date_mode=mode; self.current_date=key; self.current_list_id=None; self.view_mode="date"; self.selected_id=None; self.refresh_all()
    def start_drag(self,nid): self.drag_source=nid
    def drop_drag(self,event):
        src=self.drag_source; self.drag_source=None
        if not src: return
        w=self.winfo_containing(event.x_root,event.y_root); target=None
        while w:
            if w in self.drop_targets: target=self.drop_targets[w]; break
            w=getattr(w,"master",None)
        if target and target!=src and self.store.move_node(src,target): self.save_refresh()
    def load_json(self):
        path=filedialog.askopenfilename(filetypes=[("JSON","*.json"),("All","*.*")])
        if path:
            try: self.store.load_from(path); self.go_root()
            except Exception as e: messagebox.showerror(APP_TITLE,f"불러오기 실패: {e}")
    def save_json(self):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")])
        if path: self.store.save_as(path)
    def export_txt(self):
        path=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text","*.txt")])
        if not path: return
        lines=[]
        def walk(pid,prefix=""):
            kids=self.store.children(pid)
            for i,cid in enumerate(kids):
                n=self.store.node(cid); last=i==len(kids)-1; lines.append(f"{prefix}{'└──' if last else '├──'} {n.get('title','이름 없음')}"); walk(cid,prefix+("    " if last else "│   "))
        walk(self.current_parent); Path(path).write_text("\n".join(lines),encoding="utf-8")
    def on_close(self): self.store.save(); self.destroy()

if __name__ == "__main__":
    App().mainloop()
