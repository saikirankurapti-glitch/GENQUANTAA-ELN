# Functional Specification: Inventory Management Module

## 1. Purpose
The **Inventory Management Module** tracks laboratory stock, chemical reagents, kits, cell culture media, consumables, and raw materials. It manages stock check-ins, stock issues/consumption, batch lot tracking, supplier metadata, storage location assignments, and automated low-stock alerts.

## 2. Key Features
* **Stock Tracking:** Track `current_stock`, `minimum_stock`, and `reorder_level` for every inventory item.
* **Batch Lot Management:** Manage lot numbers, manufacturing dates, and expiration dates (`InventoryBatch`).
* **Stock Transactions:** Record all stock check-in (`RECEIVE`), stock issue (`ISSUE`), adjustment (`ADJUST`), and disposal (`DISPOSE`) transactions with complete audit history (`InventoryTransaction`).
* **Low-Stock Alerts:** Automatically flag items where `current_stock <= reorder_level`.
* **Tenant Isolation:** Ensure all inventory items, batches, and transactions are strictly scoped by `tenant_id`.

## 3. Inputs & Outputs
* **Inputs:** `InventoryItemCreate`, `InventoryItemUpdate`, `InventoryReceiveRequest`, `InventoryIssueRequest`, `InventoryFilter`.
* **Outputs:** `InventoryItemRead`, `InventoryItemDetail`, `InventoryItemSummary`, `InventoryBatchRead`, `InventoryTransactionRead`, `InventoryListResponse`.

## 4. Dependencies
* **Tenant Module:** Workspace isolation.
* **Identity Module:** User issuer and receiver identities.
* **RBAC Module:** Permissions (`inventory.create`, `inventory.read`, `inventory.update`, `inventory.issue`, `inventory.receive`).

## 5. Workflow
```
[RECEIVE STOCK BATCH] ---> [STORE AT LOCATION] ---> [ISSUE / CONSUME STOCK] ---> [LOW-STOCK ALERT]
```

## 6. Acceptance Criteria
1. `item_code` must be globally unique within a tenant.
2. `current_stock` and `minimum_stock` must be non-negative (`>= 0`).
3. Stock issuing cannot cause `current_stock` to drop below zero.
4. Expired inventory batches cannot be issued for lab use.
