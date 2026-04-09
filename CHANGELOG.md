# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Comprehensive analysis refactoring with `analysis_utils.py` and `analysis_config.py`
- Professional README with research context, experimental design, and troubleshooting guide
- `requirements.txt` for pip-based dependency management
- `CONTRIBUTING.md` with detailed guidelines for open-source collaboration
- `CHANGELOG.md` for version tracking
- `validate_logs.py` for data integrity validation
- `STAGE1_QUICKSTART.py` for Stage 1 validation workflow

### Added (Core Features)
- Multi-mode decision-making (standard text, prompt history, natural language with vision)
- Vision-assisted collision avoidance using LLM-based image analysis
- Support for multiple LLM providers (OpenAI GPT-5.2, Claude Sonnet 4.5, DeepSeek Chat)
- Five prompt abstraction levels (minimal → detailed) plus specialized TSS mode
- Six maritime collision scenarios (head-on, crossing, overtaking, etc.)
- Real-time Pygame visualization with interactive controls
- Automated batch experiment runner with 10 runs per configuration
- Comprehensive analysis pipeline (master analysis, ablations, publication figures)
- COLREGs compliance checking and rule alignment metrics
- Collision prediction via DCPA/TCPA calculation

### Changed
- Refactored all analysis files (`master_analysis.py`, `ablation_study.py`, `mode_prompt_study.py`, `final_plots.py`) to use centralized analysis utilities
- Updated `.gitignore` with comprehensive exclusions for results, secrets, IDE files
- Improved LLM response parsing with ASCII encoding fallback for smart quotes
- Enhanced error handling in LLM vision manager

### Fixed
- Eliminated 25-30% code duplication across analysis scripts
- Corrected LLM response encoding issues when handling special characters
- Improved response parser robustness for varied LLM output formats

### Deprecated
- `entity_manager_rag.py` (kept for reference, not actively used)
- `try.py` (temporary testing file)

### Removed
- Redundant metric calculation functions (consolidated to `analysis_utils.py`)
- Duplicate rule extraction logic (now in `extract_rule_num()`)
- Duplicate rule alignment calculation (now in `calculate_alignment()`)

### Security
- Added `.gitignore` with proper exclusions for credentials and secrets
- All API keys should be managed via `.env` file (not committed)

---

## [v1.0.0-beta] - 2026-04-09

### Initial Public Release

#### Added
- **Core Simulator**: Pygame-based multi-vessel maritime collision avoidance simulator
  - Vessel dynamics with heading/speed control
  - Real-time visualization with collision detection
  - DCPA/TCPA prediction for risk assessment
  - Six classical maritime encounter scenarios
  
- **LLM Integration**: Three decision-making modes
  - `entity_manager_standard.py`: Pure text-based decision-making
  - `entity_manager_prompt_history.py`: Text with temporal memory
  - `entity_manager_natural_language.py`: Vision-assisted decisions with image analysis
  
- **Multi-Provider Support**:
  - OpenAI GPT-5.2
  - Anthropic Claude Sonnet 4.5
  - DeepSeek Chat
  - Async API calls with JSON response cleaning
  
- **Prompt Engineering**: Five abstraction levels + TSS mode
  - `minimal_prompt.py`: Bare minimum context
  - `moderate_prompt.py`: Essential information
  - `detailed_prompt.py`: Comprehensive context with rules
  - `natural_language_prompt.py`: Conversational framing
  - `tss_prompt.py`: Traffic Separation Scheme specialized
  
- **Batch Experimentation**:
  - Automated 10-run experiment loops
  - Cross-product of: 3 modes × 3 providers × 5 prompts × 6 scenarios = 270 configurations
  - CSV logging of all LLM decisions
  - Run timing and cost tracking
  
- **Analysis Pipeline**:
  - ETL: Master analysis consolidates all experiment logs
  - Ablation studies: 4 supplementary figures
  - Mode-prompt interactions: 3 interaction heatmaps
  - Publication figures: 4 main results visualizations
  
- **COLREGs Evaluation**:
  - Automatic rule alignment checking
  - Collision rate measurement
  - Decision reliability metrics
  - Rule compliance scoring
  
- **Documentation**:
  - `PAPER_PLAN.md`: 7-stage publication roadmap (8-10 weeks)
  - `README.md`: Comprehensive usage guide with architecture overview
  - `STATUS_REPORT.md`: Code review findings and troubleshooting
  - `IMPLEMENTATION_SUMMARY.md`: Publication strategy overview
  - Example usage notebooks and scripts

#### Known Limitations

- **Data Collection**: Currently only 189 LLM calls collected (need ~2,500 for full analysis)
- **Deterministic Baseline**: Not yet implemented (required for Stage 1)
- **Robustness Testing**: Noise and delay perturbations not yet validated
- **Simulator Simplifications**: 
  - Assumes point vessels (no physical extent)
  - Linear dynamics (no acceleration/deceleration curves)
  - Simplified visibility model
- **LLM Sensitivity**: 
  - Performance varies significantly with prompt framing
  - Different models show different reasoning styles
  - Consistent JSON output not guaranteed (requires fallback logic)
- **Evaluation Scope**:
  - Only six scenarios (not comprehensive maritime situation space)
  - No real-world validation (simulator-only)
  - Limited to 2-3 vessel encounters
- **Cost Analysis**:
  - Full experiment requires ~$500-800 in API calls
  - No budget optimization strategies yet

---

## Planned Releases

### [v1.1.0] - Expected 2026-05-XX (Stage 2-3)
- Full dataset (2,500 LLM calls across providers)
- Robustness experiments (noise, delay, model variations)
- Deterministic COLREG baseline controller
- Statistical significance testing

### [v1.2.0] - Expected 2026-06-XX (Stage 4-5)
- Multi-vessel scenario support (4+ vessels)
- Advanced metrics (decision latency distributions, failure taxonomy)
- Real-time performance visualization
- API cost optimization strategies

### [v2.0.0] - Expected 2026-07-XX (Stage 6-7)
- Publication submission to target venue (Ocean Engineering)
- Final manuscript with all results and analysis
- Open-source community support protocols
- Extended documentation and tutorials

---

## Migration Guides

### From Beta to v1.0
- No breaking changes; all experiments conducted with beta code are compatible
- `requirements.txt` now supersedes `environment.yml` for pip-based installation

### Upgrading Dependencies
- All core dependencies pinned to specific versions in `requirements.txt`
- Use `pip install --upgrade -r requirements.txt` to get latest patch versions
- For major version upgrades, update `requirements.txt` manually after testing

---

## Contribution Notes

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Bug report guidelines
- Feature request templates
- Code submission workflow
- Code standards and style guide
- Development environment setup

---

## Authors & Attribution

**Primary Authors**: 
- [Your Name] - Simulator design, LLM integration, analysis pipeline
- [Advisor/Co-Author] - Research direction, COLREGs domain expertise

**Contributors**:
- See [CONTRIBUTORS.md](CONTRIBUTORS.md) for community contributions

**Acknowledgments**:
- Pygame community for simulation framework
- LangChain for LLM abstraction layer
- Maritime domain experts who validated scenario realism

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

Copyright © 2026 [Your Institution/Name]
All rights reserved.
