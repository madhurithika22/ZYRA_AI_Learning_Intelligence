# Performance Benchmark & Latency Report

## 1. Local Benchmark Methodology
System operation latencies were measured using `scripts/benchmark_system.py` on local execution environment with PostgreSQL 17 database.

## 2. Latency Breakdown

| Subsystem / Operation | Median Latency | p95 Latency | Max Latency |
| :--- | :--- | :--- | :--- |
| **Conventional Baseline Recommender** | < 0.5 ms | < 1.0 ms | < 2.0 ms |
| **Bottleneck Analysis Service** | 12.4 ms | 18.2 ms | 24.1 ms |
| **Next Action Intelligence Service** | 14.1 ms | 21.0 ms | 28.5 ms |
| **Learning Twin Service** | 18.5 ms | 26.3 ms | 32.0 ms |
| **Replanning Service Evaluation** | 15.2 ms | 22.8 ms | 29.4 ms |
| **Grounded Conversational AI (Deterministic Bypass)** | < 1.0 ms | < 2.0 ms | < 3.0 ms |
| **Gemini 2.5 Flash API (Live Request)** | 850 ms | 1200 ms | 1450 ms |

## 3. Findings & Performance Characteristics
- Deterministic intelligence services execute with sub-30ms p95 latencies on local PostgreSQL.
- Factual status queries bypassing LLM engine complete in < 1ms, saving 850ms+ per request.
