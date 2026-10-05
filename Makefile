# top-level: `make test` builds the c program and runs every testbench
# cocotb doesn't always fail make on a failing test, so this greps each results.xml for <failure

TB_DIRS = $(patsubst %/Makefile,%,$(wildcard tb/*/Makefile)) # picks up any tb/<dir> with a Makefile

test: sw
	@fail=0; for d in $(TB_DIRS); do \
	    echo "=== $$d ==="; \
	    $(MAKE) -s -C $$d > $$d/sim.log 2>&1 || fail=1; \
	    grep -E "TESTS=" $$d/sim.log | sed 's/^ *//'; \
	    if [ ! -f $$d/results.xml ] || grep -q "<failure" $$d/results.xml; then fail=1; echo "  FAILED, see $$d/sim.log"; fi; \
	done; \
	if [ $$fail -eq 0 ]; then echo "ALL PASS"; else echo "SOME TESTS FAILED"; exit 1; fi

sw:
	$(MAKE) -C sw

clean:
	$(MAKE) -C sw clean
	for d in $(TB_DIRS); do $(MAKE) -C $$d clean >/dev/null 2>&1; rm -f $$d/results.xml $$d/sim.log; done

.PHONY: test sw clean
