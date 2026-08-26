# ERPNext 本機 Demo 部署

這個資料夾包含在 Windows 電腦上快速部署一套本機 ERPNext（供客戶 demo 用）所需的最小檔案組合。完整安裝流程（含 WSL2、Docker Desktop 的詳細步驟）可參考本次對話紀錄；這裡只列出在**已經裝好前置需求的電腦上**要怎麼重新部署。

## 前置需求（在新電腦上，跑腳本之前要先裝好）

1. **WSL2**
   - 系統管理員權限開 PowerShell，執行 `wsl --install`
   - 裝完需要重開機
   - 重開機後，第一次啟動 Ubuntu 會要求設定一組 Linux 使用者帳密（跟 Windows 帳號無關）

2. **Docker Desktop**
   - 到 https://www.docker.com/products/docker-desktop/ 下載安裝（Windows AMD64 版，多數 PC 適用）
   - 安裝時選 **Per-user installation**（用 WSL2 backend，不需要系統管理員密碼）
   - 安裝完打開 Docker Desktop，等左下角顯示 **Engine running**
   - 進 Settings → Resources → WSL Integration，確認你的 Linux 發行版（例如 Ubuntu）有打勾

3. **cloudflared**（只有需要「產生對外連結給客戶」時才需要）
   ```powershell
   winget install --id Cloudflare.cloudflared -e
   ```

4. **git**（用來 clone 這個 repo，多數開發機應該已經有）

## 部署步驟

1. Clone 這個 repo，進到 `erpnext-deploy` 資料夾
2. PowerShell 執行原則若擋住腳本，用以下其中一種方式執行：
   ```powershell
   # 方式一：只跑這一次
   powershell -ExecutionPolicy Bypass -File .\start-demo.ps1

   # 方式二：永久允許本機腳本（僅影響目前 Windows 帳號）
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   .\start-demo.ps1
   ```
3. 腳本會自動：確認/啟動 Docker Desktop → `docker compose -f pwd.yml up -d` 啟動 ERPNext → 建立 Cloudflare quick tunnel → 印出對外連結
4. 第一次啟動要等 ERPNext 建站（約 1-2 分鐘），之後開關就很快

## 登入資訊

- 帳號：`Administrator`
- 密碼：**預設是 `admin`**，第一次部署完成後請務必立刻修改：
  ```powershell
  docker compose -f pwd.yml exec backend bench --site frontend set-admin-password "你的新密碼"
  ```
  這組新密碼只存在這台電腦本機的資料庫 volume 裡，**不會**寫進這個 git repo，請自行另外保存（例如存在本機的一個不會被 commit 的檔案）。

## 匯入 13 倉庫採購入庫測試假資料

專案內建自動化假資料生成腳本（對齊 Demo 系統的 13 倉庫、12 種電子零組件與 14 筆採購入庫單）：

```powershell
# 將腳本複製到容器並執行
docker compose -f pwd.yml cp create_mock_purchase_receipts.py backend:/home/frappe/frappe-bench/sites/
docker compose -f pwd.yml exec -w /home/frappe/frappe-bench/sites backend ../env/bin/python create_mock_purchase_receipts.py
```

執行後會自動建立：
- **13 倉庫**：A 倉 ~ M 倉
- **供應商**：華誠電子、立揚科技、泓宇通訊、剑隆電子、元捷資訊、冠鑫材料
- **料號主檔**：MLCC、XTAL、MCU、SSD、TVS、GDT 等 12 種料號
- **採購入庫單 (Purchase Receipt)**：14 筆已過帳入庫單據與對應庫存

## 關閉 Demo

```powershell
.\stop-demo.ps1                  # 只關閉對外連結，容器繼續跑（本機 http://localhost:8080 仍可用）
.\stop-demo.ps1 -StopContainers  # 連容器一起關閉
```

## 注意事項

- 這是**評估用 demo 部署**（來自 [frappe_docker](https://github.com/frappe/frappe_docker) 的 `pwd.yml` 單檔案 demo 設定），不是正式生產環境
- 資料庫是 **MariaDB**，資料存在 Docker named volume（`sites`、`db-data` 等），跟這個資料夾的位置無關，砍掉資料夾不會動到資料，但 `docker compose down -v` 會清空 volume、等於重置所有資料，請小心使用
- Cloudflare quick tunnel 是免帳號、免費的臨時通道，**每次啟動網址都會不同**，且沒有正式的 SLA 保證，只適合短期 demo，不適合長期正式對外服務
- 對外連結開著的期間，任何拿到連結的人都能存取，務必先確認密碼夠強
