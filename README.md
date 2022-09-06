# Appendix of paper: Towards Energy Consumption Measurement of Automated Program Repair

## Data available in this appendix.

All the results of this experiments are obtained from the data disposed in folder [results/](results/)
The files from [results/energy_summary/](results/energy_summary/) contain the summary of the experiment for each Tool and Bug ID.
For example, the file [results/energy_summary/energy_summary_Avatar-Chart-1.json](results/energy_summary/energy_summary_Avatar-Chart-1.json) contains the energy consumption accross all the repair attemps of running the tool `Avatar` on  Defects4J bug with id `Chart 1`. 
That file also has the correctness assessment done on each patch.
The scripts for computing the Tables shown in that paper  are in the python file at [script/PaperResults.py](script/PaperResults.py) and read the summary files at [results/energy_summary/](results/energy_summary/).  

These sumary files are computed from the raws data available at [results/row_data/](results/row_data/)
In particular there are 3 subfolders:
- logs: contains the log of the repair attemps (e.g., a tool executed on a particular file). Example, file [results/row_data/log/log_Avatar_Chart_1/log_out_Chart_1_Avatar.txt](results/row_data/log/log_Avatar_Chart_1/log_out_Chart_1_Avatar.txt) contains the log of the *instrumented* version of Avatar tool for `Chart 1`. The log contains all the events (type of event + timestamp) that we register.

For example: the piece of log shown below display the event *[PF]*  patch found together with its timestamp *1659925031785*.
```
GPR[EPVATR]-1659925031773
19:17:11.773 [main] INFO edu.lu.uni.serval.avatar.AbstractFixer - Succeeded to fix the bug Chart_1====================
GPR[PF]-1659925031785

```

- metrics: contains the measure of the energy consumption of a repair attempt. Example, [results/row_data/metrics/metric_Avatar_Chart_1/cache_wattmetre_power_watt_job_metrics_Avatar-Chart-1.csv](results/row_data/metrics/metric_Avatar_Chart_1/cache_wattmetre_power_watt_job_metrics_Avatar-Chart-1.csv) contains the power consumption of Avatar tool during the repair attempt for bug Chart 1. 

Those files have two columns: timestamps and power. For example:
```
1662055748.421738,85.9
1662055748.441768,92.4
1662055748.461803,94.4
1662055748.481742,99.1
1662055748.501784,97.1
```
- patches: the patches found (if any). Example [results/row_data/patches/Avatar_Chart_1](results/row_data/patches/Avatar_Chart_1) contains the patches form Avatar that repair  bug Chart 1. All the patches have a timestamp in their names, so it's possible to sort the patches by generation time: it's the number that follows "\_ts\_",  for example:
```
Patch_6552628_1566_ts_1657139336721.txt
Patch_6565929_1567_ts_1657139350022.txt
Patch_6618328_1573_ts_1657139402421.txt
Patch_6644049_1575_ts_1657139428142.txt
Patch_6669955_1577_ts_1657139454048.txt
Patch_6695716_1579_ts_1657139479809.txt
Patch_6708462_1580_ts_1657139492555.txt
Patch_6749287_1586_ts_1657139533380.txt
```



Due to the large scale of our experiment (many patches, large  ametric files), the size of all the row files is more than 100 Gb. Given the limit of the repository size from anonymous.4open.science, we pushed the files related to one repair attempts per tool-bug id (we recall that we execute at least  5 repair attempts per tool-bugid).
We will progressively update them, pushing all data to Zenodo.


### Documentations


#### Patch assessment:
The labels of the patches are put in the summary files, in particular, under the array element called `Correctness_Per_Patch`: the i-th element of that array indicates the correctness of the i-th patch (chronologically sorted). A 'C' means *Correct*, other annotations such as 'I' or 'na' mean *incorrect*.
For example,  the summary of Avatar repairing Chart-1  [results/energy_summary/energy_summary_Avatar-Chart-1.json](results/energy_summary/energy_summary_Avatar-Chart-1.json)
indicates that the first patch [results/energy_summary/energy_summary_Avatar-Chart-1.json#L70](results/energy_summary/energy_summary_Avatar-Chart-1.json#L70) is correct. We recall that the patches from  [results/row_data/patches/Avatar_Chart_1](results/row_data/patches/Avatar_Chart_1) have the the time of generation in their file names.
We also recall that we do not analyze patch correctness beyond the first correct patch found (as in the paper we are only interested in the energy consumed to find the first correct patch).


#### Events
The explanation about events is in file  [doc/events.md](doc/events.md)



