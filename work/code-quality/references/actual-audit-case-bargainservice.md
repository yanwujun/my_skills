# 实际审计案例记录

## 案例：BargainServiceImpl.java 审计

**文件：** 2567行 Java 服务实现
**审计时长：** 一轮通读（约10个 read_file 调用）
**发现：** 2个高危 + 3个中危 + 3个低危

### 高危发现详情

#### H1: deleteDraft() 中校验与删除非原子

```java
// 第1254-1267行
public void deleteDraft(Long id, LoginUser loginUser) {
    EnquiryEntity enquiryEntity = engine.enquiryService().getById(id);
    ExceptionChecker.checkNotNull(enquiryEntity, "议价不存在");
    engine.checkService().checkEnquiryEditRights(loginUser, enquiryEntity);
    engine.checkService().checkEnquiryState(enquiryEntity.getId(), EnquiryStateEnum.TEMP_INSERT, EnquiryStateEnum.RETURN);
    // ← 在这里，高并发下第二个请求可以通过校验
    deleteBargainInfo(enquiryEntity);  // 先删5张关联表
    engine.enquiryService().enquiryOperSave("删除", ...);
    engine.enquiryService().removeById(enquiryEntity); // 再删主表
}
```

**场景：** 两个采购人同时点击"删除"同一个议价单。两个请求都通过状态校验，然后：
- A 删关联数据 → B 的关联数据已经没了 → 删除空数据
- 如果 A、B 之间有人新建了一个议价单（ID相同），B 的删除会误删新数据

**修复：** 在查询时加 `SELECT ... FOR UPDATE`

#### H2: cancelDraft() 的 TOCTOU 窗口

```java
// 第1282-1285行
boolean started = enquiry.getEnqStartTime() != null && !now.before(enquiry.getEnqStartTime());
if (started && hasSubmittedQuote(enquiry.getId())) {
    ExceptionChecker.throwException400("当前议价已有供应商报价，不可作废");
}
// ← 此时报价可能刚被提交
```

**场景：** 采购人点作废，校验通过（无报价）。此时供应商刚好提交报价（写入DB）。然后作废操作执行，议价单状态变 INVALID，但报价数据已写入且未被清除。

### 中危发现详情

#### M1: processDraftPersist() 先删后插无锁

`saveBargainToDB()` 的流程是：`deleteBargainInfo()`（删5张表）→ `saveBatch()`（重新插入）。两个人同时保存草稿时后保存的人覆盖前一个人的全部数据。

#### M2: 价格加密无降级

`TfEQuoteServiceImpl.encryptPrice()` 如果抛出异常，整个事务回滚。`decryptPrice()` 失败只打日志，无重试。

#### M3: 风控校验被注释

约150行校验代码（50万上限、计划预算校验等）被注释。当前版本对此类业务无任何限制。

### 发现技巧

1. 从接口开始读（`BargainService.java`），了解所有方法签名的意图
2. 重点读所有 `@Transactional` 方法——长事务是 TOCTOU 高发区
3. 搜索所有 `removeById`、`delete`、`saveBatch` 等写操作，看前面有没有锁
4. 搜索所有 `.get(0)` 看有没有越界风险
5. 搜索大段被注释的代码——被注释的校验逻辑通常是上次重构遗留的
6. 检查 builder 模式中是否重复 `set` 了同一个字段
