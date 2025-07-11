# Makefile for NLP Practice 2

# --- Variables ---
# Use the SHELL variable to detect the current shell
SHELL_TYPE := $(shell echo $(SHELL) | awk -F/ '{print $$NF}')
VENV_DIR = .venv
PYTHON = ./.venv/bin/python
PIP = ./.venv/bin/pip
JUPYTER = $(VENV_DIR)/bin/jupyter
NOTEBOOK_FILE = "Práctica 2 - Recuperación de Información.ipynb"
QRELS_FILE = "cranfield-trec-dataset/cranqrel.trec.txt"
RESULTS_TITLE_FILE = "trec_results_title.txt"
RESULTS_TT_FILE = "trec_results_title_text.txt"


# --- Targets ---

.PHONY: all install setup-venv find-imports clean help run evaluate

all: help

# Setup the virtual environment and install dependencies
install: setup-venv
	@echo "Installing dependencies from requirements.txt..."
	@$(PIP) install -r requirements.txt
	@echo "\n✅ Dependencies installed successfully!"
	@echo "To activate the virtual environment, run:"
	@$(call activate_message)

# Create the virtual environment if it doesn't exist
setup-venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment in $(VENV_DIR)..."; \
		python3 -m venv $(VENV_DIR); \
		echo "Virtual environment created."; \
	else \
		echo "Virtual environment already exists."; \
	fi

# Run the Jupyter Notebook
run: install
	@echo "Executing Jupyter Notebook: $(NOTEBOOK_FILE)..."
	@$(JUPYTER) nbconvert --to notebook --execute --inplace --allow-errors $(NOTEBOOK_FILE)
	@echo "✅ Notebook executed successfully."

# Evaluate the results using trec_eval
evaluate: run
	@echo "\n\033[34m--- Evaluating Title-Only Model (with Query Expansion) ---\033[0m"
	@trec_eval $(QRELS_FILE) $(RESULTS_TITLE_FILE) | grep -E "^map |^P_10 "
	@echo "\n\033[34m--- Evaluating Title+Text Model (with Query Expansion) ---\033[0m"
	@trec_eval $(QRELS_FILE) $(RESULTS_TT_FILE) | grep -E "^map |^P_10 "


# Find and print all unique imports from the notebook
find-imports:
	@echo "Analyzing imports in $(NOTEBOOK_FILE)..."
	@if [ -f "$(NOTEBOOK_FILE)" ]; then \
		grep -oE '^(import|from) [a-zA-Z0-9_.]+' $(NOTEBOOK_FILE) | sed -E 's/^(import|from) //g' | sed -E 's/\..*//g' | sort -u; \
	else \
		echo "Notebook file not found: $(NOTEBOOK_FILE)"; \
	fi

# Clean the project by removing the virtual environment
clean:
	@echo "Removing virtual environment..."
	@rm -rf $(VENV_DIR)
	@echo "Cleanup complete."

# Display help message
help:
	@echo "\033[34m========================================\033[0m"
	@echo "\033[34m        Gemini CLI Help Menu        \033[0m"
	@echo "\033[34m========================================\033[0m"
	@echo "Makefile for NLP Practice 2"
	@echo ""
	@echo "\033[33mUsage:\033[0m"
	@echo "  \033[32mmake install\033[0m      - Create virtual environment and install dependencies."
	@echo "  \033[32mmake run\033[0m          - Execute the Jupyter Notebook."
	@echo "  \033[32mmake evaluate\033[0m   - Run the notebook and evaluate the results."
	@echo "  \033[32mmake find-imports\033[0m - Analyze the notebook and list all imported libraries."
	@echo "  \033[32mmake clean\033[0m        - Remove the virtual environment."
	@echo ""

# --- Helper Functions ---

# Define a message for activating the venv based on the shell
define activate_message
	@if [ "$(SHELL_TYPE)" = "bash" ] || [ "$(SHELL_TYPE)" = "zsh" ]; then \
		echo "   source $(VENV_DIR)/bin/activate"; \
	elif [ "$(SHELL_TYPE)" = "fish" ]; then \
		echo "   source $(VENV_DIR)/bin/activate.fish"; \
	else \
		echo "⚠️  Unsupported shell: $(SHELL_TYPE). Please activate the environment manually."; \
		echo "   For bash/zsh: source $(VENV_DIR)/bin/activate"; \
		echo "   For fish:     source $(VENV_DIR)/bin/activate.fish"; \
		echo "   For csh/tcsh: source $(VENV_DIR)/bin/activate.csh"; \
	fi
endef