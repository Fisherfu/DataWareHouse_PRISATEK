import frappe
from frappe.utils import today, nowdate

def create_mock_data():
    if not frappe.db:
        frappe.init("frontend")
        frappe.connect()

    # 1. 取得公司資訊
    companies = frappe.get_all("Company", fields=["name", "default_currency", "abbr", "default_inventory_account"])
    if not companies:
        print("[!] 找不到任何 Company，請先確認 ERPNext 初始設定。")
        return

    company_doc = frappe.get_doc("Company", companies[0].name)
    company = company_doc.name
    abbr = company_doc.abbr
    default_currency = company_doc.default_currency or "TWD"

    # 確保存在末級存貨科目
    stock_acc_name = f"1211 - 商品存貨 - {abbr}"
    parent_stock_group = f"121~122 - 存貨 - {abbr}"
    if not frappe.db.exists("Account", stock_acc_name):
        acc = frappe.get_doc({
            "doctype": "Account",
            "account_name": "商品存貨",
            "parent_account": parent_stock_group if frappe.db.exists("Account", parent_stock_group) else None,
            "company": company,
            "account_type": "Stock",
            "is_group": 0
        })
        acc.insert(ignore_permissions=True)
        inventory_account = acc.name
    else:
        inventory_account = stock_acc_name

    company_doc.default_inventory_account = inventory_account
    company_doc.save(ignore_permissions=True)
    print(f"[*] 設定公司預設存貨科目: {inventory_account}")
    print(f"[*] 使用公司: {company} (代碼: {abbr}), 預設幣別: {default_currency}")

    # 2. 尋找父倉庫
    all_wh_groups = frappe.get_all("Warehouse", filters={"company": company, "is_group": 1}, fields=["name"])
    parent_wh = all_wh_groups[0].name if all_wh_groups else None
    print(f"[*] 父倉庫: {parent_wh}")

    # 3. 建立 13 倉庫 (A 倉 ~ M 倉)
    warehouses_created = {}
    for i in range(13):
        wh_name = f"{chr(65+i)} 倉"
        wh_full_name = f"{wh_name} - {abbr}"
        if not frappe.db.exists("Warehouse", wh_full_name):
            wh_dict = {
                "doctype": "Warehouse",
                "warehouse_name": wh_name,
                "company": company,
                "is_group": 0,
                "account": inventory_account
            }
            if parent_wh:
                wh_dict["parent_warehouse"] = parent_wh
            wh_doc = frappe.get_doc(wh_dict)
            wh_doc.insert(ignore_permissions=True)
            print(f"[+] 建立倉庫: {wh_doc.name}")
            warehouses_created[wh_name] = wh_doc.name
        else:
            frappe.db.set_value("Warehouse", wh_full_name, "account", inventory_account)
            warehouses_created[wh_name] = wh_full_name

    # 4. 取得或建立 UOM (計量單位)
    uom = "Nos"
    if not frappe.db.exists("UOM", uom):
        existing_uoms = [u.name for u in frappe.get_all("UOM", limit=10)]
        if "Unit" in existing_uoms:
            uom = "Unit"
        elif "件" in existing_uoms:
            uom = "件"
        elif "個" in existing_uoms:
            uom = "個"
        elif existing_uoms:
            uom = existing_uoms[0]
        else:
            uom_doc = frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"})
            uom_doc.insert(ignore_permissions=True)
            uom = "Nos"
    print(f"[*] 使用計量單位 (UOM): {uom}")

    # 5. 取得物料群組 (Item Group)
    item_group = "All Item Groups"
    if not frappe.db.exists("Item Group", item_group):
        ig_list = frappe.get_all("Item Group", limit=1)
        item_group = ig_list[0].name if ig_list else "All Item Groups"

    # 6. 定義物料與供應商
    items_data = [
        {"item_code": "MLCC-0603-104K-X7R", "item_name": "貼片電容 0603 104K X7R", "rate": 0.85},
        {"item_code": "XTAL-24M-SMD3225", "item_name": "石英晶體 24MHz SMD3225", "rate": 4.20},
        {"item_code": "LANT-H1102NL", "item_name": "網路變壓器 H1102NL", "rate": 18.50},
        {"item_code": "TVS-SMAJ5.0CA", "item_name": "突波抑制二極體 SMAJ5.0CA", "rate": 1.10},
        {"item_code": "MCU-STM32F103C8T6", "item_name": "微控制器 STM32F103C8T6", "rate": 65.00},
        {"item_code": "GDT-2R090-8", "item_name": "氣體放電管 2R090-8", "rate": 6.80},
        {"item_code": "SSD-M2-256G-3D", "item_name": "固態硬碟 M.2 256GB 3D TLC", "rate": 680.00},
        {"item_code": "MLCC-0402-105K-X5R", "item_name": "貼片電容 0402 105K X5R", "rate": 0.62},
        {"item_code": "FUSE-1206-2A-125V", "item_name": "貼片保險絲 1206 2A 125V", "rate": 2.30},
        {"item_code": "LED-0805-RED-20MA", "item_name": "發光二極體 0805 紅光 20mA", "rate": 0.45},
        {"item_code": "ANT-2G4-PCB-FPC", "item_name": "2.4GHz 天線 PCB/FPC", "rate": 12.00},
        {"item_code": "RES-0603-1K-1%", "item_name": "貼片電阻 0603 1K 1%", "rate": 0.15},
    ]

    suppliers = ["華誠電子", "立揚科技", "泓宇通訊", "剑隆電子", "元捷資訊", "冠鑫材料"]

    supp_group = "All Supplier Groups"
    if not frappe.db.exists("Supplier Group", supp_group):
        sg_list = frappe.get_all("Supplier Group", limit=1)
        supp_group = sg_list[0].name if sg_list else "All Supplier Groups"

    for supp in suppliers:
        if not frappe.db.exists("Supplier", supp):
            s_doc = frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": supp,
                "supplier_group": supp_group,
                "supplier_type": "Company"
            })
            s_doc.insert(ignore_permissions=True)
            print(f"[+] 建立供應商: {supp}")

    for it in items_data:
        if not frappe.db.exists("Item", it["item_code"]):
            item_doc = frappe.get_doc({
                "doctype": "Item",
                "item_code": it["item_code"],
                "item_name": it["item_name"],
                "item_group": item_group,
                "stock_uom": uom,
                "is_stock_item": 1,
                "standard_rate": it["rate"]
            })
            item_doc.insert(ignore_permissions=True)
            print(f"[+] 建立料號: {it['item_code']}")

    # 7. 建立 Purchase Receipt（採購入庫單）
    mock_receipts = [
        {"dt": "2026-07-18", "supp": "華誠電子", "item": "MLCC-0603-104K-X7R", "qty": 12000, "lot": "K4A2H1", "wh": "A 倉", "rate": 0.85},
        {"dt": "2026-06-30", "supp": "華誠電子", "item": "MLCC-0603-104K-X7R", "qty": 15000, "lot": "K3F9B2", "wh": "D 倉", "rate": 0.85},
        {"dt": "2026-07-24", "supp": "立揚科技", "item": "XTAL-24M-SMD3225", "qty": 26000, "lot": "P8R37C", "wh": "J 倉", "rate": 4.20},
        {"dt": "2026-05-29", "supp": "泓宇通訊", "item": "LANT-H1102NL", "qty": 16200, "lot": "D5K21M", "wh": "C 倉", "rate": 18.50},
        {"dt": "2026-07-02", "supp": "華誠電子", "item": "TVS-SMAJ5.0CA", "qty": 56500, "lot": "M2Q88R", "wh": "B 倉", "rate": 1.10},
        {"dt": "2026-07-11", "supp": "剑隆電子", "item": "MCU-STM32F103C8T6", "qty": 1500, "lot": "T7B45N", "wh": "F 倉", "rate": 65.00},
        {"dt": "2026-06-12", "supp": "泓宇通訊", "item": "GDT-2R090-8", "qty": 3300, "lot": "W1C09J", "wh": "H 倉", "rate": 6.80},
        {"dt": "2026-08-02", "supp": "元捷資訊", "item": "SSD-M2-256G-3D", "qty": 800, "lot": "R9E62K", "wh": "M 倉", "rate": 680.00},
        {"dt": "2026-07-09", "supp": "立揚科技", "item": "MLCC-0402-105K-X5R", "qty": 128000, "lot": "S4N77A", "wh": "E 倉", "rate": 0.62},
        {"dt": "2026-08-01", "supp": "冠鑫材料", "item": "FUSE-1206-2A-125V", "qty": 9400, "lot": "B3H90L", "wh": "H 倉", "rate": 2.30},
        {"dt": "2026-07-27", "supp": "華誠電子", "item": "LED-0805-RED-20MA", "qty": 44000, "lot": "N6Q12F", "wh": "G 倉", "rate": 0.45},
        {"dt": "2026-06-21", "supp": "立揚科技", "item": "XTAL-24M-SMD3225", "qty": 7600, "lot": "P7R11X", "wh": "I 倉", "rate": 4.20},
        {"dt": "2026-08-03", "supp": "泓宇通訊", "item": "ANT-2G4-PCB-FPC", "qty": 2100, "lot": "C0K44T", "wh": "K 倉", "rate": 12.00},
        {"dt": "2026-07-05", "supp": "剑隆電子", "item": "RES-0603-1K-1%", "qty": 210000, "lot": "E5V63P", "wh": "L 倉", "rate": 0.15},
    ]

    print("\n[*] 開始建立採購入庫單 (Purchase Receipt)...")
    for rec in mock_receipts:
        target_wh = warehouses_created.get(rec["wh"]) or f"{rec['wh']} - {abbr}"
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": rec["supp"],
            "company": company,
            "posting_date": rec["dt"],
            "currency": default_currency,
            "set_warehouse": target_wh,
            "items": [
                {
                    "item_code": rec["item"],
                    "qty": rec["qty"],
                    "rate": rec["rate"],
                    "received_qty": rec["qty"],
                    "warehouse": target_wh,
                    "uom": uom,
                    "stock_uom": uom,
                    "conversion_factor": 1.0,
                    "description": f"Lot Code: {rec['lot']} | 客戶料號對照測試"
                }
            ]
        })
        pr.insert(ignore_permissions=True)
        try:
            pr.submit()
            print(f"[✓] 已建立並過帳採購入庫單: {pr.name} ({rec['item']} x {rec['qty']} -> {target_wh})")
        except Exception as e:
            print(f"[*] 單據已建立為草稿 (Draft): {pr.name} (原因: {str(e)[:80]})")

    frappe.db.commit()
    print("\n[🎉] 14 筆採購入庫測試假資料與 13 倉庫主檔已全數成功寫入 ERPNext！")

if __name__ == "__main__":
    create_mock_data()
