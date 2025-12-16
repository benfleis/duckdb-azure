##
# NOTE: this is a quick hand rolled template instantiator, to test mustache templates across
# both azure protocols
# The ultimate intent is to (by default) instantiate templates at run time, but this provides
# great insight into what they look like.
#
# If you want to edit/update the sources, all you need to do is:
# - go install github.com/cbroglie/mustache/cmd/mustache@latest
# - make clean gen
#
PROJ_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
#TMPLS:= sql/cloud/vfs/ops.slt.tmpl sql/cloud/write/writes.slt.tmpl sql/cloud/write/writes_more.slt_slow.tmpl
TMPLS:= $(shell find . -type f -a \( -name '*.slt.tmpl' -o -name '*.slt_slow.tmpl' \) )

CLOUD_AZ_CONF:= configs/cloud_az.yml
CLOUD_AZ_TESTS:= $(TMPLS:.slt.tmpl=__cloud_az.test)
CLOUD_AZ_TESTS:= $(CLOUD_AZ_TESTS:.slt_slow.tmpl=__cloud_az.test_slow)

CLOUD_ABFSS_CONF:= configs/cloud_abfss.yml
CLOUD_ABFSS_TESTS:= $(TMPLS:.slt.tmpl=__cloud_abfss.test)
CLOUD_ABFSS_TESTS:= $(CLOUD_ABFSS_TESTS:.slt_slow.tmpl=__cloud_abfss.test_slow)

LOCAL_AZ_CONF:= configs/local_az.yml
LOCAL_AZ_TESTS:= $(TMPLS:.slt.tmpl=__local_az.test)
LOCAL_AZ_TESTS:= $(LOCAL_AZ_TESTS:.slt_slow.tmpl=__local_az.test_slow)

gen:	$(CLOUD_AZ_TESTS) $(CLOUD_ABFSS_TESTS) $(LOCAL_AZ_TESTS)

clean:
	rm -f $(CLOUD_AZ_TESTS) $(CLOUD_ABFSS_TESTS) $(LOCAL_AZ_TESTS)

%__cloud_az.test: %.slt.tmpl $(CLOUD_AZ_CONF)
	mustache --allow-missing-variables=false "$(CLOUD_AZ_CONF)" $< > $@

%__cloud_az.test_slow: %.slt_slow.tmpl $(CLOUD_AZ_CONF)
	mustache --allow-missing-variables=false "$(CLOUD_AZ_CONF)" $< > $@

%__cloud_abfss.test: %.slt.tmpl $(CLOUD_ABFSS_CONF)
	mustache --allow-missing-variables=false "$(CLOUD_ABFSS_CONF)" $< > $@

%__cloud_abfss.test_slow: %.slt_slow.tmpl $(CLOUD_ABFSS_CONF)
	mustache --allow-missing-variables=false "$(CLOUD_ABFSS_CONF)" $< > $@

%__local_az.test: %.slt.tmpl $(LOCAL_AZ_CONF)
	mustache --allow-missing-variables=false "$(LOCAL_AZ_CONF)" $< > $@

%__local_az.test_slow: %.slt_slow.tmpl $(LOCAL_AZ_CONF)
	mustache --allow-missing-variables=false "$(LOCAL_AZ_CONF)" $< > $@

.PHONY: gen clean
