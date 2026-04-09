# Contributing to ASvLLM

Thank you for your interest in contributing! We welcome bug reports, feature requests, and pull requests from the community.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- Familiarity with Pygame, LLMs, and maritime autonomy (optional but helpful)

### Setup Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ASvLLM.git
cd ASvLLM

# Create development branch
git checkout -b feature/your-feature-name

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies (including dev tools)
pip install -r requirements.txt
pip install black pylint pytest  # Development tools
```

---

## How to Contribute

### 1. Report Bugs

Found a bug? Please open an [Issue](https://github.com/yourusername/ASvLLM/issues) with:

- **Clear title**: "Bug: [Description]"
- **Detailed description**: What went wrong?
- **Steps to reproduce**: How can we replicate it?
- **Expected vs. actual behavior**: What should happen?
- **Environment**: Python version, OS, LLM provider
- **Logs/Screenshots**: Any error messages?

**Example**:
```
Title: Pygame window crashes on headless systems

Description: When running on WSL without X11, the simulator crashes with SDL video error

Steps:
1. Run `python main.py` on headless Linux
2. See error: "No available video device"

Expected: Interactive mode should skip/fallback gracefully
Actual: Crashes immediately

Environment: Python 3.10, WSL2, OpenAI API
```

### 2. Request Features

Have an idea? Open a [Feature Request](https://github.com/yourusername/ASvLLM/issues) with:

- **Clear title**: "Feature: [Description]"
- **Motivation**: Why is this needed?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches?
- **Additional context**: Examples, references?

**Example**:
```
Title: Feature: Support for multiple concurrent LLM queries

Motivation: Current implementation queries one vessel at a time. 
In complex multi-vessel scenarios, parallel queries could speed up decision-making.

Proposed Solution:
- Use asyncio.gather() to query all conflicted vessels simultaneously
- Implement rate limiting to avoid API throttling
- Log aggregate decision times

Alternatives:
- Queue-based batching (simpler but less responsive)

Example Use Case:
Multi-vessel Scenario 3 could reduce per-step latency from 5s to 2s
```

### 3. Submit Code Changes

Ready to contribute code? Follow this workflow:

#### Step 1: Fork & Branch

```bash
# Fork on GitHub (web interface)
git clone https://github.com/YOUR_USERNAME/ASvLLM.git
cd ASvLLM
git checkout -b fix/issue-number
```

#### Step 2: Make Changes

Follow our **Code Standards**:

- **PEP 8 style**: Use [Black](https://github.com/psf/black) for formatting
- **Add docstrings**: All functions should have clear documentation
- **Type hints**: Use Python type hints where practical
- **Comments**: Explain "why", not "what" (code shows what)
- **Tests**: Add tests for new functionality

**Example**:
```python
def calculate_collision_risk(vessel_a, vessel_b, time_horizon_sec=60.0) -> float:
    """
    Calculate collision risk between two vessels using DCPA/TCPA prediction.
    
    Args:
        vessel_a (Vessel): First vessel object
        vessel_b (Vessel): Second vessel object
        time_horizon_sec (float): Time duration for collision prediction (default 60s)
    
    Returns:
        float: Collision risk probability [0.0, 1.0]
              0.0 = no risk, 1.0 = certain collision
    
    Raises:
        ValueError: If time_horizon_sec < 0
    
    Example:
        >>> risk = calculate_collision_risk(v1, v2, time_horizon_sec=30.0)
        >>> if risk > 0.5:
        >>>     v1.set_maneuver(Maneuver.ALTER_COURSE_STARBOARD)
    """
    if time_horizon_sec < 0:
        raise ValueError("time_horizon_sec must be non-negative")
    
    # Calculate relative velocity
    rel_vx = vessel_b.vx - vessel_a.vx
    rel_vy = vessel_b.vy - vessel_a.vy
    
    # ... implementation ...
    
    return risk_score
```

#### Step 3: Format Code

```bash
# Auto-format with Black
black *.py prompts_generator/

# Check linting
pylint entity.py batch_runner.py  # Check for issues

# Verify no obvious errors
python validate_logs.py
```

#### Step 4: Commit with Clear Messages

```bash
# Commit with descriptive message
git add .
git commit -m "Fix: Correct DCPA calculation for overtaking scenarios

- Fixed incorrect relative velocity computation
- Added unit test for edge cases
- Validated against 100 historical scenarios
- Addresses issue #42"
```

**Commit message format**:
- **First line**: `[Type]: Brief description` (50 chars max)
- **Blank line**
- **Body**: Detailed explanation, bullet points, references

**Types**: `fix`, `feat`, `refactor`, `docs`, `test`, `perf`, `chore`

#### Step 5: Push & Create Pull Request

```bash
git push origin fix/issue-number
```

Then open a **Pull Request** on GitHub with:

- **Title**: Same as commit (e.g., "Fix: Correct DCPA calculation")
- **Description**: 
  - What does this fix/add?
  - Why is it needed?
  - How was it tested?
  - Any breaking changes?
  - Closes issue #XX

**Example PR Description**:
```markdown
## Description
Fixes incorrect DCPA calculation for overtaking scenarios where vessels move parallel.

