# System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                          │
│                      (generateFrameworkKpi.py)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Main Pipeline Orchestrator                    │
│                      (kpi_generator.py)                          │
└─┬───────────┬──────────┬──────────┬──────────┬─────────┬────────┘
  │           │          │          │          │         │
  ↓           ↓          ↓          ↓          ↓         ↓
┌────┐   ┌────────┐  ┌──────┐  ┌────────┐  ┌──────┐  ┌──────┐
│ DB │   │   S3   │  │Module│  │Ollama  │  │Valid.│  │Synth.│
│    │   │Handler │  │Summ. │  │Client  │  │      │  │Data  │
└────┘   └────────┘  └──────┘  └────────┘  └──────┘  └──────┘
  ↑           ↑          ↑          ↑          ↑         ↑
  │           │          │          │          │         │
  └───────────┴──────────┴──────────┴──────────┴─────────┘
                         │
                         ↓
                   ┌──────────┐
                   │  config  │
                   └──────────┘
```

## 📊 Data Flow Diagram

```
┌──────────┐
│  Start   │
└────┬─────┘
     │
     ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 1: DATA COLLECTION                                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐     │
│  │  MySQL   │──→   │Framework │──→   │  Schema  │     │
│  │Connection│      │   Info   │      │   Info   │     │
│  └──────────┘      └──────────┘      └──────────┘     │
│                                                          │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐     │
│  │    S3    │──→   │ Download │──→   │  Extract │     │
│  │Documents │      │   Files  │      │   Text   │     │
│  └──────────┘      └──────────┘      └──────────┘     │
│                                                          │
│  ┌──────────┐      ┌──────────┐                        │
│  │Framework │──→   │  Other   │                        │
│  │   Data   │      │  Tables  │                        │
│  └──────────┘      └──────────┘                        │
└─────────────────────────────────────────────────────────┘
     │
     ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 2: ORGANIZATION                                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐     │
│  │  Group   │──→   │  Create  │──→   │  Attach  │     │
│  │  Tables  │      │ Summaries│      │ Evidence │     │
│  └──────────┘      └──────────┘      └──────────┘     │
│       │                  │                  │           │
│       │                  ↓                  │           │
│       │         policies_summary.json       │           │
│       │         audit_summary.json          │           │
│       │         risk_summary.json           │           │
│       │         ...                         │           │
│       │                                     │           │
│       └─────────────────┬───────────────────┘           │
│                         ↓                               │
│                 ┌──────────────┐                        │
│                 │  Index &     │                        │
│                 │  Score S3    │                        │
│                 │  Documents   │                        │
│                 └──────────────┘                        │
└─────────────────────────────────────────────────────────┘
     │
     ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 3: KPI GENERATION (Per Module)                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐     │
│  │  Check   │──→   │  Chunk   │──→   │  Send to │     │
│  │   Size   │      │   Data   │      │  Ollama  │     │
│  └──────────┘      └──────────┘      └──────────┘     │
│       │                  │                  │           │
│       │                  │                  ↓           │
│       │                  │         ┌──────────────┐    │
│       │                  │         │  Ollama AI   │    │
│       │                  │         │  Generates   │    │
│       │                  │         │  12 KPIs     │    │
│       │                  │         └──────────────┘    │
│       │                  │                  │           │
│       │                  │                  ↓           │
│       │                  │         ┌──────────────┐    │
│       │                  │         │Parse & Clean │    │
│       │                  │         │     JSON     │    │
│       │                  │         └──────────────┘    │
│       │                  │                  │           │
│       └──────────────────┴──────────────────┘           │
│                         │                               │
│                         ↓                               │
│                 ┌──────────────┐                        │
│                 │  Validate    │                        │
│                 │  Formulas    │                        │
│                 └──────────────┘                        │
└─────────────────────────────────────────────────────────┘
     │
     ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 4: DATA ENRICHMENT                                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  For Each KPI:                                          │
