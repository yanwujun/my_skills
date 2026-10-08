---
name: codebase-design
description: "Deep module design: interface, seam, adapter vocabulary."
---

# Codebase Design

Design **deep modules**: a lot of behaviour behind a small interface, placed at a clean seam, testable through that interface.

## Glossary

Use these terms exactly — don't substitute "component," "service," "API," or "boundary."

**Module** — anything with an interface and an implementation. Scale-agnostic: function, class, package, or tier-spanning slice.

**Interface** — everything a caller must know to use the module correctly: type signature, invariants, ordering constraints, error modes, required configuration, performance characteristics.

**Implementation** — what's inside a module. Distinct from **Adapter**.

**Depth** — leverage at the interface: behaviour per unit of interface. **Deep** = small interface, lots of behaviour. **Shallow** = interface nearly as complex as implementation.

**Seam** _(Michael Feathers)_ — a place where you can alter behaviour without editing in that place.

**Adapter** — a concrete thing that satisfies an interface at a seam. Describes role, not substance.

**Leverage** — what callers get from depth: more capability per unit of interface.

**Locality** — what maintainers get from depth: change, bugs, knowledge concentrate in one place.

## Deep vs shallow

```
Deep:  ┌──────────────┐    Shallow: ┌──────────────────┐
       │ Small I/F    │             │ Large Interface  │
       ├──────────────┤             ├──────────────────┤
       │ Deep Impl    │             │ Thin Passthrough │
       └──────────────┘             └──────────────────┘
```

Design questions: Can I reduce methods? Simplify params? Hide more complexity?

## Principles

- **Depth is a property of the interface.** Internal parts can be small and mockable.
- **The deletion test.** If deleting the module makes complexity vanish → pass-through. If complexity spreads across N callers → earning its keep.
- **Interface = test surface.** If you need to test past the interface, module is wrong shape.
- **One adapter = hypothetical seam. Two = real seam.**

## Testability

1. Accept dependencies, don't create them
2. Return results, don't produce side effects
3. Small surface area → fewer tests needed

## Java/Spring Boot 映射

- Module = Service/Facade 层
- Seam = `@Autowired` 注入点，测试用 `@MockBean`
- Depth 正例 = `OrderService.placeOrder()` 隐藏校验/库存/支付/通知
- Shallow 反例 = Controller 直接写 200 行业务逻辑