## Related Issue
Closes #42

## Changes
- Fixed relative velocity computation in `entity.py:calculate_collision_risk()`
- Added edge case handling for parallel vessel trajectories
- Added 10 unit tests covering overtaking scenarios

## Testing
- All existing tests pass
- New tests validate against historical scenarios
- Validated with batch_runner.py: 50 scenarios, 0 failures

## Breaking Changes
None

## Checklist
- [x] Code follows style guidelines (Black formatted)
- [x] Added/updated docstrings
- [x] Added tests for new functionality
- [x] Validated with validate_logs.py
- [x] Updated CHANGELOG.md
```

#### Step 6: Code Review

- Maintainers will review your PR
- Address feedback and push updates
- Once approved, we'll merge!

---

## Code Standards

### Style Guide

Follow **PEP 8** (enforced via Black):

```bash
# Format all Python files
black *.py prompts_generator/
```

### Documentation

All new functions/classes **must** have docstrings:

```python
def run_simulation(config: Dict[str, Any], verbose: bool = False) -> Dict:
    """
    Execute a single simulation run with specified configuration.
    
    This is the main entry point for executing maritime collision avoidance
    simulations. It initializes the game manager, loads scenarios, and logs
    all LLM decisions for offline analysis.
    
    Parameters
    ----------
    config : dict
        Simulation configuration with keys:
        - mode: 'standard', 'prompt_history', or 'natural'
        - provider: 'openai', 'claude', or 'deepseek'
        - scenario: Scenario name (e.g., 'Head-On Scenario')
        - prompt: 'minimal', 'moderate', 'detailed', 'natural', 'tss'
    
    verbose : bool, optional
        If True, print detailed logs (default: False)
    
    Returns
    -------
    dict
        Simulation outcomes with keys:
        - success: bool, whether all vessels reached goals
        - collisions: int, number of collisions detected
        - min_distance_km: float, minimum separation distance
        - llm_calls: int, number of LLM queries made
        - runtime_sec: float, wall-clock execution time
    
    Raises
    ------
    ValueError
        If config is missing required keys or has invalid values
    
    RuntimeError
        If LLM API fails and no fallback available
    
    See Also
    --------
    batch_runner.py : Automated multi-run experiments
    
    Examples
    --------
    >>> config = {
    ...     'mode': 'standard',
    ...     'provider': 'openai',
    ...     'scenario': 'Head-On Scenario',
    ...     'prompt': 'detailed'
    ... }
    >>> result = run_simulation(config, verbose=True)
    >>> print(f"Collision rate: {result['collisions']}")
    """
    pass
```

### Testing

For new features, write simple tests:

```bash
# Test framework is pytest (optional)
pip install pytest

# Create tests/test_collision_detection.py
def test_dcpa_head_on():
    """Verify DCPA calculation for head-on encounter."""
    v1 = Vessel(0, 500, pixels_per_km=1000)
    v2 = Vessel(1000, 500, pixels_per_km=1000)
    v1.heading = math.pi/2  # East
    v2.heading = 3*math.pi/2  # West
    
    risk = calculate_collision_risk(v1, v2)
    assert 0.8 < risk <= 1.0, f"Expected high risk, got {risk}"

# Run tests
pytest tests/test_collision_detection.py
```

---

## Development Workflow

### Quick Test Before Submitting

```bash
# 1. Format code
black *.py prompts_generator/

# 2. Validate data integrity (if dealing with logs)
python validate_logs.py

# 3. Quick simulation test
python -c "
from game_manager import GameManager
import pygame
pygame.init()
game = GameManager(1000, 1000)
game.load_simulation_scripted('standard', 'openai', 'minimal', 'Head-On Scenario')
print('✓ Code loads successfully')
"

# 4. Lint check (optional but recommended)
pylint entity.py --max-line-length=100
```

### Update Changelog

When submitting a PR, update `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- Support for parallel LLM queries in multi-vessel scenarios
- New metric: decision latency percentiles (p50, p95, p99)

### Fixed
- Bug in DCPA calculation for parallel trajectories (#42)
- LLM response timeout now correctly falls back to previous decision

### Changed
- Refactored EntityManager for better code reuse
- Updated prompt templates to improve GPT-3.5 performance
```

---

## Continuous Integration (CI)

Your PR will automatically run:

1. **Style check** (Black formatting)
2. **Linting** (pylint)
3. **Tests** (pytest, if applicable)
4. **Data validation** (validate_logs.py on sample data)

All checks must pass before merging. If a check fails:

1. See the error log
2. Fix your code
3. Push the update
4. CI reruns automatically

---

## Support

- **Questions?** Open a [Discussion](https://github.com/yourusername/ASvLLM/discussions)
- **Found a bug?** Open an [Issue](https://github.com/yourusername/ASvLLM/issues)
- **Want to chat?** Reach out: your.email@institution.edu

---

## Recognition

Contributors will be recognized in:

- `CONTRIBUTORS.md` (list of all contributors)
- GitHub contributor graph
- Project citations (for co-authored work)

Thank you for making ASvLLM better! 🚀
