import json
import os
import time
import uuid
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime
from collections import defaultdict

APP_TITLE = "작업 큐 탐색기"
STATE_FILE = "task-explorer-state.json"
ROOT_ID = "root"

COLORS = {
    "bg": "#eef4fb",
    "panel": "#ffffff",
    "line": "#d6e0ee",
    "text": "#172033",
    "muted": "#65728c",
    "primary": "#2563eb",
    "primary_soft": "#e7efff",
    "memo": "#fff8e8",
    "task": "#f8fbff",
    "done": "#edf8ef",
    "folder": "#edf2ff",
    "important": "#fff7df",
}


def now_iso():
    return datetime.now().astimezone().isoformat()


def new_id(prefix="task"):
    return f"{prefix}_{int(time.time() * 1000):x}_{uuid.uuid4().hex[:7]}"


def parse_priority(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return None


class TaskStore:
    def __init__(self):
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), STATE_FILE)
        self.state = self.empty_state()
        self.load_default()

    def empty_state(self):
        return {
            "nextOrder": 1,
            "nodes": {
                ROOT_ID: {
                    "id": ROOT_ID,
                    "title": "루트",
                    "parentId": None,
                    "completed": False,
                    "isToday": False,
                    "isImportant": False,
                    "kind": "task",
                    "memo": "",
                    "priority": None,
                    "completedAt": None,
                    "createdAt": now_iso(),
                    "createdOrder": 0,
                    "children": [],
                    "isCustomFolder": False,
                }
            },
            "customTabs": [],
            "pathLists": [],
        }

    @property
    def nodes(self):
        return self.state.setdefault("nodes", {})

    @property
    def path_lists(self):
        return self.state.setdefault("pathLists", [])

    @property
    def custom_tabs(self):
        return self.state.setdefault("customTabs", [])

    def node(self, node_id):
        return self.nodes.get(node_id)

    def load_default(self):
        if os.path.exists(self.path):
            self.load_file(self.path)
        else:
            self.ensure()

    def load_file(self, path):
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "nodes" not in data:
            raise ValueError("작업 상태 JSON이 아닙니다.")
        self.state = data
        self.ensure()

    def save_default(self):
        self.ensure()
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def save_as(self, path):
        self.ensure()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def ensure(self):
        if ROOT_ID not in self.nodes:
            self.state = self.empty_state()
            return
        if not isinstance(self.state.get("nextOrder"), (int, float)):
            self.state["nextOrder"] = 1
        for node_id, node in list(self.nodes.items()):
            if not isinstance(node, dict):
                del self.nodes[node_id]
                continue
            node.setdefault("id", node_id)
            node["id"] = str(node["id"])
            node.setdefault("title", "이름 없음")
            node.setdefault("parentId", ROOT_ID if node_id != ROOT_ID else None)
            node.setdefault("completed", False)
            node.setdefault("isToday", False)
            node.setdefault("isImportant", False)
            node.setdefault("kind", "task")
            if node.get("kind") not in ("task", "memo") or node_id == ROOT_ID:
                node["kind"] = "task"
            node.setdefault("memo", "")
            node.setdefault("priority", None)
            node.setdefault("completedAt", None)
            node.setdefault("createdAt", now_iso())
            node.setdefault("createdOrder", self.state["nextOrder"])
            node.setdefault("children", [])
            node.setdefault("isCustomFolder", False)
            if not isinstance(node["children"], list):
                node["children"] = []
            if node["kind"] == "memo":
                node["completed"] = False
                node["completedAt"] = None
                node["isToday"] = False
                node["isImportant"] = False
                node["priority"] = None
        self.nodes[ROOT_ID]["parentId"] = None
        self.nodes[ROOT_ID]["kind"] = "task"
        valid = set(self.nodes.keys())
        for node in self.nodes.values():
            node["children"] = [c for c in node.get("children", []) if c in valid and c != node["id"]]
        referenced = set()
        for node in self.nodes.values():
            for child_id in node.get("children", []):
                child = self.node(child_id)
                if child:
                    child["parentId"] = node["id"]
                    referenced.add(child_id)
        root_children = self.nodes[ROOT_ID].setdefault("children", [])
        for node_id, node in self.nodes.items():
            if node_id == ROOT_ID:
                continue
            if node_id not in referenced and node.get("parentId") not in self.nodes:
                node["parentId"] = ROOT_ID
                root_children.append(node_id)
        self.sort_all_children()

    def children(self, parent_id):
        parent = self.node(parent_id)
        if not parent:
            return []
        return [cid for cid in parent.get("children", []) if cid in self.nodes]

    def sort_key(self, node_id):
        n = self.node(node_id) or {}
        completed = 1 if n.get("completed") else 0
        priority = n.get("priority")
        p = priority if isinstance(priority, (int, float)) else 999999999
        return (completed, p, n.get("createdOrder", 0))

    def sort_children(self, parent_id):
        parent = self.node(parent_id)
        if parent:
            parent["children"] = sorted(self.children(parent_id), key=self.sort_key)

    def sort_all_children(self):
        for node_id in list(self.nodes.keys()):
            self.sort_children(node_id)

    def add_node(self, parent_id, title, kind="task", priority=None, is_today=False):
        parent = self.node(parent_id) or self.node(ROOT_ID)
        kind = "memo" if kind == "memo" else "task"
        node_id = new_id("task")
        order = int(self.state.get("nextOrder", 1))
        self.state["nextOrder"] = order + 1
        node = {
            "id": node_id,
            "title": title.strip() or "이름 없음",
            "parentId": parent["id"],
            "completed": False,
            "isToday": bool(is_today) if kind == "task" else False,
            "isImportant": False,
            "kind": kind,
            "memo": "",
            "priority": priority if kind == "task" else None,
            "completedAt": None,
            "createdAt": now_iso(),
            "createdOrder": order,
            "children": [],
            "isCustomFolder": False,
        }
        self.nodes[node_id] = node
        parent.setdefault("children", []).append(node_id)
        self.sort_children(parent["id"])
        return node_id

    def add_folder(self, parent_id, title):
        node_id = self.add_node(parent_id, title, kind="task")
        node = self.node(node_id)
        node["isCustomFolder"] = True
        node["kind"] = "task"
        self.custom_tabs.append({
            "id": node_id,
            "title": node["title"],
            "createdOrder": node["createdOrder"],
            "createdAt": node["createdAt"],
        })
        return node_id

    def folders(self):
        result = [n for n in self.nodes.values() if n.get("id") != ROOT_ID and n.get("isCustomFolder")]
        return sorted(result, key=lambda n: n.get("createdOrder", 0))

    def add_path_list(self, title):
        item = {
            "id": new_id("list"),
            "title": title.strip() or "목록",
            "taskIds": [],
            "createdOrder": self.state.get("nextOrder", 1),
            "createdAt": now_iso(),
        }
        self.state["nextOrder"] = int(self.state.get("nextOrder", 1)) + 1
        self.path_lists.append(item)
        return item["id"]

    def path_list(self, list_id):
        for item in self.path_lists:
            if item.get("id") == list_id:
                return item
        return None

    def all_nodes(self):
        return [n for n in self.nodes.values() if n.get("id") != ROOT_ID]

    def delete_subtree(self, node_id):
        if node_id == ROOT_ID:
            return
        node = self.node(node_id)
        if not node:
            return
        for child_id in list(node.get("children", [])):
            self.delete_subtree(child_id)
        parent = self.node(node.get("parentId"))
        if parent and node_id in parent.get("children", []):
            parent["children"].remove(node_id)
        self.nodes.pop(node_id, None)

    def set_kind(self, node_id, kind, subtree=False):
        kind = "memo" if kind == "memo" else "task"
        ids = []
        def walk(x):
            if x == ROOT_ID:
                return
            ids.append(x)
            if subtree:
                for c in self.children(x):
                    walk(c)
        walk(node_id)
        for x in ids:
            n = self.node(x)
            if not n:
                continue
            n["kind"] = kind
            if kind == "memo":
                n["completed"] = False
                n["completedAt"] = None
                n["isToday"] = False
                n["isImportant"] = False
                n["priority"] = None
        self.sort_all_children()

    def move_node(self, node_id, new_parent_id):
        if node_id == ROOT_ID or node_id == new_parent_id:
            return False
        cur = new_parent_id
        while cur:
            if cur == node_id:
                return False
            cur_node = self.node(cur)
            cur = cur_node.get("parentId") if cur_node else None
        node = self.node(node_id)
        new_parent = self.node(new_parent_id)
        if not node or not new_parent:
            return False
        old_parent = self.node(node.get("parentId"))
        if old_parent and node_id in old_parent.get("children", []):
            old_parent["children"].remove(node_id)
        node["parentId"] = new_parent_id
        new_parent.setdefault("children", []).append(node_id)
        self.sort_children(new_parent_id)
        return True


