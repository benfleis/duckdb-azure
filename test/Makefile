##
# NOTE: this is a quick hand rolled template instantiator, to test mustache templates across
# both azure protocols
# The ultimate intent is to (by default) instantiate templates at run time, but this provides
# great insight into what they look like.
#
PROJ_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
TMPLS:= sql/cloud/vfs/ops.slt.tmpl sql/cloud/write/writes.slt.tmpl sql/cloud/write/writes_more.slt_slow.tmpl

PROTOS:= az abfss

AZ_CONF:= configs/cloud_az.yml
AZ_TESTS:= $(TMPLS:.slt.tmpl=_az.test)
AZ_TESTS:= $(AZ_TESTS:.slt_slow.tmpl=_az.test_slow)

ABFSS_CONF:= configs/cloud_abfss.yml
ABFSS_TESTS:= $(TMPLS:.slt.tmpl=_abfss.test)
ABFSS_TESTS:= $(ABFSS_TESTS:.slt_slow.tmpl=_abfss.test_slow)

gen:	$(AZ_TESTS) $(ABFSS_TESTS)

clean:
	rm -f $(AZ_TESTS) $(ABFSS_TESTS)

%_az.test: %.slt.tmpl $(AZ_CONF)
	mustache --allow-missing-variables=false "$(AZ_CONF)" $< > $@

%_az.test_slow: %.slt_slow.tmpl $(AZ_CONF)
	mustache --allow-missing-variables=false "$(AZ_CONF)" $< > $@

%_abfss.test: %.slt.tmpl $(ABFSS_CONF)
	mustache --allow-missing-variables=false "$(ABFSS_CONF)" $< > $@

%_abfss.test_slow: %.slt_slow.tmpl $(ABFSS_CONF)
	mustache --allow-missing-variables=false "$(ABFSS_CONF)" $< > $@

.PHONY: gen clean
