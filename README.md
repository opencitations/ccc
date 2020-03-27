# Deploy CCC

Preliminaries

 * install dependencies: fuzzywuzzy `pip install fuzzywuzzy`
 * config files:
   * change `script/bee/conf.py` (*do not change* the additional config file in `script/ccc/conf_bee.py`)
   * change `script/ccc/conf_spacin.py` (*do not change* `script/spacin/conf.py` which is ignored by `script/ccc/run_spacin.py`)
 * create a blazegraph with the same .properties file of occ
 * check for the gently_run/stop bash scripts

The following run files that are copies of `script/bee/run.py` and `script/spacin/run.py` with changes in the imported modules

 * run bee from the folder `scripts`: `python -m script.ccc.run_bee`. It creates a folder called `test` (in the same folder `scripts`).
 * run spacin from the folder `scripts`: `python -m script.ccc.run_spacin` which takes files from the above folder `test`.