def parse_tree_text(raw, keep_root=True):
    lines = str(raw or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    items = []

    def depth_from_prefix(prefix):
        normalized = prefix.replace("\t", "    ")
        depth = 0
        cursor = 0
        while cursor + 3 < len(normalized):
            chunk = normalized[cursor:cursor + 4]
            if chunk in ("│   ", "    "):
                depth += 1
                cursor += 4
            else:
                break
        return depth

    for line in lines:
        text = line.rstrip()
        if not text.strip():
            continue
        stripped = text.strip()
        for connector in ("├──", "└──"):
            idx = text.find(connector)
            if idx >= 0:
                title = text[idx + len(connector):].strip()
                items.append({"title": title, "depth": depth_from_prefix(text[:idx]) + 1})
                break
        else:
            leading = len(text) - len(text.lstrip(" \t"))
            if stripped.startswith(("- ", "* ", "+ ")):
                items.append({"title": stripped[2:].strip(), "depth": leading // 2})
            else:
                items.append({"title": stripped, "depth": leading // 2})
    if not keep_root and len(items) > 1 and items[0]["depth"] == 0:
        rest_min = min(i["depth"] for i in items[1:])
        if rest_min > 0:
            return [{"title": i["title"], "depth": i["depth"] - 1} for i in items[1:]]
    return items


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x820")
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg"])
        self.store = TaskStore()
        self.current_parent = ROOT_ID
        self.selected_id = None
        self.view_mode = tk.StringVar(value="all")
        self.kind_filter = tk.StringVar(value="all")
        self.show_paste = tk.BooleanVar(value=False)
        self.search_text = tk.StringVar(value="")
        self.current_path_list_id = None
        self.current_date_key = None
        self.dragging_id = None
        self.folder_ids = []
        self.setup_style()
        self.create_widgets()
        self.refresh_all()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Malgun Gothic", 10))
        style.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=("Malgun Gothic", 10))
        style.configure("Title.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Malgun Gothic", 20, "bold"))
        style.configure("Muted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=("Malgun Gothic", 9))
        style.configure("TButton", font=("Malgun Gothic", 9, "bold"), padding=(8, 5), background="#edf3fb", foreground=COLORS["text"])
        style.map("TButton", background=[("active", COLORS["primary_soft"])])
        style.configure("Primary.TButton", background=COLORS["primary"], foreground="#ffffff")
        style.configure("Danger.TButton", background="#ffecec", foreground="#991b1b")
        style.configure("TRadiobutton", background=COLORS["panel"], foreground=COLORS["text"], font=("Malgun Gothic", 9))
        style.configure("TCheckbutton", background=COLORS["panel"], foreground=COLORS["text"], font=("Malgun Gothic", 9))
        style.configure("Treeview", font=("Malgun Gothic", 10), rowheight=30, background="#ffffff", fieldbackground="#ffffff", foreground=COLORS["text"])
        style.configure("Treeview.Heading", font=("Malgun Gothic", 9, "bold"), background="#e7edf6", foreground=COLORS["text"])
        style.map("Treeview", background=[("selected", COLORS["primary"])], foreground=[("selected", "#ffffff")])

    def create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self, padding=10)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text=APP_TITLE, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.search_text).grid(row=0, column=1, sticky="ew", padx=12)
        ttk.Button(top, text="검색", command=self.refresh_tree).grid(row=0, column=2)

        main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        left = ttk.Frame(main, padding=8, style="Panel.TFrame")
        center = ttk.Frame(main, padding=8, style="Panel.TFrame")
        right = ttk.Frame(main, padding=8, style="Panel.TFrame")
        main.add(left, weight=1)
        main.add(center, weight=4)
        main.add(right, weight=2)

        left.columnconfigure(0, weight=1)
        ttk.Label(left, text="보기", style="Panel.TLabel", font=("Malgun Gothic", 11, "bold")).grid(row=0, column=0, sticky="w")
        for i, (label, value) in enumerate([("전체", "all"), ("오늘 할 일", "today"), ("중요", "important"), ("4분할", "matrix"), ("완료", "done")], start=1):
            ttk.Radiobutton(left, text=label, value=value, variable=self.view_mode, command=self.refresh_tree).grid(row=i, column=0, sticky="w", pady=2)
        ttk.Separator(left).grid(row=7, column=0, sticky="ew", pady=8)
        ttk.Label(left, text="종류", style="Panel.TLabel", font=("Malgun Gothic", 11, "bold")).grid(row=8, column=0, sticky="w")
        for i, (label, value) in enumerate([("전체 보기", "all"), ("할 일만", "task"), ("메모만", "memo")], start=9):
            ttk.Radiobutton(left, text=label, value=value, variable=self.kind_filter, command=self.refresh_tree).grid(row=i, column=0, sticky="w", pady=2)
        ttk.Separator(left).grid(row=12, column=0, sticky="ew", pady=8)
        ttk.Button(left, text="JSON 불러오기", command=self.load_json).grid(row=13, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="JSON 저장", command=self.save_json).grid(row=14, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="TXT 내보내기", command=self.export_txt).grid(row=15, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="현재 하위 메모화", command=self.memoize_current).grid(row=16, column=0, sticky="ew", pady=2)

        ttk.Separator(left).grid(row=17, column=0, sticky="ew", pady=8)
        ttk.Label(left, text="날짜", style="Panel.TLabel", font=("Malgun Gothic", 11, "bold")).grid(row=18, column=0, sticky="w")
        self.date_list = tk.Listbox(left, height=7, borderwidth=0, highlightthickness=1, highlightbackground=COLORS["line"], font=("Malgun Gothic", 9))
        self.date_list.grid(row=19, column=0, sticky="ew", pady=4)
        self.date_list.bind("<Double-1>", lambda _e: self.open_date_from_list())

        ttk.Label(left, text="목록", style="Panel.TLabel", font=("Malgun Gothic", 11, "bold")).grid(row=20, column=0, sticky="w", pady=(8, 0))
        self.path_listbox = tk.Listbox(left, height=5, borderwidth=0, highlightthickness=1, highlightbackground=COLORS["line"], font=("Malgun Gothic", 9))
        self.path_listbox.grid(row=21, column=0, sticky="ew", pady=4)
        self.path_listbox.bind("<Double-1>", lambda _e: self.open_path_list())
        self.list_name = ttk.Entry(left)
        self.list_name.grid(row=22, column=0, sticky="ew")
        list_buttons = ttk.Frame(left, style="Panel.TFrame")
        list_buttons.grid(row=23, column=0, sticky="ew", pady=3)
        ttk.Button(list_buttons, text="만들기", command=self.create_path_list).pack(side=tk.LEFT, expand=True, fill="x", padx=(0, 2))
        ttk.Button(list_buttons, text="열기", command=self.open_path_list).pack(side=tk.LEFT, expand=True, fill="x", padx=2)
        ttk.Button(list_buttons, text="삭제", command=self.delete_path_list).pack(side=tk.LEFT, expand=True, fill="x", padx=(2, 0))

        ttk.Label(left, text="폴더", style="Panel.TLabel", font=("Malgun Gothic", 11, "bold")).grid(row=24, column=0, sticky="w", pady=(8, 0))
        self.folder_listbox = tk.Listbox(left, height=5, borderwidth=0, highlightthickness=1, highlightbackground=COLORS["line"], font=("Malgun Gothic", 9))
        self.folder_listbox.grid(row=25, column=0, sticky="ew", pady=4)
        self.folder_listbox.bind("<Double-1>", lambda _e: self.open_folder())
        self.folder_name = ttk.Entry(left)
        self.folder_name.grid(row=26, column=0, sticky="ew")
        folder_buttons = ttk.Frame(left, style="Panel.TFrame")
        folder_buttons.grid(row=27, column=0, sticky="ew", pady=3)
        ttk.Button(folder_buttons, text="만들기", command=self.create_folder).pack(side=tk.LEFT, expand=True, fill="x", padx=(0, 2))
        ttk.Button(folder_buttons, text="열기", command=self.open_folder).pack(side=tk.LEFT, expand=True, fill="x", padx=2)
        ttk.Button(folder_buttons, text="삭제", command=self.delete_folder).pack(side=tk.LEFT, expand=True, fill="x", padx=(2, 0))

        center.columnconfigure(0, weight=1)
        center.rowconfigure(4, weight=1)
        self.path_label = ttk.Label(center, text="루트", foreground="#48607f")
        self.path_label.grid(row=0, column=0, sticky="ew")

        form = ttk.Frame(center)
        form.grid(row=1, column=0, sticky="ew", pady=6)
        form.columnconfigure(0, weight=1)
        self.title_entry = ttk.Entry(form)
        self.title_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.kind_combo = ttk.Combobox(form, values=["할 일", "메모"], state="readonly", width=8)
        self.kind_combo.set("할 일")
        self.kind_combo.grid(row=0, column=1, padx=(0, 6))
        self.priority_entry = ttk.Entry(form, width=14)
        self.priority_entry.grid(row=0, column=2, padx=(0, 6))
        self.priority_entry.insert(0, "우선순위")
        self.today_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, text="오늘", variable=self.today_var).grid(row=0, column=3, padx=(0, 6))
        ttk.Button(form, text="추가", style="Primary.TButton", command=self.add_task).grid(row=0, column=4)
        self.title_entry.bind("<Return>", lambda _e: self.add_task())

        paste_bar = ttk.Frame(center)
        paste_bar.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        ttk.Button(paste_bar, text="트리 붙여넣기", command=self.toggle_paste).pack(side=tk.LEFT)
        self.paste_frame = ttk.Frame(center)
        self.paste_text = tk.Text(self.paste_frame, height=5, wrap="none")
        self.paste_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Button(self.paste_frame, text="붙여넣기 추가", command=self.add_pasted_tree).pack(side=tk.LEFT, padx=6)

        toolbar = ttk.Frame(center)
        toolbar.grid(row=3, column=0, sticky="ew", pady=4)
        for label, cmd in [("루트", self.go_root), ("열기", self.open_selected), ("수정", self.rename_selected), ("삭제", self.delete_selected), ("완료", self.toggle_done), ("중요", self.toggle_important), ("오늘", self.toggle_today), ("메모화", self.memoize_selected), ("할 일화", self.taskify_selected), ("다음 행동", self.next_action), ("목록에 추가", self.add_selected_to_path_list), ("목록에서 제거", self.remove_selected_from_current_list), ("위로 이동", self.move_to_parent)]:
            ttk.Button(toolbar, text=label, command=cmd).pack(side=tk.LEFT, padx=2)

        columns = ("kind", "priority", "today", "important", "children", "created")
        self.tree = ttk.Treeview(center, columns=columns, show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="작업")
        self.tree.heading("kind", text="종류")
        self.tree.heading("priority", text="우선순위")
        self.tree.heading("today", text="오늘")
        self.tree.heading("important", text="중요")
        self.tree.heading("children", text="하위")
        self.tree.heading("created", text="작성")
        self.tree.column("#0", width=420, minwidth=200)
        self.tree.column("kind", width=70, anchor="center")
        self.tree.column("priority", width=80, anchor="center")
        self.tree.column("today", width=55, anchor="center")
        self.tree.column("important", width=55, anchor="center")
        self.tree.column("children", width=55, anchor="center")
        self.tree.column("created", width=130, anchor="center")
        self.tree.grid(row=4, column=0, sticky="nsew")
        self.tree.tag_configure("memo", background=COLORS["memo"])
        self.tree.tag_configure("task", background=COLORS["task"])
        self.tree.tag_configure("done", background=COLORS["done"])
        self.tree.tag_configure("folder", background=COLORS["folder"])
        self.tree.tag_configure("today", background=COLORS["primary_soft"])
        self.tree.tag_configure("important", background=COLORS["important"])
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda _e: self.open_selected())
        self.tree.bind("<Button-3>", lambda _e: self.toggle_done())
        self.tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_drop)
        yscroll = ttk.Scrollbar(center, orient="vertical", command=self.tree.yview)
        yscroll.grid(row=4, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=yscroll.set)

        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        self.detail_label = ttk.Label(right, text="선택 없음", font=("Malgun Gothic", 11, "bold"))
        self.detail_label.grid(row=0, column=0, sticky="ew")
        self.detail_info = ttk.Label(right, text="", foreground="#65728c", wraplength=340)
        self.detail_info.grid(row=1, column=0, sticky="ew", pady=(4, 8))
        self.memo_text = tk.Text(right, wrap="word")
        self.memo_text.grid(row=2, column=0, sticky="nsew")
        ttk.Button(right, text="메모 저장", command=self.save_memo).grid(row=3, column=0, sticky="ew", pady=6)

    def current_kind_default(self):
        parent = self.store.node(self.current_parent)
        return "memo" if parent and parent.get("kind") == "memo" else "task"

    def refresh_all(self):
        self.sync_form_defaults()
        self.refresh_path()
        self.refresh_side_lists()
        self.refresh_tree()
        self.refresh_detail()

    def sync_form_defaults(self):
        kind = self.current_kind_default()
        self.kind_combo.set("메모" if kind == "memo" else "할 일")

    def refresh_path(self):
        if self.view_mode.get() == "pathList" and self.current_path_list_id:
            item = self.store.path_list(self.current_path_list_id)
            self.path_label.config(text=f"저장 목록 > {item.get('title') if item else '목록 없음'}")
            return
        if self.view_mode.get() == "date" and self.current_date_key:
            self.path_label.config(text=f"작성일 > {self.current_date_key}")
            return
        if self.view_mode.get() == "completed-date" and self.current_date_key:
            self.path_label.config(text=f"완료일 > {self.current_date_key}")
            return
        parts = []
        cur = self.store.node(self.current_parent)
        while cur:
            parts.append(cur.get("title", ""))
            pid = cur.get("parentId")
            cur = self.store.node(pid) if pid else None
        self.path_label.config(text=" > ".join(reversed(parts)) or "루트")

    def refresh_side_lists(self):
        self.date_list.delete(0, tk.END)
        created = defaultdict(int)
        completed = defaultdict(int)
        for node in self.store.all_nodes():
            created[(node.get("createdAt") or "")[:10] or "날짜 없음"] += 1
            if node.get("completedAt"):
                completed[(node.get("completedAt") or "")[:10] or "날짜 없음"] += 1
        for key in sorted(created.keys(), reverse=True):
            self.date_list.insert(tk.END, f"작성 {key} ({created[key]})")
        for key in sorted(completed.keys(), reverse=True):
            self.date_list.insert(tk.END, f"완료 {key} ({completed[key]})")

        self.path_listbox.delete(0, tk.END)
        for item in self.store.path_lists:
            self.path_listbox.insert(tk.END, f"{item.get('title')} ({len(item.get('taskIds', []))})")

        self.folder_listbox.delete(0, tk.END)
        self.folder_ids = []
        for node in self.store.folders():
            self.folder_ids.append(node["id"])
            self.folder_listbox.insert(tk.END, node.get("title", "폴더"))

    def row_visible(self, node):
        if not node or node["id"] == ROOT_ID:
            return False
        mode = self.view_mode.get()
        kf = self.kind_filter.get()
        if kf == "task" and node.get("kind") == "memo":
            return False
        if kf == "memo" and node.get("kind") != "memo":
            return False
        if mode == "today" and not node.get("isToday"):
            return False
        if mode == "important" and not node.get("isImportant"):
            return False
        if mode == "done" and not node.get("completed"):
            return False
        if mode in ("today", "important", "matrix") and node.get("kind") == "memo":
            return False
        query = self.search_text.get().strip().lower()
        if query and query not in node.get("title", "").lower() and query not in node.get("memo", "").lower():
            return False
        return True

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        mode = self.view_mode.get()
        if mode == "pathList" and self.current_path_list_id:
            item = self.store.path_list(self.current_path_list_id)
            ids = item.get("taskIds", []) if item else []
            for node_id in sorted(ids, key=self.store.sort_key):
                node = self.store.node(node_id)
                if node and self.row_visible(node):
                    self.insert_node("", node_id, flat=True)
            return
        if mode == "date" and self.current_date_key:
            ids = [n["id"] for n in self.store.all_nodes() if (n.get("createdAt") or "")[:10] == self.current_date_key]
            for node_id in sorted(ids, key=self.store.sort_key):
                node = self.store.node(node_id)
                if node and self.row_visible(node):
                    self.insert_node("", node_id, flat=True)
            return
        if mode == "completed-date" and self.current_date_key:
            ids = [n["id"] for n in self.store.all_nodes() if (n.get("completedAt") or "")[:10] == self.current_date_key]
            for node_id in sorted(ids, key=self.store.sort_key):
                node = self.store.node(node_id)
                if node and self.row_visible(node):
                    self.insert_node("", node_id, flat=True)
            return
        if mode in ("today", "important", "done") or self.search_text.get().strip():
            roots = [n["id"] for n in self.store.nodes.values() if self.row_visible(n)]
            roots.sort(key=self.store.sort_key)
            for node_id in roots:
                self.insert_node("", node_id, flat=True)
        elif mode == "matrix":
            for title, ids in self.matrix_groups():
                parent_iid = self.tree.insert("", "end", text=title, values=("", "", "", "", len(ids), ""), open=True)
                for node_id in ids:
                    self.insert_node(parent_iid, node_id, flat=True)
        else:
            for node_id in self.store.children(self.current_parent):
                node = self.store.node(node_id)
                if self.row_visible(node):
                    self.insert_node("", node_id)

    def matrix_groups(self):
        groups = {"급하고 중요한 일": [], "중요하지만 급하지 않은 일": [], "급하지만 중요하지 않은 일": [], "둘 다 아닌 일": []}
        def walk(x):
            n = self.store.node(x)
            if not n:
                return
            if n.get("kind") != "memo" and not n.get("completed") and self.row_visible(n):
                if n.get("isToday") and n.get("isImportant"):
                    groups["급하고 중요한 일"].append(x)
                elif n.get("isImportant"):
                    groups["중요하지만 급하지 않은 일"].append(x)
                elif n.get("isToday"):
                    groups["급하지만 중요하지 않은 일"].append(x)
                else:
                    groups["둘 다 아닌 일"].append(x)
            for c in self.store.children(x):
                walk(c)
        for c in self.store.children(self.current_parent):
            walk(c)
        return [(k, sorted(v, key=self.store.sort_key)) for k, v in groups.items()]

    def insert_node(self, parent_iid, node_id, flat=False):
        node = self.store.node(node_id)
        if not node:
            return
        created = node.get("createdAt", "")[:16].replace("T", " ")
        values = (
            "폴더" if node.get("isCustomFolder") else ("메모" if node.get("kind") == "memo" else "할 일"),
            "" if node.get("priority") is None else node.get("priority"),
            "Y" if node.get("isToday") else "",
            "Y" if node.get("isImportant") else "",
            len(self.store.children(node_id)),
            created,
        )
        text = node.get("title", "이름 없음")
        if node.get("completed"):
            text = "✓ " + text
        tags = []
        if node.get("isCustomFolder"):
            tags.append("folder")
        elif node.get("completed"):
            tags.append("done")
        elif node.get("kind") == "memo":
            tags.append("memo")
        elif node.get("isToday"):
            tags.append("today")
        elif node.get("isImportant"):
            tags.append("important")
        else:
            tags.append("task")
        iid = self.tree.insert(parent_iid, "end", iid=node_id if not self.tree.exists(node_id) else new_id("view"), text=text, values=values, open=False, tags=tuple(tags))
        if not flat:
            for child_id in self.store.children(node_id):
                child = self.store.node(child_id)
                if child and self.row_visible(child):
                    self.insert_node(iid, child_id)

    def on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            self.selected_id = None
        else:
            iid = sel[0]
            self.selected_id = iid if iid in self.store.nodes else None
        self.refresh_detail()

    def refresh_detail(self):
        node = self.store.node(self.selected_id) if self.selected_id else None
        self.memo_text.delete("1.0", tk.END)
        if not node:
            self.detail_label.config(text="선택 없음")
            self.detail_info.config(text="")
            return
        self.detail_label.config(text=node.get("title", "이름 없음"))
        self.detail_info.config(text=f"종류: {'메모' if node.get('kind') == 'memo' else '할 일'} / 하위: {len(self.store.children(node['id']))}")
        self.memo_text.insert("1.0", node.get("memo", ""))

    def save_and_refresh(self):
        self.store.save_default()
        self.refresh_all()

    def add_task(self):
        title = self.title_entry.get().strip()
        if not title:
            return
        kind = "memo" if self.kind_combo.get() == "메모" else "task"
        priority = parse_priority(self.priority_entry.get())
        self.store.add_node(self.current_parent, title, kind=kind, priority=priority, is_today=self.today_var.get())
        self.title_entry.delete(0, tk.END)
        self.priority_entry.delete(0, tk.END)
        self.today_var.set(False)
        self.save_and_refresh()

    def selected_node(self):
        node = self.store.node(self.selected_id) if self.selected_id else None
        if not node:
            messagebox.showinfo(APP_TITLE, "작업을 선택하세요.")
        return node

    def open_selected(self):
        node = self.selected_node()
        if node:
            self.current_parent = node["id"]
            self.selected_id = None
            self.refresh_all()

    def go_root(self):
        self.current_parent = ROOT_ID
        self.current_path_list_id = None
        self.current_date_key = None
        self.view_mode.set("all")
        self.selected_id = None
        self.refresh_all()

    def rename_selected(self):
        node = self.selected_node()
        if not node:
            return
        title = simpledialog.askstring(APP_TITLE, "이름 수정", initialvalue=node.get("title", ""))
        if title:
            node["title"] = title.strip()
            self.save_and_refresh()

    def delete_selected(self):
        node = self.selected_node()
        if not node:
            return
        if messagebox.askyesno(APP_TITLE, f"'{node.get('title')}'와 하위를 삭제할까요?"):
            self.store.delete_subtree(node["id"])
            self.selected_id = None
            self.save_and_refresh()

    def toggle_done(self):
        node = self.selected_node()
        if not node or node.get("kind") == "memo" or node.get("isCustomFolder"):
            return
        node["completed"] = not node.get("completed")
        node["completedAt"] = now_iso() if node["completed"] else None
        self.save_and_refresh()

    def toggle_today(self):
        node = self.selected_node()
        if not node or node.get("kind") == "memo" or node.get("isCustomFolder"):
            return
        node["isToday"] = not node.get("isToday")
        self.save_and_refresh()

    def toggle_important(self):
        node = self.selected_node()
        if not node or node.get("kind") == "memo" or node.get("isCustomFolder"):
            return
        node["isImportant"] = not node.get("isImportant")
        self.save_and_refresh()

    def memoize_selected(self):
        node = self.selected_node()
        if node:
            self.store.set_kind(node["id"], "memo", subtree=True)
            self.save_and_refresh()

    def taskify_selected(self):
        node = self.selected_node()
        if node:
            self.store.set_kind(node["id"], "task", subtree=False)
            self.save_and_refresh()

    def next_action(self):
        node = self.selected_node()
        if not node or node.get("isCustomFolder"):
            return
        node["kind"] = "task"
        node["completed"] = False
        node["completedAt"] = None
        node["isToday"] = True
        self.save_and_refresh()

    def memoize_current(self):
        if self.current_parent == ROOT_ID:
            messagebox.showwarning(APP_TITLE, "루트 전체 메모화는 막았습니다. 큰 항목 안으로 들어가서 실행하세요.")
            return
        node = self.store.node(self.current_parent)
        if node and messagebox.askyesno(APP_TITLE, f"'{node.get('title')}'와 하위를 전부 메모화할까요?"):
            self.store.set_kind(self.current_parent, "memo", subtree=True)
            self.save_and_refresh()

    def move_to_parent(self):
        node = self.selected_node()
        if not node:
            return
        parent = self.store.node(node.get("parentId"))
        grand = self.store.node(parent.get("parentId")) if parent else None
        if grand and self.store.move_node(node["id"], grand["id"]):
            self.save_and_refresh()

    def save_memo(self):
        node = self.selected_node()
        if not node:
            return
        node["memo"] = self.memo_text.get("1.0", tk.END).rstrip("\n")
        self.save_and_refresh()

    def toggle_paste(self):
        if self.show_paste.get():
            self.paste_frame.grid_forget()
            self.show_paste.set(False)
        else:
            self.paste_frame.grid(row=2, column=0, sticky="ew", pady=(0, 6))
            self.show_paste.set(True)
            self.paste_text.focus_set()

    def add_pasted_tree(self):
        raw = self.paste_text.get("1.0", tk.END)
        items = parse_tree_text(raw, keep_root=True)
        if not items:
            return
        parent_by_depth = {}
        created = []
        for item in items:
            depth = max(0, int(item.get("depth", 0)))
            parent_id = parent_by_depth.get(depth - 1, self.current_parent)
            node_id = self.store.add_node(parent_id, item["title"], kind="task")
            parent_by_depth[depth] = node_id
            for d in list(parent_by_depth.keys()):
                if d > depth:
                    del parent_by_depth[d]
            created.append(node_id)
        if created:
            self.paste_text.delete("1.0", tk.END)
            self.toggle_paste()
            self.save_and_refresh()

    def load_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON or TXT", "*.json *.txt"), ("All", "*.*")])
        if not path:
            return
        try:
            if path.lower().endswith(".json"):
                self.store.load_file(path)
                self.store.save_default()
            else:
                with open(path, "r", encoding="utf-8-sig") as f:
                    self.paste_text.delete("1.0", tk.END)
                    self.paste_text.insert("1.0", f.read())
                if not self.show_paste.get():
                    self.toggle_paste()
            self.current_parent = ROOT_ID
            self.selected_id = None
            self.refresh_all()
        except Exception as e:
            messagebox.showerror(APP_TITLE, str(e))

    def create_path_list(self):
        title = self.list_name.get().strip()
        if not title:
            return
        self.store.add_path_list(title)
        self.list_name.delete(0, tk.END)
        self.save_and_refresh()

    def selected_path_list_id(self):
        idx = self.path_listbox.curselection()
        if not idx:
            return None
        return self.store.path_lists[idx[0]].get("id") if idx[0] < len(self.store.path_lists) else None

    def open_path_list(self):
        list_id = self.selected_path_list_id()
        if not list_id:
            return
        self.current_path_list_id = list_id
        self.current_date_key = None
        self.view_mode.set("pathList")
        self.refresh_all()

    def delete_path_list(self):
        list_id = self.selected_path_list_id()
        if not list_id:
            return
        if messagebox.askyesno(APP_TITLE, "선택한 목록을 삭제할까요? 실제 작업은 삭제되지 않습니다."):
            self.store.state["pathLists"] = [x for x in self.store.path_lists if x.get("id") != list_id]
            if self.current_path_list_id == list_id:
                self.current_path_list_id = None
                self.view_mode.set("all")
            self.save_and_refresh()

    def add_selected_to_path_list(self):
        node = self.selected_node()
        list_id = self.selected_path_list_id()
        if not node or not list_id:
            messagebox.showinfo(APP_TITLE, "작업과 왼쪽 목록을 선택하세요.")
            return
        item = self.store.path_list(list_id)
        if item and node["id"] not in item["taskIds"]:
            item["taskIds"].append(node["id"])
            self.save_and_refresh()

    def remove_selected_from_current_list(self):
        node = self.selected_node()
        if not node or self.view_mode.get() != "pathList" or not self.current_path_list_id:
            return
        item = self.store.path_list(self.current_path_list_id)
        if item:
            item["taskIds"] = [x for x in item.get("taskIds", []) if x != node["id"]]
            self.save_and_refresh()

    def create_folder(self):
        title = self.folder_name.get().strip()
        if not title:
            return
        self.store.add_folder(self.current_parent, title)
        self.folder_name.delete(0, tk.END)
        self.save_and_refresh()

    def selected_folder_id(self):
        idx = self.folder_listbox.curselection()
        if not idx:
            return None
        return self.folder_ids[idx[0]] if idx[0] < len(self.folder_ids) else None

    def open_folder(self):
        folder_id = self.selected_folder_id()
        if folder_id:
            self.current_parent = folder_id
            self.current_path_list_id = None
            self.current_date_key = None
            self.view_mode.set("all")
            self.refresh_all()

    def delete_folder(self):
        folder_id = self.selected_folder_id()
        if folder_id and messagebox.askyesno(APP_TITLE, "선택한 폴더와 안의 작업을 모두 삭제할까요?"):
            self.store.delete_subtree(folder_id)
            self.save_and_refresh()

    def open_date_from_list(self):
        idx = self.date_list.curselection()
        if not idx:
            return
        text = self.date_list.get(idx[0])
        if text.startswith("작성 "):
            self.current_date_key = text.split(" ", 1)[1].split(" (")[0]
            self.view_mode.set("date")
        elif text.startswith("완료 "):
            self.current_date_key = text.split(" ", 1)[1].split(" (")[0]
            self.view_mode.set("completed-date")
        else:
            return
        self.current_path_list_id = None
        self.refresh_all()

    def on_drag_start(self, event):
        iid = self.tree.identify_row(event.y)
        self.dragging_id = iid if iid in self.store.nodes else None

    def on_drag_drop(self, event):
        if not self.dragging_id:
            return
        target = self.tree.identify_row(event.y)
        source = self.dragging_id
        self.dragging_id = None
        if target and target in self.store.nodes and target != source:
            if self.store.move_node(source, target):
                self.save_and_refresh()
        elif self.view_mode.get() == "all":
            if self.store.move_node(source, self.current_parent):
                self.save_and_refresh()

    def save_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            self.store.save_as(path)

    def export_txt(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not path:
            return
        lines = []
        def walk(node_id, prefix=""):
            kids = self.store.children(node_id)
            for i, cid in enumerate(kids):
                n = self.store.node(cid)
                last = i == len(kids) - 1
                lines.append(prefix + ("└── " if last else "├── ") + n.get("title", ""))
                walk(cid, prefix + ("    " if last else "│   "))
        walk(self.current_parent)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def on_close(self):
        self.store.save_default()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
