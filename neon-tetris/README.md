# 炫彩俄羅斯方塊 (Neon Tetris)

## Windows EXE 打包方法

在 Windows 電腦上執行以下指令：

```cmd
# 1. 安裝 Python (如未安裝)
# https://www.python.org/downloads/

# 2. 安裝依賴
pip install pygame pyinstaller

# 3. 下載代碼並進入目錄
# 將 neon_tetris.py 放到資料夾

# 4. 打包成 EXE
pyinstaller --onefile --name NeonTetris neon_tetris.py

# 5. 找到 EXE
# dist\NeonTetris.exe
```

## 直接下載 (Mac)
https://github.com/hkcforai/neon-tetris/releases/download/v1.0.0/NeonTetris

## 操作說明
- ← → : 移動
- ↓ : 加速
- ↑ / X : 旋轉
- 空格 : 硬下落
- P : 暫停
