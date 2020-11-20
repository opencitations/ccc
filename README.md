# Deploy CCC

Dependencies

 * install dependencies with `pip install -r requirements.txt`
 * In `ccc/scripts`, put Blazegraph.jar [Direct link to download](https://github.com/blazegraph/database/releases/download/BLAZEGRAPH_2_1_6_RC/blazegraph.jar)

### RUN BEE LOCALLY

 * Change `bee/conf.py` content with content of `bee/conf_local.py`
 * Change `ccc/conf_spacin.py` content with content of `ccc/conf_spacin_local.py`
 * Shell (from `ccc/scripts`): `python3 -m script.ccc.run_bee`. It creates a folder called `test` in the same folder `scripts`.
 * OUTPUT JSON: `scripts/test/share/ref/todo`
 * ERRORS: `scripts/test/index/ref/issue`

#### Rerun BEE

 * Empty/remove the folder `test/`
 * Run: `python3 -m script.ccc.run_bee`

#### Run BEE on a single XML file
 * Include the XML file in the folder `script/ccc/`
 * Uncomment lines 39, 40 of `script/ccc/jats2oc.py`
 * Change in `script/ccc/test_bee.py` the name of the file to be parsed
 * Run: `python3 -m script.ccc.test_bee`

## RUN SPACIN LOCALLY

 * INPUT JSON: `scripts/test/share/ref/todo`
 * OUTPUT RDF (dump): `scripts/ccc/`
 * Run Blazegraph: `java -Dfile.encoding=UTF-8 -Dsun.jnu.encoding=UTF-8 -server -Xmx1g -Djetty.port=9999 -Dbigdata.propertyFile=ccc.properties -jar blazegraph.jar`
 * Run: `python3 -m script.ccc.run_spacin`

#### Rerun SPACIN

 * Empty `scripts/ccc/` BUT do not remove `scripts/ccc/context.json`
 * Remove `scripts/ccc.jnl` (quit the .jar first!)
 * If you want to rerun SPACIN on the same JSON files, move the content of `scripts/test/share/ref/done` into `scripts/test/share/ref/todo`


Other notes:

 * *do not change* the config file `script/ccc/conf_bee.py`
 * *do not delete* `context.json` included in `scripts/ccc/` when rerunning SPACIN
