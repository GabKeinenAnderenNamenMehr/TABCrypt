# -*- coding: utf-8 -*-

import os
import sys
import json
import shutil
import tempfile
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    print("Missing library 'tkinterdnd2'.")
    print("Please install with:  pip install tkinterdnd2")
    sys.exit(1)


# ============================================================
#  CONFIGURATION DEFAULTS
# ============================================================

DEFAULT_PASSWORDS = {
    "ZXRules": "1847022185176208962489145797518470221851762089624891457975334454FADSFASDF45345",
    "ZXStrings": "1847022185176208962489145797518470221851762089624891457975334454FADSFASDF45345",
    "ZXCampaign": "1688788812-163327433-2005584771",
    "ZXCampaignStrings": "",
}

DEFAULT_ZIP_PARAMS = {
    "mx": "9",
    "mm": "Deflate",
    "md": "32k",
    "mfb": "128",
}

DELETE_ARCHIVE_AFTER_UNPACK_DEFAULT = True

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "tabcrypt_config.json"
)

ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


# ============================================================
#  HELPER FUNCTIONS
# ============================================================

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def is_zip_file(path):
    try:
        with open(path, "rb") as f:
            header = f.read(4)
        return header in ZIP_SIGNATURES
    except Exception:
        return False


# ============================================================
#  MAIN APPLICATION
# ============================================================

class DatCryptApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TABCrypt - They Are Billions modding tool")
        self.root.geometry("640x520")
        self.root.minsize(520, 400)

        cfg = load_config()
        self.passwords = dict(DEFAULT_PASSWORDS)
        self.passwords.update(cfg.get("passwords", {}))
        self.zip_params = dict(DEFAULT_ZIP_PARAMS)
        self.zip_params.update(cfg.get("zip_params", {}))
        self.sevenzip_path = cfg.get("sevenzip_path")

        self.delete_var = tk.BooleanVar(value=DELETE_ARCHIVE_AFTER_UNPACK_DEFAULT)

        self._build_menu()
        self._build_ui()

        self.root.after(100, self.ensure_sevenzip)

    # --------------------------------------------------------
    # SAVE CONFIGURATION
    # --------------------------------------------------------
    def save_all_config(self):
        cfg = load_config()
        cfg["sevenzip_path"] = self.sevenzip_path
        cfg["passwords"] = self.passwords
        cfg["zip_params"] = self.zip_params
        save_config(cfg)

    # --------------------------------------------------------
    # MENU
    # --------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open file...", command=self.open_file_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(
            label="Passwords...", command=lambda: self.open_settings(tab=0)
        )
        settings_menu.add_command(
            label="ZIP Parameters...", command=lambda: self.open_settings(tab=1)
        )
        settings_menu.add_separator()
        settings_menu.add_command(label="7z.exe Path...", command=self.choose_sevenzip)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        self.root.config(menu=menubar)

    def open_file_dialog(self):
        paths = filedialog.askopenfilenames(
            title="Select file(s)",
            filetypes=[(".dat files", "*.dat"), ("All files", "*.*")],
            parent=self.root,
        )
        for p in paths:
            self.process_path(p)

    # --------------------------------------------------------
    # SETTINGS DIALOG
    # --------------------------------------------------------
    def open_settings(self, tab=0):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("440x380")
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Tab 1: Passwords ---
        pw_frame = ttk.Frame(notebook, padding=10)
        notebook.add(pw_frame, text="Passwords")

        pw_entries = {}
        names_sorted = sorted(self.passwords.keys())
        for i, name in enumerate(names_sorted):
            ttk.Label(pw_frame, text=name + ":").grid(
                row=i, column=0, sticky="w", padx=5, pady=6
            )
            var = tk.StringVar(value=self.passwords.get(name, ""))
            entry = ttk.Entry(pw_frame, textvariable=var, width=28)
            entry.grid(row=i, column=1, padx=5, pady=6, sticky="ew")
            pw_entries[name] = var
        pw_frame.columnconfigure(1, weight=1)

        hint = ttk.Label(
            pw_frame,
            text=(
                "Note: ZXRules and ZXStrings can share the same\n"
                "password - just enter the same value for both."
            ),
            foreground="#555555",
            justify="left",
        )
        hint.grid(
            row=len(names_sorted), column=0, columnspan=2,
            sticky="w", padx=5, pady=(14, 0),
        )

        # --- Tab 2: ZIP Parameters ---
        zip_frame = ttk.Frame(notebook, padding=10)
        notebook.add(zip_frame, text="ZIP Parameters")

        ttk.Label(zip_frame, text="Compression level (0-9):").grid(
            row=0, column=0, sticky="w", padx=5, pady=8
        )
        mx_var = tk.StringVar(value=str(self.zip_params.get("mx", "9")))
        ttk.Spinbox(zip_frame, from_=0, to=9, textvariable=mx_var, width=10).grid(
            row=0, column=1, padx=5, pady=8, sticky="w"
        )

        ttk.Label(zip_frame, text="Compression method:").grid(
            row=1, column=0, sticky="w", padx=5, pady=8
        )
        mm_var = tk.StringVar(value=self.zip_params.get("mm", "Deflate"))
        ttk.Combobox(
            zip_frame, textvariable=mm_var, width=17, state="readonly",
            values=["Deflate", "Deflate64", "Copy", "BZip2", "LZMA", "PPMd"],
        ).grid(row=1, column=1, padx=5, pady=8, sticky="w")

        ttk.Label(zip_frame, text="Dictionary size:").grid(
            row=2, column=0, sticky="w", padx=5, pady=8
        )
        md_var = tk.StringVar(value=self.zip_params.get("md", "32k"))
        ttk.Entry(zip_frame, textvariable=md_var, width=12).grid(
            row=2, column=1, padx=5, pady=8, sticky="w"
        )

        ttk.Label(zip_frame, text="Word size (fast bytes):").grid(
            row=3, column=0, sticky="w", padx=5, pady=8
        )
        mfb_var = tk.StringVar(value=str(self.zip_params.get("mfb", "128")))
        ttk.Entry(zip_frame, textvariable=mfb_var, width=12).grid(
            row=3, column=1, padx=5, pady=8, sticky="w"
        )

        zip_frame.columnconfigure(1, weight=1)

        notebook.select(tab)

        # --- Buttons ---
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        def on_save():
            for name, var in pw_entries.items():
                self.passwords[name] = var.get()
            self.zip_params["mx"] = mx_var.get().strip() or "9"
            self.zip_params["mm"] = mm_var.get().strip() or "Deflate"
            self.zip_params["md"] = md_var.get().strip() or "32k"
            self.zip_params["mfb"] = mfb_var.get().strip() or "128"
            self.save_all_config()
            self.log("Settings saved.")
            win.destroy()

        ttk.Button(btn_frame, text="Save", command=on_save).pack(
            side="right", padx=(6, 0)
        )
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="right")

    # --------------------------------------------------------
    # UI LAYOUT
    # --------------------------------------------------------
    def _build_ui(self):
        pad = {"padx": 10, "pady": 8}

        header = ttk.Label(
            self.root,
            text="Drop file(s) below or use 'File -> Open file...' "
                 "to automatically encrypt/decrypt them.",
            justify="center",
        )
        header.pack(fill="x", **pad)

        self.drop_frame = tk.Label(
            self.root,
            text="\u21E9  Drop files here  \u21E9",
            relief="groove",
            borderwidth=2,
            bg="#f0f0f0",
            fg="#333333",
            font=("Segoe UI", 12, "bold"),
            height=6,
        )
        self.drop_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind("<<Drop>>", self.on_drop)

        options_frame = ttk.Frame(self.root)
        options_frame.pack(fill="x", padx=10)

        chk = ttk.Checkbutton(
            options_frame,
            text="Delete archive after successful unpacking",
            variable=self.delete_var,
        )
        chk.pack(side="left")

        log_label = ttk.Label(self.root, text="Log:")
        log_label.pack(fill="x", padx=10, pady=(8, 0))

        self.log_widget = scrolledtext.ScrolledText(
            self.root, height=14, state="disabled", wrap="word"
        )
        self.log_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        clear_btn = ttk.Button(self.root, text="Clear log", command=self.clear_log)
        clear_btn.pack(pady=(0, 10))

    def log(self, text):
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", text + "\n")
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")

    def clear_log(self):
        self.log_widget.configure(state="normal")
        self.log_widget.delete("1.0", "end")
        self.log_widget.configure(state="disabled")

    # --------------------------------------------------------
    # LOCATE 7-ZIP
    # --------------------------------------------------------
    def ensure_sevenzip(self):
        if self.sevenzip_path and os.path.isfile(self.sevenzip_path):
            self.log(f"7-Zip found: {self.sevenzip_path}")
            return

        candidates = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "7z.exe"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                self.sevenzip_path = c
                self.save_all_config()
                self.log(f"7-Zip found: {c}")
                return

        messagebox.showinfo(
            "7-Zip not found",
            "Please select the 7z.exe file manually\n",
            parent=self.root,
        )
        self.choose_sevenzip()

    def choose_sevenzip(self):
        chosen = filedialog.askopenfilename(
            title="Select 7z.exe",
            filetypes=[("7z.exe", "7z.exe"), ("All files", "*.*")],
            parent=self.root,
        )
        if chosen:
            self.sevenzip_path = chosen
            self.save_all_config()
            self.log(f"7-Zip set: {chosen}")
        elif not self.sevenzip_path:
            self.log("WARNING: Without 7z.exe, packing/unpacking is not possible.")

    # --------------------------------------------------------
    # DRAG AND DROP
    # --------------------------------------------------------
    def on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        for p in paths:
            if os.path.isdir(p):
                self.log(f"Folders are not supported, skipping: {p}")
                continue
            self.process_path(p)

    def process_path(self, path):
        if not self.sevenzip_path:
            messagebox.showerror("Error", "7z.exe has not been configured.")
            return
        if not os.path.isfile(path):
            self.log(f"File not found: {path}")
            return

        self.log(f"--- Processing: {path}")
        if is_zip_file(path):
            self.unpack_file(path)
        else:
            self.pack_file(path)

    # --------------------------------------------------------
    # BASE NAME RESOLUTION
    # --------------------------------------------------------
    def resolve_base_name(self, filename):
        base_no_ext = os.path.splitext(filename)[0]
        for name in sorted(self.passwords.keys(), key=len, reverse=True):
            if base_no_ext.lower().startswith(name.lower()):
                return name
        return None

    # --------------------------------------------------------
    # COLLISION-SAFE TARGET NAMES
    # --------------------------------------------------------
    def find_available_suffixed_name(self, folder, base_name, tag):
        n = 1
        while True:
            candidate = os.path.join(folder, f"{base_name}_{tag}_({n}).dat")
            if not os.path.exists(candidate):
                return candidate
            n += 1

    def place_result_file(self, src, folder, base_name, tag):
        canonical_path = os.path.join(folder, base_name + ".dat")
        try:
            os.replace(src, canonical_path)
            return canonical_path
        except OSError:
            alt_path = self.find_available_suffixed_name(folder, base_name, tag)
            try:
                shutil.move(src, alt_path)
            except Exception as e:
                self.log(f"ERROR: Could not place result file: {e}")
                return None
            self.log(
                f"Note: '{os.path.basename(canonical_path)}' is currently not "
                "writable (e.g. still open in another program) - falling "
                f"back to '{os.path.basename(alt_path)}'."
            )
            return alt_path

    # --------------------------------------------------------
    # 7-ZIP INVOCATION
    # --------------------------------------------------------
    # --------------------------------------------------------
    # BUILD ZIP ARGS
    # --------------------------------------------------------
    def build_zip_args(self):
        p = self.zip_params
        method = p.get("mm", "Deflate")
        method_upper = method.strip().upper()

        args = ["-tzip", f"-mx={p.get('mx', '9')}", f"-mm={method}"]

        # -md (dictionary size) is only a valid switch for LZMA/LZMA2/PPMd.
        # Deflate/Deflate64/Copy/BZip2 use a fixed dictionary size and 7-Zip
        # errors out ("Invalid parameter") if -md is passed for them.
        if method_upper in ("LZMA", "LZMA2", "PPMD") and p.get("md"):
            args.append(f"-md={p['md']}")

        # -mfb (word size / fast bytes) is valid for Deflate/Deflate64 and
        # the LZMA family/PPMd, but not for Copy or BZip2.
        if method_upper in ("DEFLATE", "DEFLATE64", "LZMA", "LZMA2", "PPMD") and p.get("mfb"):
            args.append(f"-mfb={p['mfb']}")

        return args

    def run_7z(self, cmd):
        try:
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW
            proc = subprocess.run(
                cmd, capture_output=True, text=True, creationflags=creationflags
            )
            output = (proc.stdout or "").strip()
            error = (proc.stderr or "").strip()
            if output:
                self.log(output)
            if proc.returncode != 0 and error:
                self.log(error)
            return proc.returncode
        except Exception as e:
            self.log(f"Error calling 7z: {e}")
            return -1

    # --------------------------------------------------------
    # PACKING
    # --------------------------------------------------------
    def pack_file(self, path):
        filename = os.path.basename(path)
        base_name = self.resolve_base_name(filename)
        if base_name is None:
            self.log(
                f"ERROR: Could not match '{filename}' to a known base name. "
                "Skipping."
            )
            return

        password = self.passwords.get(base_name)
        if not password:
            self.log(
                f"ERROR: No password set for '{base_name}' "
                "(see Settings -> Passwords...). Skipping."
            )
            return

        folder = os.path.dirname(os.path.abspath(path)) or "."
        canonical_name = base_name + ".dat"
        is_exact_basename = os.path.normcase(filename) == os.path.normcase(canonical_name)

        tmp_dir = tempfile.mkdtemp(prefix="datcrypt_")
        try:
            work_copy = os.path.join(tmp_dir, canonical_name)
            try:
                shutil.copy2(path, work_copy)
            except Exception as e:
                self.log(f"ERROR: Could not copy file: {e}")
                return

            tmp_archive = os.path.join(tmp_dir, base_name + ".__tmp__.zip")
            cmd = (
                [self.sevenzip_path, "a"]
                + self.build_zip_args()
                + [f"-p{password}", "-y", tmp_archive, work_copy]
            )
            rc = self.run_7z(cmd)
            if rc != 0 or not os.path.isfile(tmp_archive):
                self.log(f"ERROR while packing: {filename}")
                return

            if is_exact_basename:
                target_path = self.find_available_suffixed_name(
                    folder, base_name, "packaged"
                )
                try:
                    shutil.move(tmp_archive, target_path)
                except Exception as e:
                    self.log(f"ERROR: Could not place archive: {e}")
                    return
                self.log(
                    f"Note: '{filename}' already had the base name - archive "
                    f"was saved as '{os.path.basename(target_path)}' to avoid "
                    "overwriting the original."
                )
            else:
                target_path = self.place_result_file(
                    tmp_archive, folder, base_name, "packaged"
                )
                if target_path is None:
                    return

            self.log(
                f"OK packed: '{os.path.basename(target_path)}' "
                f"(password group: {base_name})"
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # --------------------------------------------------------
    # UNPACKING
    # --------------------------------------------------------
    def unpack_file(self, path):
        filename = os.path.basename(path)
        base_name = self.resolve_base_name(filename)
        if base_name is None:
            self.log(
                f"ERROR: Could not match '{filename}' to a known base name. "
                "Skipping."
            )
            return

        password = self.passwords.get(base_name)
        if not password:
            self.log(
                f"ERROR: No password set for '{base_name}' "
                "(see Settings -> Passwords...). Skipping."
            )
            return

        folder = os.path.dirname(os.path.abspath(path)) or "."
        abs_path = os.path.abspath(path)
        canonical_path = os.path.join(folder, base_name + ".dat")
        archive_is_canonical = os.path.normcase(abs_path) == os.path.normcase(
            os.path.abspath(canonical_path)
        )
        delete_archive = self.delete_var.get()

        tmp_dir = tempfile.mkdtemp(prefix="datcrypt_")
        try:
            cmd = [self.sevenzip_path, "x", f"-p{password}", "-y", f"-o{tmp_dir}", path]
            rc = self.run_7z(cmd)
            if rc != 0:
                self.log(
                    f"ERROR while unpacking '{path}' "
                    "(wrong password or corrupted archive?)."
                )
                return

            extracted_files = [
                os.path.join(tmp_dir, f)
                for f in os.listdir(tmp_dir)
                if os.path.isfile(os.path.join(tmp_dir, f))
            ]
            if not extracted_files:
                self.log(f"ERROR: Archive '{filename}' contained no file.")
                return
            if len(extracted_files) > 1:
                self.log(
                    f"WARNING: Archive '{filename}' contained multiple files, "
                    "only the first one will be used."
                )
            extracted_file = extracted_files[0]

            if archive_is_canonical and not delete_archive:
                target_path = self.find_available_suffixed_name(
                    folder, base_name, "unpacked"
                )
                try:
                    shutil.move(extracted_file, target_path)
                except Exception as e:
                    self.log(f"ERROR: Could not place result file: {e}")
                    return
                self.log(
                    f"Note: keeping original archive '{filename}' intact - "
                    f"unpacked file saved as '{os.path.basename(target_path)}'."
                )
            else:
                target_path = self.place_result_file(
                    extracted_file, folder, base_name, "unpacked"
                )
                if target_path is None:
                    return

            self.log(
                f"OK unpacked: '{os.path.basename(target_path)}' "
                f"(password group: {base_name})"
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        if delete_archive and os.path.abspath(target_path) != abs_path:
            try:
                os.remove(path)
            except Exception as e:
                self.log(f"Warning: Could not delete archive: {e}")


def main():
    root = TkinterDnD.Tk()
    app = DatCryptApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
