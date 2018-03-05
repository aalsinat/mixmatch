# -*- mode: python -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Users\\aalsinat\\Development\\mktinabox\\mixmatch'],
             binaries=[],
             datas=[('mixmatch\\actions', 'mixmatch\\actions')],
             hiddenimports=['json', 'wx', 'zeep', 'urllib3'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='mixmatch',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='favicon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='mixmatch')
