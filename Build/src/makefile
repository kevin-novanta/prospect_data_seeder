# Wrapper Makefile at Build/src
# Forwards all targets to the real Makefile in tools/taxonomy_builder

SUBMK := tools/taxonomy_builder/Makefile

.PHONY: % default
%:
	@$(MAKE) -f $(SUBMK) $@

default: help