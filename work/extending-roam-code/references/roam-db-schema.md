# roam-code DB Schema (relevant tables for graph export)

## Core Tables

### files
- `id` INTEGER PK
- `path` TEXT UNIQUE — relative file path
- `language` TEXT — detected language
- `file_role` TEXT DEFAULT 'source'
- `hash` TEXT
- `mtime` REAL
- `line_count` INTEGER

### symbols
- `id` INTEGER PK
- `file_id` INTEGER FK → files.id
- `name` TEXT — symbol name
- `qualified_name` TEXT — fully qualified
- `kind` TEXT — class, function, method, variable, constant, property, module, interface, enum, struct, trait, constructor, field
- `signature` TEXT
- `line_start`, `line_end` INTEGER
- `docstring` TEXT
- `visibility` TEXT — public, private, protected
- `is_exported` INTEGER 0/1
- `parent_id` INTEGER FK → symbols.id
- `decorators` TEXT — comma-joined decorator names
- `is_async` INTEGER 0/1
- `extractor_version` TEXT

### edges
- `id` INTEGER PK
- `source_id` INTEGER FK → symbols.id
- `target_id` INTEGER FK → symbols.id
- `kind` TEXT — calls, imports, inherits, implements, contains, references, overrides, dispatch, type_ref, pytest_fixture_dep
- `line` INTEGER
- `bridge` TEXT
- `confidence` REAL
- `source_file_id` INTEGER FK → files.id

### file_edges
- `id` INTEGER PK
- `source_file_id`, `target_file_id` FK → files.id
- `kind` TEXT — imports, etc.
- `symbol_count` INTEGER

### graph_metrics
- `symbol_id` INTEGER PK FK → symbols.id
- `pagerank` REAL
- `in_degree`, `out_degree` INTEGER
- `betweenness`, `closeness`, `eigenvector` REAL
- `debt_score` REAL

### symbol_metrics
- `symbol_id` INTEGER PK FK → symbols.id
- `cognitive_complexity` REAL
- `nesting_depth` INTEGER
- `param_count` INTEGER
- `line_count` INTEGER
- `cyclomatic_density` REAL
- `halstead_volume`, `halstead_difficulty`, `halstead_effort` REAL

### file_stats
- `file_id` INTEGER PK FK → files.id
- `commit_count`, `total_churn`, `distinct_authors` INTEGER
- `complexity` REAL
- `health_score` REAL
- `cochange_entropy` REAL

### clusters
- `symbol_id` INTEGER PK FK → symbols.id
- `cluster_id` INTEGER
- `cluster_label` TEXT

### business_rules (added by business-rule-graph)
- `id` INTEGER PK
- `rule_id` TEXT — unique rule identifier
- `rule_type` TEXT — validation, authorization, workflow, calculation, data_integrity, process, configuration, integration
- `domain` TEXT — LLM semantic classification
- `flow` TEXT — business flow name
- `description` TEXT
- `severity` TEXT
- `source_file` TEXT
- `source_line` INTEGER
- `hash` TEXT
- `params` TEXT — JSON string
- `extraction` TEXT
- `merge_with` TEXT

### business_rule_edges (added by business-rule-graph)
- `id` INTEGER PK
- `source_rule_id` INTEGER FK → business_rules.id
- `target_rule_id` INTEGER FK → business_rules.id
- `edge_type` TEXT — same_field, same_flow, conflicts_with, related