│                                                          │
│  ┌──────────┐                                           │
│  │Has Data? │                                           │
│  └────┬─────┘                                           │
│       │                                                  │
│   ┌───┴───┐                                            │
│   │       │                                             │
│  YES     NO                                             │
│   │       │                                             │
│   │       ↓                                             │
│   │  ┌──────────────┐     ┌──────────────┐            │
│   │  │  Generate    │──→  │  Upload to   │            │
│   │  │  Synthetic   │     │     S3       │            │
│   │  │  Dataset     │     └──────────────┘            │
│   │  └──────────────┘            │                     │
│   │                               │                     │
│   └───────────────┬───────────────┘                     │
│                   ↓                                     │
│          ┌──────────────┐                               │
│          │  Evaluate    │                               │
│          │  Formula     │                               │
│          └──────────────┘                               │
│                   │                                     │
│                   ↓                                     │
│          ┌──────────────┐                               │
│          │  Calculate   │                               │
│          │    Value     │                               │
│          └──────────────┘                               │
└─────────────────────────────────────────────────────────┘
     │
     ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 5: FINALIZATION                                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐     │
│  │ Remove   │──→   │  Final   │──→   │  Write   │     │
│  │Duplicates│      │Validation│      │ to MySQL │     │
│  └──────────┘      └──────────┘      └──────────┘     │
└─────────────────────────────────────────────────────────┘
     │
     ↓
┌──────────┐
│   Done   │
└──────────┘
```

## 🔄 Module Interaction Map

```
                    ┌──────────────┐
                    │   config.py  │
                    │  (Settings)  │
                    └──────┬───────┘
                           │
                           │ Used by all modules
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ↓                  ↓                  ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ database.py  │   │s3_handler.py │   │ollama_client │
│              │   │              │   │    .py       │
│ - Connect    │   │ - Download   │   │              │
│ - Query      │   │ - Extract    │   │ - Generate   │
│ - Save       │   │ - Cache      │   │ - Parse      │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       │                  │                  │
       └──────────┬───────┴──────────────────┘
                  │
                  ↓
        ┌──────────────────┐
        │kpi_generator.py  │
        │  (Orchestrator)  │
        └────────┬─────────┘
                 │
                 │ Coordinates
                 │
     ┌───────────┼───────────┐
     │           │           │
     ↓           ↓           ↓
┌─────────┐ ┌─────────┐ ┌─────────┐
│evidence │ │module   │ │kpi_     │
│.py      │ │summaries│ │validation│
│         │ │.py      │ │.py      │
└─────────┘ └─────────┘ └─────────┘
     │           │           │
     └───────────┼───────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
     ↓           ↓           ↓
┌─────────┐ ┌─────────┐ ┌─────────┐
│formula_ │ │synthetic│ │         │
│evaluator│ │_data.py │ │         │
│.py      │ │         │ │         │
└─────────┘ └─────────┘ └─────────┘
```

## 📦 Module Responsibilities

### Layer 1: Configuration
```
┌────────────────────────────────────────┐
│            config.py                   │
│                                        │
│  • Database credentials                │
│  • S3 configuration                    │
│  • Ollama settings                     │
│  • Feature flags                       │
│  • Global constants                    │
└────────────────────────────────────────┘
```

### Layer 2: Data Access
```
┌──────────────────────┐  ┌──────────────────────┐
│    database.py       │  │   s3_handler.py      │
│                      │  │                      │
│  • MySQL connection  │  │  • S3 download       │
│  • Schema queries    │  │  • Text extraction   │
│  • Data retrieval    │  │  • File caching      │
│  • KPI persistence   │  │  • DataFrame loading │
└──────────────────────┘  └──────────────────────┘
```

### Layer 3: Data Processing
```
┌──────────────────────┐  ┌──────────────────────┐
│    evidence.py       │  │ module_summaries.py  │
│                      │  │                      │
│  • Index building    │  │  • Summary creation  │
│  • Evidence scoring  │  │  • Data chunking     │
│  • S3 attachment     │  │  • Module grouping   │
└──────────────────────┘  └──────────────────────┘
```

### Layer 4: AI & Validation
```
┌──────────────────────┐  ┌──────────────────────┐
│  ollama_client.py    │  │  kpi_validation.py   │
│                      │  │                      │
│  • API calls         │  │  • Formula checks    │
│  • JSON parsing      │  │  • Deduplication     │
│  • Prompt engineering│  │  • Alignment         │
└──────────────────────┘  └──────────────────────┘
```

### Layer 5: Value Computation
```
┌──────────────────────┐  ┌──────────────────────┐
│formula_evaluator.py  │  │  synthetic_data.py   │
│                      │  │                      │
│  • Formula eval      │  │  • Dataset generation│
│  • Value calculation │  │  • PDF creation      │
│  • Type inference    │  │  • S3 upload         │
└──────────────────────┘  └──────────────────────┘
```

### Layer 6: Orchestration
```
┌────────────────────────────────────────┐
│         kpi_generator.py               │
│                                        │
│  • Pipeline coordination               │
│  • Module processing                   │
│  • Error handling                      │
│  • Progress tracking                   │
└────────────────────────────────────────┘
```

### Layer 7: Entry Point
```
┌────────────────────────────────────────┐
│         generateFrameworkKpi.py                 │
│                                        │
│  • CLI interface                       │
│  • Argument parsing                    │
│  • Main execution                      │
└────────────────────────────────────────┘
```

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────┐
│              Security Layers                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. Configuration (config.py)                   │
│     • Credentials stored in .env                │
│     • No hardcoded secrets in code              │
│                                                  │
│  2. Database Access (database.py)               │
│     • Parameterized queries (SQL injection safe)│
│     • Connection pooling                        │
│     • Error handling                            │
│                                                  │
│  3. S3 Access (s3_handler.py)                   │
│     • IAM credentials                           │
│     • Bucket policies                           │
│     • Signed URLs                               │
│                                                  │
│  4. Data Validation (kpi_validation.py)         │
│     • Input sanitization                        │
│     • Formula validation                        │
│     • Type checking                             │
│                                                  │
└─────────────────────────────────────────────────┘
```

