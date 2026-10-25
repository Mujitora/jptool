# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

manga_datas, manga_binaries, manga_hiddenimports = collect_all("manga_ocr")
unidic_datas, unidic_binaries, unidic_hiddenimports = collect_all("unidic_lite")
transformers_hiddenimports = [
    "transformers.models.bert_japanese.tokenization_bert_japanese",
    "transformers.models.bert.tokenization_bert",
    "transformers.models.gpt2.modeling_gpt2",
    "transformers.models.vision_encoder_decoder.modeling_vision_encoder_decoder",
    "transformers.models.vit.modeling_vit",
]


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=manga_binaries + unidic_binaries,
    datas=[("data/jmdict.json", "data"), *manga_datas, *unidic_datas],
    hiddenimports=manga_hiddenimports + transformers_hiddenimports + unidic_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    [],
    name="JPTool",
    exclude_binaries=True,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["data/tori.ico"],
)

collect = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="JPTool",
)
