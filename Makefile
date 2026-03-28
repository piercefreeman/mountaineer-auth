.PHONY: lint ci-lint lint-ruff lint-ty test help

# Default target
all: lint

# Package directory
PKG_DIR := ./mountaineer_auth/

# Define a function to run ruff on a specific directory
# Usage: $(call run_ruff,<directory>)
define run_ruff
	@echo "\n=== Running ruff on $(1) ==="; \
	echo "Running ruff format in $(1)"; \
	(cd $(1) && uv run ruff format .) || { echo "FAILED: ruff format in $(1)"; exit 1; }; \
	echo "Running ruff check --fix in $(1)"; \
	(cd $(1) && uv run ruff check --fix .) || { echo "FAILED: ruff check in $(1)"; exit 1; }; \
	echo "=== ruff completed successfully for $(1) ===";
endef

# Define a function to run ruff in CI mode (check only, no fixes)
# Usage: $(call run_ruff_ci,<directory>)
define run_ruff_ci
	@echo "\n=== Running ruff (validation only) on $(1) ==="; \
	echo "Running ruff format --check in $(1)"; \
	(cd $(1) && uv run ruff format --check .) || { echo "FAILED: ruff format in $(1)"; exit 1; }; \
	echo "Running ruff check (no fix) in $(1)"; \
	(cd $(1) && uv run ruff check .) || { echo "FAILED: ruff check in $(1)"; exit 1; }; \
	echo "=== ruff validation completed successfully for $(1) ===";
endef

# Define a function to run ty on a specific directory
# Usage: $(call run_ty,<directory>)
define run_ty
	@echo "\n=== Running ty on $(1) ==="; \
	(uv run ty check --project . $(1)) || { echo "FAILED: ty in $(1)"; exit 1; }; \
	echo "=== ty completed successfully for $(1) ===";
endef

# Main lint target (with fixes)
lint:
	@echo "=== Linting mountaineer-auth ==="
	$(call run_ruff,$(PKG_DIR))
	$(call run_ty,$(PKG_DIR))
	@echo "\n=== All linters completed successfully ==="

# CI lint target (validation only, no fixes)
ci-lint:
	@echo "=== CI Linting mountaineer-auth (validation only) ==="
	$(call run_ruff_ci,$(PKG_DIR))
	$(call run_ty,$(PKG_DIR))
	@echo "\n=== All linters completed successfully ==="

# Tool-specific targets
lint-ruff:
	@echo "=== Running ruff ==="
	$(call run_ruff,$(PKG_DIR))

lint-ty:
	@echo "=== Running ty ==="
	$(call run_ty,$(PKG_DIR))

# Test target
test:
	@echo "=== Running tests ==="
	(uv run pytest -vvv $(PKG_DIR)) || { echo "FAILED: tests"; exit 1; }
	@echo "=== Tests completed successfully ==="

# Show help
help:
	@echo "Available targets:"
	@echo " "
	@echo "  lint            - Run all linters (with fixes)"
	@echo "  ci-lint         - Run all linters (validation only, no fixes)"
	@echo "  lint-ruff       - Run ruff only (with fixes)"
	@echo "  lint-ty         - Run ty type checker only"
	@echo " "
	@echo "  test            - Run tests"