## 🚀 Performance Optimization

```
┌─────────────────────────────────────────────────┐
│           Performance Features                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. Caching (s3_handler.py, evidence.py)        │
│     • S3 document cache (avoid re-download)     │
│     • Chunk cache (avoid re-processing)         │
│     • Schema cache (avoid re-query)             │
│                                                  │
│  2. Chunking (module_summaries.py)              │
│     • Smart data splitting                      │
│     • Context window optimization               │
│     • Memory management                         │
│                                                  │
│  3. Parallel Processing (potential)             │
│     • Module-level parallelization              │
│     • S3 download parallelization               │
│                                                  │
│  4. Lazy Loading                                │
│     • Load data only when needed                │
│     • Stream large files                        │
│                                                  │
└─────────────────────────────────────────────────┘
```

## 🔄 Error Handling Flow

```
                    ┌──────────┐
                    │  Error   │
                    │ Occurs   │
                    └────┬─────┘
                         │
                         ↓
                ┌────────────────┐
                │  Log Error     │
                │  with Context  │
                └────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ↓                       ↓
    ┌─────────┐           ┌─────────┐
    │Retryable│           │Critical │
    │  Error  │           │  Error  │
    └────┬────┘           └────┬────┘
         │                     │
         ↓                     ↓
    ┌─────────┐           ┌─────────┐
    │  Retry  │           │  Abort  │
    │ (3 max) │           │  & Exit │
    └────┬────┘           └─────────┘
         │
         ↓
    ┌─────────┐
    │ Success │
    │    or   │
    │  Abort  │
    └─────────┘
```

## 📊 Data Storage Architecture

```
┌─────────────────────────────────────────────────┐
│              Storage Locations                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  MySQL Database (database.py)                   │
│  ├── frameworks                                 │
│  ├── policies                                   │
│  ├── risks                                      │
│  ├── incidents                                  │
│  ├── audit                                      │
│  └── kpis ← Final output                        │
│                                                  │
│  S3 Bucket (s3_handler.py)                      │
│  ├── Evidence documents                         │
│  ├── Synthetic datasets (CSV)                   │
│  └── Synthetic evidence (PDF)                   │
│                                                  │
│  Local Files (module_summaries.py)              │
│  ├── Module summaries (JSON)                    │
│  ├── Schema metadata (JSON)                     │
│  ├── S3 cache (JSON)                            │
│  └── Chunk cache (JSON)                         │
│                                                  │
│  In-Memory (config.py)                          │
│  ├── EVIDENCE_DATAFRAMES                        │
│  ├── CURRENT_SCHEMA_INFO                        │
│  └── Model instances (KB_MODEL, SBERT_MODEL)    │
│                                                  │
└─────────────────────────────────────────────────┘
```

This architecture ensures:
- ✅ Separation of concerns
- ✅ Scalability
- ✅ Maintainability
- ✅ Testability
- ✅ Performance
- ✅ Security

