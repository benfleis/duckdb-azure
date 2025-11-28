TMPLS:= writes.slt.tmpl writes_more.slt_slow.tmpl

PROTOS:= az abfss

AZ_TESTS:= $(TMPLS:.slt.tmpl=_az.test)
AZ_TESTS:= $(AZ_TESTS:.slt_slow.tmpl=_az.test_slow)
ABFSS_TESTS:= $(TMPLS:.slt.tmpl=_abfss.test)
ABFSS_TESTS:= $(ABFSS_TESTS:.slt_slow.tmpl=_abfss.test_slow)

gen:	$(AZ_TESTS) $(ABFSS_TESTS)

clean:
	rm -f $(AZ_TESTS) $(ABFSS_TESTS)


%_az.test: %.slt.tmpl
	mustache --allow-missing-variables=false ../../../configs/cloud_az.yml $< > $@

%_az.test_slow: %.slt_slow.tmpl
	mustache --allow-missing-variables=false ../../../configs/cloud_az.yml $< > $@

%_abfss.test: %.slt.tmpl
	mustache --allow-missing-variables=false ../../../configs/cloud_abfss.yml $< > $@

%_abfss.test_slow: %.slt_slow.tmpl
	mustache --allow-missing-variables=false ../../../configs/cloud_abfss.yml $< > $@

.PHONY: gen clean
