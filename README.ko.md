# zig-doc-engine (한국어)

> **Zig v0.16.0으로 작성된 초경량(535KB), 초고속 기술문서 색인 및 FTS5 검색 엔진.**

[English Version](README.md)

`zig-doc-engine`은 AI 코딩 에이전트, 개발자 CLI 도구, 임베디드 장치를 위해 설계된 무의존성(Zero-dependency) 로컬 문서 검색 엔진입니다. 메모리 복사 없는(Zero-copy) 마크다운 파싱과 SQLite FTS5 전문 검색 엔진을 결합하여, 1ms 미만의 콜드 스타트와 초당 65,000회 이상의 검색 처리량을 제공합니다.

---

## ⚡ 핵심 벤치마크 실측 요약 (Rust & Go 대비)

10MB 마크다운 코퍼스(11,046개 섹션) 및 20,000회 멀티스레드 검색 실측 결과:

| 지표 | **zig-doc-engine (Zig v0.16.0)** | **Rust (AOT rusqlite)** | **Go 1.26 (cgo-sqlite3)** | 비교 우위 |
| :--- | :---: | :---: | :---: | :--- |
| **10MB 마크다운 파싱·청킹** | **7.89 ms** | 13.02 ms | 19.69 ms | 🏆 **Zig (Rust 대비 1.65배 빠름)** |
| **FTS5 일괄 색인 (1.1만 행)** | 82.87 ms | **77.82 ms** | 90.52 ms | ⚖️ **동급 (~14만 행/초)** |
| **8스레드 동시 검색 처리량** | 64,266 QPS | **66,982 QPS** | 66,096 QPS | ⚖️ **동급 (~66,000 QPS)** |
| **피크 메모리 점유 (RSS)** | **23.55 MB** | 33.28 MB | 65.59 MB | 🏆 **Zig (Go 대비 1/3 메모리)** |
| **바이너리 크기 (Strip)** | **535 KB** | 2.29 MB | 3.82 MB | 🏆 **Zig (Rust 대비 1/4 크기)** |

---

## 🚀 주요 특징

* **Zero-copy 파싱**: 힙 메모리 할당 낭비 없이 수 MB 단위의 마크다운을 Zig 슬라이스로 즉시 파싱.
* **임베디드 SQLite FTS5**: BM25 랭킹, 스니펫 하이라이팅, 불리언 검색을 C 네이티브로 직접 처리.
* **1ms 미만 Cold-start**: VM이나 런타임이 없어 실행 즉시 1ms 이내에 결과 반환.
* **듀얼 타깃 빌드**: 단일 CLI 실행 바이너리(`doc-engine`) 및 C-ABI 정적 라이브러리(`libdocengine.a`) 동시 빌드.
* **다양한 소스 연동**: `llms.txt`, 공식 마크다운 명세, 로컬 문서 저장소 지원.

---

## 🛠️ 빌드 및 설치

### 요구 사항
* [Zig v0.16.0+](https://ziglang.org/download/)
* `sqlite3` 라이브러리

```bash
git clone https://github.com/entropyparadox-lab/zig-doc-engine.git
cd zig-doc-engine
zig build -Doptimize=ReleaseFast
```

빌드 결과물 (`zig-out/`):
* `zig-out/bin/doc-engine`: 535KB 단일 실행 바이너리
* `zig-out/lib/libdocengine.a`: C 호환 정적 라이브러리
* `zig-out/include/doc_engine.h`: C 헤더 파일

---

## 📖 CLI 사용법

```bash
# 기본 검색
doc-engine search "Router State"

# 특정 라이브러리 필터링 및 개수 제한
doc-engine search "ArrayListUnmanaged" --lib zig --limit 3

# 문서 전문 확인
doc-engine get curated:axum-0.8

# 색인된 라이브러리 목록 확인
doc-engine list
```

---

## 🔄 커뮤니티 지식 플라이휠: LLM 버전 드리프트 & 빌드 에러 기여

LLM은 주요 라이브러리의 메이저 버전 변경(Zig 0.11 ➔ 0.16, Axum 0.7 ➔ 0.8, React 18 ➔ 19 등) 시 구버전 문법을 할루시네이션하는 경우가 많습니다.

`zig-doc-engine`은 오픈소스 **지식 플라이휠(Knowledge Flywheel)**을 운영합니다:
1. **에러 해결 & 실검증**: AI 코딩 에이전트(Hermes, Claude Code, Cursor, Codex 등)가 빌드/컴파일 에러를 수정하고 종료 코드 0(Exit Code 0)으로 실검증 완료.
2. **동의 기반 기여**: 개발자 승인 하에 개인정보/사내 시크릿을 마스킹하고 [GitHub Issue Form](https://github.com/entropyparadox-lab/zig-doc-engine/issues/new?template=llm_drift_submission.yml) 또는 PR로 기여.
3. **즉시 FTS5 색인**: 머지된 해결책은 `doc-engine` 로컬 검색 DB에 즉시 색인되어 차후 전 세계 AI 에이전트의 구버전 할루시네이션을 원천 차단.

---

## 📄 라이선스

MIT License. 상세 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
