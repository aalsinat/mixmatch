# -*- mode: python -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Users\\alexa\\Development\\mktinabox\\source\\mixmatch'],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          name='mixmatch',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , version='version.rc' , icon='favicon.ico')
