# -*- mode: python ; coding: utf-8 -*-
import os

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

project_dir = os.path.abspath(os.path.dirname(SPEC))
grc_backend_dir = os.path.join(project_dir, "grc_backend")
grc_frontend_dir = os.path.join(project_dir, "grc_frontend")
entry_script = os.path.join(grc_backend_dir, "onprem_launcher.py")

datas = []

# Backend env and project files
if os.path.exists(os.path.join(grc_backend_dir, ".env")):
    datas.append((os.path.join(grc_backend_dir, ".env"), "grc_backend"))
if os.path.exists(os.path.join(grc_backend_dir, ".env.production")):
    datas.append((os.path.join(grc_backend_dir, ".env.production"), "grc_backend"))
if os.path.exists(os.path.join(grc_backend_dir, "manage.py")):
    datas.append((os.path.join(grc_backend_dir, "manage.py"), "grc_backend"))
if os.path.isdir(os.path.join(grc_backend_dir, "backend")):
    datas.append((os.path.join(grc_backend_dir, "backend"), "grc_backend/backend"))
if os.path.isdir(os.path.join(grc_backend_dir, "grc")):
    datas.append((os.path.join(grc_backend_dir, "grc"), "grc_backend/grc"))
if os.path.isdir(os.path.join(grc_backend_dir, "tprm_backend")):
    datas.append((os.path.join(grc_backend_dir, "tprm_backend"), "grc_backend/tprm_backend"))

# Frontend files required for `npm run dev:all`
if os.path.exists(os.path.join(grc_frontend_dir, "package.json")):
    datas.append((os.path.join(grc_frontend_dir, "package.json"), "grc_frontend"))
if os.path.exists(os.path.join(grc_frontend_dir, "package-lock.json")):
    datas.append((os.path.join(grc_frontend_dir, "package-lock.json"), "grc_frontend"))
if os.path.isdir(os.path.join(grc_frontend_dir, "src")):
    datas.append((os.path.join(grc_frontend_dir, "src"), "grc_frontend/src"))
if os.path.isdir(os.path.join(grc_frontend_dir, "vue")):
    datas.append((os.path.join(grc_frontend_dir, "vue"), "grc_frontend/vue"))
if os.path.isdir(os.path.join(grc_frontend_dir, "public")):
    datas.append((os.path.join(grc_frontend_dir, "public"), "grc_frontend/public"))
if os.path.isdir(os.path.join(grc_frontend_dir, "tprm_frontend")):
    datas.append((os.path.join(grc_frontend_dir, "tprm_frontend"), "grc_frontend/tprm_frontend"))

a = Analysis(
    [entry_script],
    pathex=[project_dir, grc_backend_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="onprem_grc_stack",
    debug=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="onprem_grc_stack",
)

