# -*- coding: utf-8 -*-
"""
OBJ 导入 Unity 工具
功能：选择 OBJ 文件（及关联的 MTL / 贴图文件），复制到指定 Unity 项目的 Assets 目录。
Unity 在检测到 Assets 目录中的新 OBJ 文件后会自动导入为模型资源。
"""

import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# 常见贴图扩展名
TEXTURE_EXTS = {".png", ".jpg", ".jpeg", ".tga", ".bmp", ".tif", ".tiff",
                ".psd", ".exr", ".hdr"}


def find_mtl_for_obj(obj_path):
    """读取 OBJ 文件，找出其中引用的 .mtl 文件名列表。"""
    mtl_names = []
    try:
        with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.lower().startswith("mtllib"):
                    parts = line.split()
                    if len(parts) >= 2:
                        mtl_names.append(parts[1])
    except Exception:
        pass
    return mtl_names


def find_textures_in_mtl(mtl_path):
    """读取 MTL 文件，找出其中引用的贴图文件名列表。"""
    tex_names = []
    try:
        with open(mtl_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                low = line.lower()
                # map_Kd / map_Ks / map_Ka / map_bump / bump / disp / decal / etc.
                if low.startswith("map_") or low.startswith("bump") or low.startswith("disp"):
                    parts = line.split()
                    if len(parts) >= 2:
                        tex_names.append(parts[-1])
    except Exception:
        pass
    return tex_names


def collect_dependencies(obj_path, log):
    """收集 OBJ 同目录下的 MTL 和贴图文件。返回要复制的源文件路径列表。"""
    src_dir = os.path.dirname(obj_path)
    deps = []

    mtl_names = find_mtl_for_obj(obj_path)
    for mname in mtl_names:
        mpath = os.path.join(src_dir, mname)
        if os.path.isfile(mpath):
            deps.append(mpath)
            log(f"  发现材质文件: {mname}")
            # 从 MTL 找贴图
            for tname in find_textures_in_mtl(mpath):
                tpath = os.path.join(src_dir, tname)
                if os.path.isfile(tpath):
                    deps.append(tpath)
                    log(f"  发现贴图: {tname}")
                else:
                    log(f"  [警告] MTL 引用的贴图未找到: {tname}")
        else:
            log(f"  [警告] OBJ 引用的 MTL 未找到: {mname}")

    return deps


class ObjToUnityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OBJ 导入 Unity 工具")
        self.root.geometry("720x520")
        self.root.minsize(680, 480)

        self.obj_paths = []
        self.unity_project = tk.StringVar()
        self.target_subfolder = tk.StringVar(value="ImportedModels")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # --- OBJ 文件选择 ---
        frm_obj = ttk.LabelFrame(self.root, text="1. 选择 OBJ 文件")
        frm_obj.pack(fill="x", **pad)

        row1 = ttk.Frame(frm_obj)
        row1.pack(fill="x", padx=8, pady=6)
        ttk.Button(row1, text="添加 OBJ 文件...", command=self.add_obj).pack(side="left")
        ttk.Button(row1, text="清空列表", command=self.clear_obj).pack(side="left", padx=6)

        self.lst_obj = tk.Listbox(frm_obj, height=5, selectmode="extended")
        self.lst_obj.pack(fill="x", padx=8, pady=(0, 6))

        # --- Unity 项目选择 ---
        frm_proj = ttk.LabelFrame(self.root, text="2. 选择 Unity 项目（包含 Assets 文件夹）")
        frm_proj.pack(fill="x", **pad)

        row2 = ttk.Frame(frm_proj)
        row2.pack(fill="x", padx=8, pady=6)
        ttk.Entry(row2, textvariable=self.unity_project).pack(
            side="left", fill="x", expand=True)
        ttk.Button(row2, text="浏览...", command=self.pick_project).pack(side="left", padx=6)

        row2b = ttk.Frame(frm_proj)
        row2b.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Label(row2b, text="Assets 内目标子文件夹:").pack(side="left")
        ttk.Entry(row2b, textvariable=self.target_subfolder, width=30).pack(
            side="left", padx=6)

        # --- 导入按钮 ---
        frm_btn = ttk.Frame(self.root)
        frm_btn.pack(fill="x", **pad)
        self.btn_import = ttk.Button(frm_btn, text="开始导入到 Unity", command=self.do_import)
        self.btn_import.pack(side="left")
        self.progress = ttk.Progressbar(frm_btn, mode="determinate", length=300)
        self.progress.pack(side="right")

        # --- 日志 ---
        frm_log = ttk.LabelFrame(self.root, text="日志")
        frm_log.pack(fill="both", expand=True, **pad)
        self.txt_log = tk.Text(frm_log, height=10, state="disabled", wrap="word")
        self.txt_log.pack(fill="both", expand=True, padx=8, pady=6)

    # ---------- 事件 ----------
    def add_obj(self):
        files = filedialog.askopenfilenames(
            title="选择 OBJ 文件",
            filetypes=[("Wavefront OBJ", "*.obj"), ("所有文件", "*.*")])
        for f in files:
            if f not in self.obj_paths:
                self.obj_paths.append(f)
                self.lst_obj.insert("end", f)

    def clear_obj(self):
        self.obj_paths.clear()
        self.lst_obj.delete(0, "end")

    def pick_project(self):
        d = filedialog.askdirectory(title="选择 Unity 项目根目录")
        if d:
            self.unity_project.set(d)

    def log(self, msg):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")
        self.root.update_idletasks()

    def do_import(self):
        if not self.obj_paths:
            messagebox.showwarning("提示", "请先添加至少一个 OBJ 文件。")
            return

        proj = self.unity_project.get().strip()
        if not proj or not os.path.isdir(proj):
            messagebox.showerror("错误", "请选择有效的 Unity 项目目录。")
            return

        assets_dir = os.path.join(proj, "Assets")
        if not os.path.isdir(assets_dir):
            messagebox.showerror("错误",
                "所选目录下没有 Assets 文件夹。\n请选择 Unity 项目根目录（即包含 Assets 文件夹的目录）。")
            return

        sub = self.target_subfolder.get().strip().strip("/\\")
        target_dir = os.path.join(assets_dir, sub) if sub else assets_dir
        os.makedirs(target_dir, exist_ok=True)

        self.btn_import.configure(state="disabled")
        threading.Thread(target=self._import_worker,
                         args=(list(self.obj_paths), target_dir), daemon=True).start()

    def _import_worker(self, obj_list, target_dir):
        try:
            self.log(f"目标目录: {target_dir}")
            total = len(obj_list)
            self.progress.configure(maximum=total, value=0)

            copied_files = set()
            for i, obj_path in enumerate(obj_list, 1):
                self.log(f"\n[{i}/{total}] 处理: {os.path.basename(obj_path)}")

                # 收集依赖
                deps = collect_dependencies(obj_path, self.log)

                # 复制 OBJ
                dest_obj = os.path.join(target_dir, os.path.basename(obj_path))
                shutil.copy2(obj_path, dest_obj)
                copied_files.add(dest_obj)
                self.log(f"  已复制: {os.path.basename(dest_obj)}")

                # 复制依赖（MTL / 贴图）
                for dep in deps:
                    dep_name = os.path.basename(dep)
                    dest_dep = os.path.join(target_dir, dep_name)
                    if not os.path.isfile(dest_dep):
                        shutil.copy2(dep, dest_dep)
                        self.log(f"  已复制: {dep_name}")
                    else:
                        self.log(f"  已存在，跳过: {dep_name}")

                self.progress.configure(value=i)

            self.log("\n========================================")
            self.log("导入完成！")
            self.log(f"共复制 {len(copied_files)} 个 OBJ 文件及其关联资源到:")
            self.log(target_dir)
            self.log("\n请切换到 Unity 窗口，Unity 将自动检测并导入新资源。")
            messagebox.showinfo("完成",
                f"成功导入 {len(copied_files)} 个模型！\n\n请切换到 Unity 窗口查看自动导入的资源。")
        except Exception as e:
            self.log(f"[错误] {e}")
            messagebox.showerror("导入失败", str(e))
        finally:
            self.btn_import.configure(state="normal")


def main():
    root = tk.Tk()
    try:
        # 现代主题
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    ObjToUnityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
